# revised from alert_xml.py
# chaoyi 2021.10.05
#
# to monitor the CWB opendata platform for latest earthquake report

from library import unzipFile, getOriginTimeUTC, getEqParameters, getCwbStationInfo
import os
import pandas as pd
import xml.etree.ElementTree as ET
import wget

cwbOpendataApi = "opendataapi?dataid=E-A0015-001&authorizationkey=CWB-BFBE0988-4DB7-47A8-AE56-3D82EFBFDF6E"

def main():
    xmlDir = 'xml'
    os.chdir(xmlDir)
    
    removeExistOpendataApi()
    # download data from cwb opendata api
    downloadZipfile = "download.zip"
    downloadXMLfiles(downloadZipfile)

    xmlFolder = 'xmlfiles'
    unzipFile(downloadZipfile, xmlFolder)

    for xmlfile in sorted(os.listdir(xmlFolder)):
        # get event id
        eqid = getEqid(f"{xmlFolder}/{xmlfile}")
        lastestEqid = getLatestEqid()
        print('Latest Event: ', lastestEqid, 'This Event: ', eqid)
        if eqid > lastestEqid:
            originTImeUTC = getOriginTimeUTC(f"{xmlFolder}/{xmlfile}")
            eqLongitude, eqLatitude, eqDepth, eqMagnitude = getEqParameters(f"{xmlFolder}/{xmlfile}")
            df = getCwbStationInfo(f"{xmlFolder}/{xmlfile}")
            # print(df)
      

def removeExistOpendataApi():
    global cwbOpendataApi
    if os.path.isfile(cwbOpendataApi): 
        os.remove(cwbOpendataApi)


def downloadXMLfiles(filename):
    global cwbOpendataApi
    if os.path.isfile(filename):
        os.remove(filename)
    wget.download(f"https://opendata.cwb.gov.tw/{cwbOpendataApi}", out=filename)


def getEqid(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    return int(root[7][1][1].text)


def getLatestEqid():
    with open('latest.EQ') as f:
        return int(f.readlines()[0])


if __name__ == "__main__":
    main()
