import glob
import linecache
import numpy as np
import os
import pandas as pd
import re
import requests
import shutil
import subprocess
from bs4 import BeautifulSoup
from ftplib import FTP
from obspy import read, UTCDateTime
from obspy.io.sac import SACTrace

class Earthquake():
    def __init__(self, url):
        self.__url = url
        self.__parameters = self.__obtainEqParameters()
        self.__dir = self.__obtainDir()
        self.__obtainFoldersName()
        
    def __obtainEqParameters(self):
        parameters = {}
        if not os.path.exists("tmp"):
            os.makedirs("tmp")
        req = requests.get(self.__url)
        with open(f'tmp/tmp.txt', 'w') as eqReport:
            eqReport.write(req.content.decode('utf-8'))
        lineNum = 0
        with open(f'tmp/tmp.txt', 'r') as eqReport:
            for line in eqReport:
                lineNum += 1
                if re.search('eqReportBoxBg', line):
                    break
                    
        self.__eqNo = int(linecache.getline(f'tmp/tmp.txt', lineNum+3).split()[-1])
        parameters['EarthquakeNo'] = self.__eqNo
        
        year = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[60:64])        
        month = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[54:56])
        date = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[57:59])
        hour = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[65:67])
        minute = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[68:70])
        second = float(linecache.getline(f'tmp/tmp.txt', lineNum+5)[71:75])
        originTimeStringUTC = f"{year}-{month:02}-{date:02}T{hour:02}:{minute:02}:{second}+08"
        self.__originTimeUTC = UTCDateTime(originTimeStringUTC)        
        parameters['OriginTimeUTC'] = self.__originTimeUTC
        
        self.__latitude = float(linecache.getline(f'tmp/tmp.txt', lineNum+7)[17:22])
        self.__latitudeUnit = 'Degree(N)'
        self.__longitude = float(linecache.getline(f'tmp/tmp.txt', lineNum+7)[24:30])
        self.__longitudeUnit = 'Degree(E)'
        self.__depth = float(linecache.getline(f'tmp/tmp.txt', lineNum+9)[15:20])
        self.__depthUnit = 'km'
        parameters['Hypocenter'] = [self.__latitude, self.__latitudeUnit, self.__longitude, self.__longitudeUnit, self.__depth, self.__depthUnit]
        
        self.__magnitude = float(linecache.getline(f'tmp/tmp.txt', lineNum+11)[22:25])
        parameters['Magnitude(ML)'] = self.__magnitude
        
        shutil.rmtree("tmp")
        return parameters
    
    def __obtainDir(self):
        dir = f'/home/palert/data/SAC/{self.__originTimeUTC.year}{self.__originTimeUTC.month:02d}'
        if not os.path.exists(dir):
            os.makedirs(dir)
        return dir
    
    def __obtainFoldersName(self):
        datetime2minAgo = self.__originTimeUTC - 120
        self.folder2minAgo = datetime2minAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'
        datetime20secAgo = self.__originTimeUTC - 20
        self.folder20secAgo = datetime20secAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'

    def downloadData(self):
        ftpNTU = FTP()
        ftpNTU.connect('140.112.65.220', 2121)  # IP, port
        ftpNTU.login()  # user, password
        ftpNTU.cwd(f'events/{self.__originTimeUTC.year}{self.__originTimeUTC.month:02d}')
        bz2FileName = f'{self.folder2minAgo}.tar.bz2'
        print('Preparing data. Please be patient...')
        localfile = open(f'{self.__dir}/' + bz2FileName, 'wb')
        ftpNTU.retrbinary('RETR ' + bz2FileName, localfile.write)
        localfile.close()
        ftpNTU.quit()
        os.system(f'tar -C {self.__dir} -jxvf {self.__dir}/{bz2FileName}')
        os.remove(f'{self.__dir}/{bz2FileName}')
        if not os.path.exists(f'{self.__dir}/{self.folder20secAgo}'):
            os.makedirs(f'{self.__dir}/{self.folder20secAgo}')
        os.system(f'cp {self.__dir}/{self.folder2minAgo}/* {self.__dir}/{self.folder20secAgo}')            
    
    def processData(self, dir2Process, diffStartime, diffEndtime):
        print(f'Process data in {dir2Process}...')
        os.chdir(dir2Process)
        
        os.system('rm -f A* B* CHGB* HGSD* FUSB* KMNB* LATB* LYUB* MASB* MATB* NACB* NNSB* PHUB* RLNB* SBCB* SSLB* SXI1* TATO* TDCB* TPUB* TWGB* TWKB* VWDT* VWUC* WARB* WFSB* WUSB* YD07* YHNB* YULB* YOJ*')
        
        st = read('*TW*')
        self.sync(st)
        self.cutWaveform(st, self.__originTimeUTC + diffStartime, self.__originTimeUTC + diffEndtime)
        
        for file in list(glob.glob('*TW*')):
            sac = SACTrace.read(file)
            sac.o = self.__originTimeUTC
            sac.iztype = 'io'
            sac.evla = self.__latitude
            sac.evlo = self.__longitude
            sac.evdp = self.__depth
            sac.mag = self.__magnitude
            sac.write(file)
        os.chdir('../../../')
    
    @staticmethod
    def sync(st):
        maxstart = np.max([tr.stats.starttime for tr in st])
        minend =  np.min([tr.stats.endtime for tr in st])
        st.trim(maxstart, minend)
    
    @staticmethod    
    def cutWaveform(st, starttime, endtime):        
        for tr in st:
            filename = f'{tr.stats.station}.{tr.stats.channel}.{tr.stats.network}.{tr.stats.location}'
            tr.trim(starttime, endtime)
            tr.write(filename, format="SAC")

    def tmp(self):
        self.dfStations = pd.read_csv('stalist.txt', sep=" ",header=None)
        self.dfStations.columns =['staName', 'staLatitude', 'staLongitude']
        self.dfStations.set_index('staName', inplace=True)
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')        
        self.__getPGAs()
        # self.__saveStaInfo2Sac()
        os.chdir('../../../')
        
    def __getPGAs(self):
        print(f'Get pgas...')
        fileTime = self.__originTimeUTC.strftime('%Y%m%d%H%M%S')
        fileName = f'{self.__dir}/{self.folder20secAgo}/{fileTime}PGAs.txt'
        f = open(fileName, "w")
        
        originTimehhmmss = self.__originTimeUTC.strftime('%H%M%S')
        f.write(f'{self.__originTimeUTC.year} {self.__originTimeUTC.month:02} {self.__originTimeUTC.day:02} {originTimehhmmss} {self.__latitude} {self.__longitude} {self.__depth} {self.__magnitude}\n')
        
        for sta in list(self.dfStations.index):
            p = subprocess.Popen(["/home/palert/data/rdsac2", sta], stdout=subprocess.PIPE)
            pgas = p.communicate()[0].decode("utf-8").split()
            if float(pgas[0]) > 0:
                f.write(f"{sta} {self.dfStations.loc[sta, 'staLatitude']:.6f} {self.dfStations.loc[sta, 'staLongitude']:.6f} {float(pgas[0])} {float(pgas[1])} {float(pgas[2])} {float(pgas[3])}\n")
        f.close()

    def __saveStaInfo2Sac(self):
        print(f'Save station informtation to sac files...')
        for sta in list(self.dfStations.index):
            for comp in ['E', 'N', 'Z']:
                file = f'{sta}.HL{comp}.TW.--'
                if os.path.exists(file):
                    sac = SACTrace.read(file)
                    sac.stla = self.dfStations.loc[sta, 'staLatitude']
                    sac.stlo = self.dfStations.loc[sta, 'staLongitude']
                    sac.write(file)
           
    @property
    def parameters(self):
        return self.__parameters
        
    @property
    def dir(self):
        return self.__dir
        

def main():
    print("Please find your target event on this website: https://scweb.cwb.gov.tw/en-us/earthquake/data")
    print("Earthquake Information -> Details -> Earthquake Report")
    # eqUrl = input("Insert url of the earthquake report: ")  ### tmp: remove #
    eqUrl = "https://scweb.cwb.gov.tw/en-us/earthquake/imgs/ee2022010805122045003"  ### tmp: remove this line
    event = Earthquake(eqUrl)
    # event.downloadData()
    # event.processData(f'{event.dir}/{event.folder2minAgo}', -120, 480)
    # event.processData(f'{event.dir}/{event.folder20secAgo}', -20, 100)
    event.tmp()
    
if __name__ == "__main__":
    main()