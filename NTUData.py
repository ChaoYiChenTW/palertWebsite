import glob
import linecache
import numpy as np
import os
import pandas as pd
import re
import requests
import shutil
import subprocess
import sys 
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
        ftpNTU = FTP()
        ftpNTU.connect('140.112.65.220', 2121)  # IP, port
        ftpNTU.login()  # user, password
        ftpNTU.cwd(f'events/{self.__originTimeUTC.year}{self.__originTimeUTC.month:02d}')
        if f'{self.folder2minAgo}.tar.bz2' not in ftpNTU.nlst():
            datetime2minAgo = self.__originTimeUTC - 120 + 1
            self.folder2minAgo = datetime2minAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'
            if f'{self.folder2minAgo}.tar.bz2' not in ftpNTU.nlst():
                datetime2minAgo = self.__originTimeUTC - 120 - 1
                self.folder2minAgo = datetime2minAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'
                if f'{self.folder2minAgo}.tar.bz2' not in ftpNTU.nlst():
                    sys.exit('This event doesn\'t exit in NTU server.')
        ftpNTU.quit()
        datetime20secAgo = datetime2minAgo + 100
        self.folder20secAgo = datetime20secAgo.strftime('%Y%m%d_%H%M%S') + '_MAN'

    def downloadData(self):
        ftpNTU = FTP()
        ftpNTU.connect('***.***.***.***', 2121)  # IP, port
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
        os.chdir('/home/palert/data')
    
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
    
    def getPGAsDataframe(self):
        print(f'Get pgas dataframe...')
        self.df = pd.read_csv('stalist.txt', sep=" ",header=None)
        self.df.columns =['staName', 'staLatitude', 'staLongitude']
        self.df['PGAsMaxInENZ'] = 0
        self.df['intensity'] = 0
        self.df['PGAsResultantOfENZ'] = 0
        self.df['PGAsResultantOfEN'] = 0
        
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')
        for i, row in self.df.iterrows():
            p = subprocess.Popen(["/home/palert/data/rdsac2", row['staName']], stdout=subprocess.PIPE)
            pgas = p.communicate()[0].decode("utf-8").split()
            self.df.loc[i, 'PGAsMaxInENZ'] = float(pgas[0])
            self.df.loc[i, 'intensity'] = float(pgas[1])
            self.df.loc[i, 'PGAsResultantOfENZ'] = float(pgas[2])
            self.df.loc[i, 'PGAsResultantOfEN'] = float(pgas[3])
        os.chdir('../../../')        

    def getPGAsFilename(self):
        fileTime = self.__originTimeUTC.strftime('%Y%m%d%H%M%S')
        self.__filePGAs = f'{self.__dir}/{self.folder20secAgo}/{fileTime}PGAs.txt'
        self.__filePGAs_1 = f'{self.__dir}/{self.folder20secAgo}/{fileTime}PGAs_1.txt'
    
    def getPGAsFile(self):        
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')
        print(f'Get {self.__filePGAs}...')
        
        f = open(self.__filePGAs, "w")
        
        originTimehhmmss = self.__originTimeUTC.strftime('%H%M%S')
        f.write(f'{self.__originTimeUTC.year} {self.__originTimeUTC.month:02} {self.__originTimeUTC.day:02} {originTimehhmmss} {self.__latitude} {self.__longitude} {self.__depth} {self.__magnitude}\n')
        
        for i in range(len(self.df)):
            if self.df.loc[i, 'PGAsMaxInENZ'] > 0:
                f.write(f"{self.df.loc[i, 'staName']} {self.df.loc[i, 'staLatitude']:.6f} {self.df.loc[i, 'staLongitude']:.6f} {self.df.loc[i, 'PGAsMaxInENZ']} {self.df.loc[i, 'intensity']} {self.df.loc[i, 'PGAsResultantOfENZ']} {self.df.loc[i, 'PGAsResultantOfEN']}\n")
        
        f.close()
        
        shutil.copyfile(self.__filePGAs, self.__filePGAs_1)
        if not os.path.exists(f'/var/www/html/palert/pga/staticpga/{self.__originTimeUTC.year}'):
            os.makedirs(f'/var/www/html/palert/pga/staticpga/{self.__originTimeUTC.year}')
        shutil.copy(self.__filePGAs, '/var/www/html/palert/pga/staticpga/', follow_symlinks=True)
        shutil.copy(self.__filePGAs_1, '/var/www/html/palert/pga/staticpga/', follow_symlinks=True)
        shutil.copy(self.__filePGAs, f'/var/www/html/palert/pga/staticpga/{self.__originTimeUTC.year}', follow_symlinks=True)
        shutil.copy(self.__filePGAs_1, f'/var/www/html/palert/pga/staticpga/{self.__originTimeUTC.year}', follow_symlinks=True)
        
        os.chdir('/home/palert/data/')        
        
    def saveStaInfo2Sac(self):
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')
        print(f'Save station informtation to sac files...')
        for sta in list(self.df.index):
            for comp in ['E', 'N', 'Z']:
                file = f'{sta}.HL{comp}.TW.--'
                if os.path.exists(file):
                    sac = SACTrace.read(file)
                    sac.stla = self.df.loc[sta, 'staLatitude']
                    sac.stlo = self.df.loc[sta, 'staLongitude']
                    sac.write(file)
        os.chdir('../../../')
    
    def contourMulti(self):
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')
        subprocess.run('csh /home/palert/data/contour_multi.csh', shell=True)
        os.chdir('../../../')
        
    def accum3sPGAs(self):
        originTime = self.__originTimeUTC.strftime('%Y%m%d%H%M%S')
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')
        if not os.path.exists("accum"):
            os.makedirs("accum")
        os.chdir("accum")
        for i in range(1,41):
            os.system('cp ../*TW.-- ./')
            print(f'cut 0-{3 * i}')
            st = read('*TW*')
            starttime = self.__originTimeUTC - 20
            endtime = starttime + 3 * i
            self.cutWaveform(st, starttime, endtime)
            
            PGAout = f'PGAs_{i:02}'
            with open(PGAout, 'w') as f:
                f.write(f"{endtime.strftime('%Y %m %d %H%M%S')}\n")
                
                for index, row in self.df.iterrows():
                    p = subprocess.Popen(["/home/palert/data/rdsac2", row['staName']], stdout=subprocess.PIPE)
                    pgas = [*map(float, p.communicate()[0].decode("utf-8").split())]
                    f.write(f"{row['staName']} {row['staLatitude']:.6f} {row['staLongitude']:.6f} {pgas[0]:.3f} {pgas[1]:.2f} {pgas[2]:.3f} {pgas[3]:.3f}\n")
        os.system('rm -rf *TW*')
        os.chdir('../')
        shutil.copytree('accum', f'/var/www/html/palert/pga/staticpga/{originTime}.accum')
        shutil.copytree('accum', f'/var/www/html/palert/pga/staticpga/{self.__originTimeUTC.year}/{originTime}.accum')
        os.chdir('/home/palert/data/')
     
    def accum3sPGAsPlot(self):
        os.chdir(f'{self.__dir}/{self.folder20secAgo}')
        inputfile = self.__filePGAs_1.split('/')[-1]
        subprocess.run('csh /home/palert/data/gmt.csh', shell=True, input=inputfile, encoding='ascii')
        # subprocess.run('csh /home/palert/data/gmt_bk.csh', shell=True)
        os.chdir('/home/palert/data/')

    def passFiles2tesis(self):
        # 這部分可能要再跟其芳確認一下 (from NTU_xml.csh)
        return
        originTime = self.__originTimeUTC.strftime('%Y%m%d%H%M%S')
        files = [self.__filePGAs, f'{self.__dir}/{originTime}_1.png']
        paths = []
        subprocess.run(["scp", FILE, "USER@SERVER:PATH"])
    
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
    eqUrl = "https://scweb.cwb.gov.tw/en-us/earthquake/imgs/ee2022010805121947003"
    ### tmp: remove this line
    event = Earthquake(eqUrl)
    # event.downloadData()
    # event.processData(f'{event.dir}/{event.folder2minAgo}', -120, 480)
    # event.processData(f'{event.dir}/{event.folder20secAgo}', -20, 100)
    # event.getPGAsDataframe()
    # event.getPGAsFilename()
    # event.getPGAsFile()
    # event.saveStaInfo2Sac()
    # event.contourMulti()
    # event.accum3sPGAs()
    # event.accum3sPGAsPlot()

if __name__ == "__main__":
    main()
