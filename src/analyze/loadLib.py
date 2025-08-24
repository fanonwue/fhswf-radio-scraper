'''
Library to load previously saved data from the crawler for analysis.

contains some helperfunctions to load and harmonize the data as well as some functions 
that just contain common functionality
'''

import sys, os
import json
import logging
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def getOutputDir() -> str:
    outdir = os.path.join(os.path.dirname(__file__),'..', '..','output_analysis')
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir

def findParsable(dir: str, exclude: list = None, include: list = None) -> list[str]:
    '''
    Find all subdirs in the given dir that contain parsed data (i.e. have a 'parsed' subdir)
    '''
    if exclude is None:
        exclude = ['_landing_page', 'OffizielleCharts']
    if include is None:
        include = []
    dirs = [d for d in os.listdir(dir) 
                if os.path.isdir(os.path.join(dir,d)) 
                and (not any(e in d for e in exclude)
                and (len(include) == 0 or any(i in d for i in include)))
                and os.path.exists(os.path.join(dir,d,'parsed'))
            ]
    return dirs

def harmonizeTime(data: list, filename: str) -> str:
    '''
    Harmonize time information in the data dicts: ensure that all dicsts have an iso formatted datetime entry'''
    date = filename.split('_')[-1].split('.')[0]
    timezone = '+02:00' # NOTE: all data is from german speeaking radio stations and the summer -> CEST
    for d in data:
        if 'datetime' in d.keys():
            pass
        elif 'time' in d.keys():
            dateTimeStr = f"{date}T{d['time']}{timezone}" 
            d['datetime'] = dateTimeStr
            d.pop('time', None) # remove time entry
        elif 'datetime' not in d.keys() and 'time' not in d.keys():
            raise ValueError(f'no datetime or time information found in data from {filename}')
        d['datetime'] = datetime.datetime.fromisoformat(d['datetime'])

def loadJsonFiles(baseDir: str) -> tuple[list[list[dict]], list[str]]:
    parseDirs = findParsable(baseDir)
    loaded = []
    parentDirs = []
    for dir in [os.path.join(baseDir, d, 'parsed') for d in parseDirs]:
        parsedFiles = os.listdir(dir)
        parentDir = os.path.basename(os.path.dirname(dir)) 
        parentDirs.append(parentDir)
        logging.info(f'loading files{len(parsedFiles): >4} from: {dir}')
        for file in parsedFiles:
            with open(os.path.join(dir,file), 'r+') as fp:
                thisLoaded = json.load(fp)
                # add station information to loaded data
                for l in thisLoaded: 
                    l['station'] = parentDir
                harmonizeTime(thisLoaded, file)
                loaded.append(thisLoaded)
    loaded = [d for sublist in loaded for d in sublist]
    return loaded, parentDirs

def checkDictStructure(dictList: list[dict]) -> bool:
    # Check that all dicts in the list have the same structure
    keys = dictList[0].keys()
    for d in dictList[1:]:
        if (any([k not in keys for k in d.keys()])):
            logging.warning(f'incompatible structures: {keys} <-> {d.keys()}')
            return False
    return True

def harmonizeData(songData: list[dict]) -> list[dict]:
    '''
    hamonize the dicts so that all list entries have the keys: datetime, title, performer
    '''
    transfomations = [('artist', 'performer')]
    for t in transfomations:
        songData =[{
            (t[1] if k == t[0] else k): v
            for k,v in song.items()
        } for song in songData]
    
    # make everything all caps to minimize different spellings of the same thing
    for song in songData:
        for key in song:
            if key in ['performer', 'title', 'station']:
                song[key] = song[key].upper()

    return songData

def loadOfficialChartsJson(baseDir: str) -> dict[list[dict]]:
    '''load previously saved official charts data from the crawler by calendar week'''
    parseDirs = findParsable(baseDir, include=['OffizielleCharts'] ,exclude=[])
    loaded = dict()
    for dir in [os.path.join(baseDir, d, 'parsed') for d in parseDirs]:
        parsedFiles = os.listdir(dir)
        for file in parsedFiles:
            with open(os.path.join(dir,file), 'r+') as fp:
                thisLoaded = json.load(fp)
                iso_ts = file.split('_')[-1].split('.')[0]
                iso_year, iso_week, _ = datetime.datetime.fromisoformat(iso_ts).isocalendar()
                isoWeekStr = f"{iso_year}-W{iso_week:02d}"
                loaded[isoWeekStr] = thisLoaded
    return loaded