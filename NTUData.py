import linecache
import glob
import numpy as np
import os
import re
import requests
import shutil
from bs4 import BeautifulSoup
from ftplib import FTP
from obspy import read, UTCDateTime

class Earthquake():
    def __init__(self, url, dir):
        self.__url = url
        self.__dir = dir
        self.__parameters = self.__obtainEqParameters()
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
        parameters['Earthquake No.'] = self.__eqNo
        
        self.__year = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[60:64])        
        self.__month = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[54:56])
        self.__date = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[57:59])
        self.__hour = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[65:67])
        self.__minute = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[68:70])
        self.__second = float(linecache.getline(f'tmp/tmp.txt', lineNum+5)[71:75])
        originTimeString = f"{self.__year}-{self.__month:02}-{self.__date:02}T{self.__hour:02}:{self.__minute:02}:{self.__second}+08"
        self.__originTime = UTCDateTime(originTimeString)        
        parameters['Origin Time'] = self.__originTime
        
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
    
    def __obtainFoldersName(self):
        datetime2minAgo = self.__originTime - 120
        self.folder2minAgo = datetime2minAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'
        datetime20secAgo = self.__originTime - 20
        self.folder20secAgo = datetime20secAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'

    def downloadData(self):
        ftpNTU = FTP()
        ftpNTU.connect('140.112.65.220', 2121)  # IP, port
        ftpNTU.login()  # user, password
        ftpNTU.cwd(f'events/{self.__year}{self.__month:02d}')
        bz2FileName = f'{self.__folder2minAgo}.tar.bz2'
        print('Preparing data. Please be patient...')
        localfile = open(f'{self.__dir}/' + bz2FileName, 'wb')
        ftpNTU.retrbinary('RETR ' + bz2FileName, localfile.write)
        localfile.close()
        ftpNTU.quit()
        os.system(f'tar -C {self.__dir} -jxvf {self.__dir}/{bz2FileName}')
        if not os.path.exists(f'{self.__dir}/{self.__folder20secAgo}'):
            os.makedirs(f'{self.__dir}/{self.__folder20secAgo}')
        os.system(f'cp {self.__dir}/{self.__folder2minAgo}/* {self.__dir}/{self.__folder20secAgo}')            
    
    def processData(self, dir2Process, diffStartime, diffEndtime):
        print(f'Process data in {dir2Process}')
        os.chdir(dir2Process)
        
        os.system('rm -f A* B* CHGB* HGSD* FUSB* KMNB* LATB* LYUB* MASB* MATB* NACB* NNSB* PHUB* RLNB* SBCB* SSLB* SXI1* TATO* TDCB* TPUB* TWGB* TWKB* VWDT* VWUC* WARB* WFSB* WUSB* YD07* YHNB* YULB* YOJ*')
        
        st = read('*TW*')
        self.sync(st)
        self.cutWaveform(st, self.__originTime + diffStartime, self.__originTime + diffEndtime)
        print(st)
        os.chdir('../../')
    
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

 
    @property
    def parameters(self):
        return self.__parameters
        

def main():
    print("Please find your target event on this website: https://scweb.cwb.gov.tw/en-us/earthquake/data")
    print("Earthquake Information -> Details -> Earthquake Report")
    # eqUrl = input("Insert url of the earthquake report: ")  ### tmp: remove #
    eqUrl = "https://scweb.cwb.gov.tw/en-us/earthquake/imgs/ee2022010805122045003"  ### tmp: remove this line
    dir2saveData = 'data'
    event = Earthquake(eqUrl, dir2saveData)
    # event.downloadData()
    # event.processData(f'{dir2saveData}/{event.folder2minAgo}', -120, 480)
    event.processData(f'{dir2saveData}/{event.folder20secAgo}', -20, 100)
    
    
if __name__ == "__main__":
    main()