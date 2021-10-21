# revised from alert_xml.py
# chaoyi 2021.10.05
#
# to monitor the CWB opendata platform for latest earthquake report

import library
import os
import pandas as pd
import xml.etree.ElementTree as ET
import wget


def main():
    xmlDir = 'xml'
    os.chdir(xmlDir)

    cwbOpendataApi = "opendataapi?dataid=E-A0015-001&authorizationkey=CWB-BFBE0988-4DB7-47A8-AE56-3D82EFBFDF6E"
    library.removeFile(cwbOpendataApi)
    zipfile = "download.zip"
    downloadXMLfiles(cwbOpendataApi, zipfile)

    xmlFolder = 'xmlfiles'
    library.unzipFile(zipfile, xmlFolder)

    for xmlfile in sorted(os.listdir(xmlFolder)):
        eqid = getEqid(f"{xmlFolder}/{xmlfile}")
        lastestEqid = getLatestEqid()
        print('Latest Event: ', lastestEqid, 'This Event: ', eqid)
        if eqid > lastestEqid:
            eqParameters = {}
            library.getEqParameters(eqParameters, f"{xmlFolder}/{xmlfile}")
            print(eqParameters)
            df = library.getCwbStationInfo(f"{xmlFolder}/{xmlfile}")
            print(df)
     

def downloadXMLfiles(cwbOpendataApi, filename):
    """
    function downloadXMLfiles( cwbOpendataApi, filename )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : os
                 wget
              
    Description: to download xmlfiles with eq information from CWB opendata api.
                 
    Parameters : cwbOpendataApi, str
                 filename, str (output filename)
    
    Examples of sage:
        >> downloadXMLfiles(cwbOpendataApi, zipfile)
    """
    if os.path.isfile(filename):
        os.remove(filename)
    wget.download(f"https://opendata.cwb.gov.tw/{cwbOpendataApi}", out=filename)


def getEqid(filename):
    """
    function getEqid( filename )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : ET (xml.etree.ElementTree)
              
    Description: to get the eq id number.
                 
    Parameters : filename, str (a xmlfile)
    
    Return     : eq id number, int
    
    Examples of sage:
        >> xmlFolder = 'xmlfiles'
        >> xmlfile = 'CWB-EQ110091-2021-0901-062756.xml'
        >> print(getEqid(f"{xmlFolder}/{xmlfile}"))
        110091
    """
    tree = ET.parse(filename)
    root = tree.getroot()
    ns = {'d': root.tag.split('}')[0].strip('{')}
    eqid = root.find('d:dataset/d:earthquake/d:earthquakeNo', ns).text
    return int(eqid)


def getLatestEqid():
    """
    function getLatestEqid( )
    
    Author: Chaoyi Chen
    Date: Fall 2021
              
    Description: to get the latest processed eq id number.
    
    Return     : latest eq id number, int
    
    Examples of sage:
        >> print(getLatestEqid())
        110091
    """
    with open('latest.EQ') as f:
        return int(f.readlines()[0])


if __name__ == "__main__":
    main()
