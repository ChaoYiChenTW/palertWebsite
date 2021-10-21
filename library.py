import os
import pandas as pd
import shutil
import xml.etree.ElementTree as ET
import zipfile
from obspy.core import UTCDateTime
        

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
    """
    function getCwbStationInfo( xmlfile )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : ET (xml.etree.ElementTree)
                 pd (pandas)
              
    Description: to get station information of a event.
                 
    Parameters : xmlfile, str (a xml file including event information)
    
    Return     : a pd.dataframe including all station information
    
    Examples of sage:
        >> df = getCwbStationInfo(xmlfile)
    """
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    ns = {'d': root.tag.split('}')[0].strip('{')}
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
    return df


def getEqParameters(dict, xmlfile):
    """
    function getEqParameters( xmlfile )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : ET (xml.etree.ElementTree)
              
    Description: to get the eq parameters (lat, lon dep, ML).
                 
    Parameters : dict, dict (an empty to output eq parameters)
                 xmlfile, str (a xml file including event information)
    
    Examples of sage:
        >> xmlfile = 'CWB-EQ110095-2021-0915-185053.xml'
        >> eqParameters = {}
        >> print(getEqParameters(eqParameters, xmlfile))
        {'longitude': 121.39, 'latitude': 23.16, 'depth': 20.6, 'magnitude': 4.5}
    """
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    ns = {'d': root.tag.split('}')[0].strip('{')}
    eqParameters = root.find('d:dataset/d:earthquake/d:earthquakeInfo', ns)
    dict['originTImeUTC'] = UTCDateTime(eqParameters.find('d:originTime', ns).text)
    dict['longitude'] = float(eqParameters.find('d:epicenter/d:epicenterLon', ns).text)
    dict['latitude'] = float(eqParameters.find('d:epicenter/d:epicenterLat', ns).text)
    dict['depth'] = float(eqParameters.find('d:depth', ns).text)
    dict['magnitude'] = float(eqParameters.find('d:magnitude/d:magnitudeValue', ns).text)


def removeFile(filename):
    """
    function removeFile( filename )
    
    Author: Chaoyi Chen
    Date: Fall 2021
    
    Module     : os
              
    Description: to remove a file.
                 
    Parameters : filename, str (file to remove)
    
    Examples of sage:
        >> removeFile('text.txt')
    """
    if os.path.isfile(filename):
        os.remove(filename)
        

if __name__ == "__main__":
    print('You\'re in a function library.')
    
    xmlfile = 'libraryTest/CWB-EQ110091-2021-0901-062756.xml'
    # print('\n---test getEqParameters---')
    # dict = {}
    # getEqParameters(dict, xmlfile)
    # print(dict)
    # 
    # print('\n---test unzipFile---')
    # inputName = 'libraryTest/download.zip'
    # outputName = 'libraryTest/unzipFolder'
    # unzipFile(inputName, outputName)
    # 
    # print('\n---test getCwbStationInfo---')
    # print(getCwbStationInfo(xmlfile))