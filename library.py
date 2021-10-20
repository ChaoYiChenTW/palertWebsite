import os
import pandas as pd
import shutil
import xml.etree.ElementTree as ET
import zipfile
from obspy.core import UTCDateTime
    
    
def getEqParameters(xmlfile):
    """
    function getEqParameters( xmlfile )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : ET (xml.etree.ElementTree)
            
    Function   : ET.parse
              
    Description: to get the eq parameters (lat, lon dep, ML).
                 
    Parameters : xmlfile (a Xml file)
    
    Return     : eqLongitude, float
                 eqLatitude, float 
                 eqDepth, float 
                 eqMagnitude, float
    
    Examples of sage:
        >> xmlfile = 'CWB-EQ110095-2021-0915-185053.xml'
        >> print(getEqParameters(xmlfile))
        (121.39, 23.16, 20.6, 4.5)
    """
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    eqLongitude = float(root[7][1][7][1][0].text)
    eqLatitude = float(root[7][1][7][1][1].text)
    eqDepth = float(root[7][1][7][2].text)
    eqMagnitude = float(root[7][1][7][3][1].text)
    return eqLongitude, eqLatitude, eqDepth, eqMagnitude


def getOriginTimeUTC(xmlfile):
    """
    function getOriginTimeUTC( xmlfile )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : ET (xml.etree.ElementTree)
                 obspy.core
            
    Function   : ET.parse
                 obspy.core.UTCDateTime
              
    Description: to get the eq origin time from cwb xmlfile and 
                 convert time zone from Taipei to UTC.
                 
    Parameters : xmlfile (a Xml file)
    
    Return     : the eq origin time as an UTCDateTime object
    
    Examples of sage:
        >> xmlfile = 'libraryTest/CWB-EQ110095-2021-0915-185053.xml'
        >> print(getOriginTimeUTC(xmlfile))
        2021-09-15T10:50:53.000000Z
    """
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    return UTCDateTime(root[7][1][7][0].text)


def unzipFile(inputName, outputName):
    """
    function unzipFile( inputName, outputName )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : os
                 shutil
                 zipfile
              
    Description: to unzip a zip file.
                 
    Parameters : inputName (name of the input zip file)
    
    Return     : folder or file named as outputName
    
    Examples of sage:
        >> inputName = 'libraryTest/download.zip'
        >> outputName = 'libraryTest/unzipFolder'
        >> unzipFile(inputName, outputName)
        >> ls libraryTest
        download.zip   unzipFolder
    """
    if os.path.isdir(outputName): shutil.rmtree(outputName)
    if os.path.isfile(outputName): os.remove(outputName)
    with zipfile.ZipFile(inputName, 'r') as zip_ref:
        zip_ref.extractall(outputName)
        
        
def getCwbStationInfo(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    # ns = {'d': root.tag.split('}')[0].strip('{')}
    ns = {'d': 'urn:cwb:gov:tw:cwbcommon:0.1'}
    data = {'stationCode': [],
            'stationLon': [],
            'stationLat': [],
            'stationDist': [],
            'stationAz': [],
            'stationIntensity': [],
            'stationPGAz': [],
            'stationPGAns': [],
            'stationPGAew': []}
    for station in root.findall('d:dataset/d:earthquake/d:intensity/d:shakingArea/d:eqStation', ns):
        if station.find('d:stationCode', ns) == None:
            data['stationCode'].append(None)
        else:
            data['stationCode'].append(station.find('d:stationCode', ns).text)
            
        if station.find('d:stationLon', ns) == None:
            data['stationLon'].append(None)
        else:
            data['stationLon'].append(float(station.find('d:stationLon', ns).text))
        if station.find('d:stationLat', ns) == None:
            data['stationLat'].append(None)     
        else:
            data['stationLat'].append(float(station.find('d:stationLat', ns).text))
        if station.find('d:distance', ns) == None:
            data['stationDist'].append(None)
        else:
            data['stationDist'].append(float(station.find('d:distance', ns).text))       
        if station.find('d:azimuth', ns) == None:
            data['stationAz'].append(None)       
        else:
            data['stationAz'].append(float(station.find('d:azimuth', ns).text)) 
        if station.find('d:stationIntensity', ns) == None:
            data['stationIntensity'].append(None)        
        else:
            data['stationIntensity'].append(int(station.find('d:stationIntensity', ns).text))
        if station.find('d:pga/d:vComponent', ns) == None:
            data['stationPGAz'].append(None)      
        else:
            data['stationPGAz'].append(float(station.find('d:pga/d:vComponent', ns).text)) 
        if station.find('d:pga/d:nsComponent', ns) == None:
            data['stationPGAns'].append(None)      
        else:
            data['stationPGAns'].append(float(station.find('d:pga/d:nsComponent', ns).text)) 
        if station.find('d:pga/d:ewComponent', ns) == None:
            data['stationPGAew'].append(None)   
        else:
            data['stationPGAew'].append(float(station.find('d:pga/d:ewComponent', ns).text))
    df = pd.DataFrame(data)
    df['stationPGAmax'] = df[['stationPGAz', 'stationPGAns', 'stationPGAew']].max(axis=1)
    print(df)
    return df
        

if __name__ == "__main__":
    print('You\'re in a function library.')
    
    # print('\n---test getEqParameters---')
    xmlfile = 'libraryTest/CWB-EQ110091-2021-0901-062756.xml'
    # print(getEqParameters(xmlfile))
    # 
    # print('\n---test getOriginTimeUTC---')
    # print(getOriginTimeUTC(xmlfile))
    # 
    # print('\n---test unzipFile---')
    # inputName = 'libraryTest/download.zip'
    # outputName = 'libraryTest/unzipFolder'
    # unzipFile(inputName, outputName)
    
    print('\n---test getCwbStationInfo---')
    getCwbStationInfo(xmlfile)