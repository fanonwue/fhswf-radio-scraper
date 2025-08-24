'''
Get weekly top lists of artists and songs from the parsed playlists of various radio stations.
'''

import os
import json
import logging
import datetime
from bdb import BdbQuit

# local imports
import loadLib



def getWeeklyData(loadedData: list[dict]) -> dict[list[dict]]:
    '''
    Split loaded data into weekly chunks (list of lists of dicts)
    '''
    # sort data by datetime
    loadedData = sorted(loadedData, key=lambda x: x['datetime'])
    startDate = loadedData[0]['datetime']
    endDate = loadedData[-1]['datetime']
    logging.info(f'Data ranges from {startDate} to {endDate}')

    # enrich data with ISO calendar week
    for entry in loadedData:
        iso_year, iso_week, _ = entry['datetime'].isocalendar()
        entry['iso_year'] = iso_year
        entry['iso_week'] = iso_week
    
    weeklyData = dict()
    # create weekly bins

    for entry in loadedData:
        week_key = f"{entry['iso_year']}-W{entry['iso_week']:02d}"
        if week_key not in weeklyData:
            weeklyData[week_key] = []
        weeklyData[week_key].append(entry) 
    
    logging.info(f'Split data into {len(weeklyData.keys())} weekly chunks.')
    return weeklyData


def getTop(data: list[dict], key: str, topCount: int = 10) -> list[tuple[str,int]]:
    '''
    Get the top N entries for a given key in the data list of dicts.
    Returns a list of tuples (key, count) sorted by count descending.
    '''
    countDict = dict()
    for entry in data:
        if key in entry:
            val = entry[key]
            if val not in countDict:
                countDict[val] = 0
            countDict[val] += 1
    topList = sorted(countDict.items(), key=lambda x: x[1], reverse=True)[:topCount]
    return topList

def getSongPositions(radioCharts: list[tuple[str, int]], officialCharts: list[dict], week: str) -> None:
    '''
    Get the position of artists in the official charts for a given week.
    
    enriches the data with the chart position if available
    '''
    newRadioCharts = []
    for titile, count in radioCharts:
        position = next((item['position'] for item in officialCharts if item['title'].upper() == titile), None)
        newRadioCharts.append({
            'title': titile,
            'count': count,
            'official_position': position
        })
    return newRadioCharts



def main(baseDir: str):
    loadedData, stations  = loadLib.loadJsonFiles(baseDir)
    # flatten loaded data into a simple list of dicts
    loadedData = loadLib.harmonizeData(loadedData)

    if not loadLib.checkDictStructure(loadedData):
        raise ValueError('Incompatible data structures found in loaded data. Please harmonize first.')
    
    artistCounts = getWeeklyData(loadedData)

    officialCharts = loadLib.loadOfficialChartsJson(baseDir)

    topArtists = dict()
    for week, data in artistCounts.items():
        topArtists[week] = getTop(data, 'performer', topCount=100)
        logging.info(f'Top artists for week {week}: {topArtists[week][:10]}')
    
    topSongs = dict()
    for week, data in artistCounts.items():
        topSongs[week] = getTop(data, 'title', topCount=100)
        topSongs[week] = getSongPositions(topSongs[week], officialCharts.get(week, []), week)
        logging.info(f'Top Titiles for week {week}: {topSongs[week][:10]}')

    #save to json
    outputFile = os.path.join(loadLib.getOutputDir(), 'weekly_top_artists.json')
    with open(outputFile, 'w', encoding='utf-8') as f:
        json.dump(topArtists, f, ensure_ascii=False, indent=4)
    logging.info(f'Saved weekly top artists to {outputFile}')

    outputFile = os.path.join(loadLib.getOutputDir(), 'weekly_top_songs.json')
    with open(outputFile, 'w', encoding='utf-8') as f:
        json.dump(topSongs, f, ensure_ascii=False, indent=4)
    logging.info(f'Saved weekly top songs to {outputFile}')



def getArgPars():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze top artists and songs from parsed radio station data.')
    parser.add_argument('--parseDir', type=str, required=True,
                        help='Directory containing parsed data from various radio stations.')
    return parser.parse_args()

if __name__ == '__main__':
    args = getArgPars()
    try:
        main(baseDir=args.parseDir)
    except BdbQuit:
        logging.info('Exiting program.')
        exit(0)