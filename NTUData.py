import shutil
import os
import requests
from bs4 import BeautifulSoup

class Earthquake():
    def __init__(self, url):
        self.__url = url
        self.__parameters = self.__obtainEqParameters()
        
    def __obtainEqParameters(self):
        if not os.path.exists("tmp"):
            os.makedirs("tmp")
        req = requests.get(self.__url)
        with open(f'tmp/tmp.txt', 'w') as eqReportHtml:
            eqReportHtml.write(req.content.decode('utf-8'))
        # shutil.rmtree("tmp")
        return "test"
        
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