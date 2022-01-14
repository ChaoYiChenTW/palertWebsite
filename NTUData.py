import linecache
import shutil
import os
import requests
import re
from obspy.core import UTCDateTime
from bs4 import BeautifulSoup

class Earthquake():
    def __init__(self, url):
        self.__url = url
        self.__parameters = self.__obtainEqParameters()
        
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
        self.__year = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[60:64])
        self.__month = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[57:59])
        self.__date = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[54:56])
        self.__hour = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[65:67])
        self.__minute = int(linecache.getline(f'tmp/tmp.txt', lineNum+5)[68:70])
        self.__second = float(linecache.getline(f'tmp/tmp.txt', lineNum+5)[71:75])
        originTimeString = f"{self.__year}-{self.__month:02}-{self.__date:02}T{self.__hour:02}:{self.__minute:02}:{self.__second}+08"
        self.__originTime = UTCDateTime(originTimeString)
        parameters['Earthquake No'] = self.__eqNo
        parameters['Origin Time'] = self.__originTime
        # shutil.rmtree("tmp")
        return parameters
        
    @property
    def parameters(self):
        return self.__parameters
        

def main():
    print("Please find your target event on this website: https://scweb.cwb.gov.tw/en-us/earthquake/data")
    print("Earthquake Information -> Details -> Earthquake Report")
    # eqUrl = input("Insert url of the earthquake report: ")  ### tmp: remove #
    eqUrl = "https://scweb.cwb.gov.tw/en-us/earthquake/imgs/ee2022010805122045003"  ### tmp: remove this line
    event = Earthquake(eqUrl)
    print(event.parameters)
    
    
if __name__ == "__main__":
    main()