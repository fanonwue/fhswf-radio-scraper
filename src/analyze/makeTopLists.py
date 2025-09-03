import sys, os
import logging
import traceback
import csv
import json

# 3rd party imports
import matplotlib.pyplot as plt

# local imports
import loadLib



def countPerformersAndSongs(songData: list[dict], timeRange: tuple[int,int] = (0,24)) -> dict:
    '''
    Count the number of times each performer and their songs appear in the songData list of dict
    excluding entries outside the given timeRange (hours in 24h format)
    '''
    performerStats = dict()
    for entry in songData:
        if 'performer' not in entry.keys():
            logging.warning(f'Key \'performer\' not found in {entry}')
            continue
            
        time = entry['datetime'].hour
        if timeRange[0] > timeRange[1]:
            # e.g. 22 - 02
            if time < timeRange[0] and time > timeRange[1]:
                # exclide entries outside the time range
                continue
        else:
            if time < timeRange[0] or time > timeRange[1]:
                # exclide entries outside the time range
                continue
        
        # count performer occurences - how offten is an artist played
        # this sould be the sum of all songs played 
        invlovedArtists = loadLib.splitArtists(entry['performer'])
        for artist in invlovedArtists:
            if artist not in performerStats:
                performerStats[artist] = {'cnt': 0}
            performerStats[artist]['cnt'] += 1

        #if entry['performer'] not in performerStats:
        #    performerStats[entry['performer']] = {'cnt': 0}
        #performerStats[entry['performer']]['cnt'] += 1


        # count songs
        for artist in invlovedArtists:
            if entry['title'] not in performerStats[artist]:
                performerStats[artist][entry['title']] = 1
            else:
                performerStats[artist][entry['title']] += 1
    return performerStats 

def drawBarGraph(labledData: list[tuple[str,int]], xlable='', ylable='', title=''):
    print(f'Drawing bar graph for {title}...')
    lables, values = zip(*labledData)
    plt.bar(lables, values)
    # Formatting
    plt.xticks(rotation=90)
    plt.xlabel(xlable)
    plt.ylabel(ylable)
    #plt.title(title)
    plt.xticks([])
    plt.tight_layout()
    # Save data 
    outFile = title.replace(' ','_') + '.png'
    logging.info(f'Saving figure as {outFile}')
    plt.show()


def analyzeArtistsAndSongs(performerStats:dict, station: str, drawFigures:bool, topCount: int = 20) -> tuple[list[tuple[str,int]],list[tuple[str,int]]]:
    """
    Print the most played artists and songs

    :returns: a sortet list of with the most played artist and a sortet list of the most played songs
    """
    logging.info(f'Analyzing {station}...')
    output_artist = [ (k,performerStats[k]['cnt']) for k in sorted(performerStats, key=lambda stat: performerStats[stat]['cnt'], reverse=True)]
    #output_str = f'Top {topCount} Artists: \n                          '+'\n                          '.join( [f'{out[0]}: {out[1]}' for out in output_artist[:topCount]] )
    logging.info( f'found {len(output_artist)} artists')
    #logging.info( output_str )

    # Sum of all songs played
    sumSongs = sum([o[1] for o in output_artist])
    # Sum of the times the top ten artists have been played accross all statios
    topSongs = sum([o[1] for o in output_artist[:topCount]]) 
    logging.info( f'There have been {sumSongs} songs aired. Of those songs {topSongs} where by the {topCount} most played artists ({(topSongs/sumSongs)*100:.2f}%)')

    if (drawFigures):
        drawBarGraph(output_artist[:100], 'artist', 'times played', f'Artist distribution ({station})')

    songs = []
    for p in performerStats:
        for s in performerStats[p]:
            if s != 'cnt':
                songs.append((p,s,performerStats[p][s]))
    songs = sorted(songs, key=lambda x: x[2], reverse=True)
    
    # Sum of all songs played
    sumSongs = sum([o[2] for o in songs])
    # Sum of the times the top ten artists have been played accross all statios
    topSongs = sum([o[2] for o in songs[:topCount]]) 
    logging.info( f'There have been {sumSongs} songs aired. Of those songs {topSongs} where in the {topCount} most played songs ({(topSongs/sumSongs)*100:.2f}%)')

    #output_str = f'Top {topCount} Songs: \n                          '+ '\n                          '.join( [f'{s[0]} - {s[1]}: {s[2]}' for s in songs[:topCount] ])
    #logging.info(output_str)
    if (drawFigures):
        drawBarGraph( [ (f'{s[0]} - {s[1]}',s[2]) for s in songs[:100] ], 'song', 'times played', f'Song distribution ({station})' )
    return output_artist, songs

def isInTimeRange(entry: dict, timeRange: tuple[int,int]) -> bool:
    '''
    Check if the entry's time is within the given timeRange (hours in 24h format)
    '''
    time = entry['datetime'].hour
    if timeRange[0] > timeRange[1]:
        # e.g. 22 - 02
        if time < timeRange[0] and time > timeRange[1]:
            return False
    else:
        if time < timeRange[0] or time > timeRange[1]:
            return False
    return True

def getGenreChart(performerStats: dict, station: str, drawFigures: bool, timeRange: tuple[int,int] = (0,24)) -> None:
    artistsWithGenres = []
    # try to load existing data
    jsonPath = os.path.join(loadLib.getOutputDir(), 'song_genres_sf.json')
    if os.path.exists(jsonPath):
        with open(jsonPath, 'r+', encoding='utf-8') as fp:
            artistsWithGenres = loadLib.simpifyGenreList(json.load(fp))
    
    genreCount = {}
    for stat in performerStats:
        if not isInTimeRange(stat, timeRange):
            continue
        artists = loadLib.splitArtists(stat['performer'])
        for genreStat in artistsWithGenres:
            for artist in artists:
                if genreStat[0].lower() == artist.lower():
                    if genreStat[1][0] == 'unknown':
                        continue
                    if genreStat[1][0] not in genreCount:
                        genreCount[genreStat[1][0]] = 0
                    genreCount[genreStat[1][0]] += 1
    
    labels = list(genreCount.keys())
    sizes = list(genreCount.values())

    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    #plt.title(f'Genre distribution ({station})')
    plt.tight_layout()
    outFile = station.replace(' ','_') +f'_{timeRange[0]}h_{timeRange[1]}h'  +  '_genres.png'
    logging.info(f'Saving figure as {outFile}')
    plt.savefig(outFile)
    if drawFigures:
        plt.show()


def outputCsv(artistData: list[tuple[str,int]], songData: list[tuple[str,int]], csvFile: str):
    logging.info(f'Saving top artists and songs to {csvFile}')
    csvPath = os.path.join(loadLib.getOutputDir(), csvFile)
    with open(csvPath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Artist', 'Times Played', 'Artist - Song', 'Times Played'])
        max_len = max(len(artistData), len(songData))
        for i in range(max_len):
            artist = artistData[i][0] if i < len(artistData) else ''
            artist_cnt = artistData[i][1] if i < len(artistData) else ''
            song = f'{songData[i][0]} - {songData[i][1]}' if i < len(songData) else ''
            song_cnt = songData[i][2] if i < len(songData) else ''
            writer.writerow([artist, artist_cnt, song, song_cnt])

def main(drawFigures: bool = False, outputCsvFile: bool = True, baseDir: str = None):
    loadedData, stations  = loadLib.loadJsonFiles(baseDir)
    # flatten loaded data into a simple list of dicts
    loadedData = loadLib.harmonizeData(loadedData)

    if not loadLib.checkDictStructure(loadedData):
        raise ValueError('Incompatible data structures found in loaded data. Please harmonize first.')
    
    performerStats = countPerformersAndSongs(loadedData)
    
    artists,songs = analyzeArtistsAndSongs(performerStats=performerStats, station='all stations', drawFigures=drawFigures)
    if outputCsvFile:
        csvFile = 'top_artists_and_songs.csv'
        outputCsv(artists, songs, csvFile)

    # analyze data per stataion
    for station in stations:
        station = station.upper()
        stationData = [data for data in loadedData if 
                       data['station'] == station
                       ]
        performerStatsStation = countPerformersAndSongs(stationData)
        artists, songs = analyzeArtistsAndSongs(performerStats=performerStatsStation, station=station, drawFigures=drawFigures)
        if outputCsvFile:
            csvFile = f'top_artists_and_songs_{station}.csv'
            outputCsv(artists, songs, csvFile)
        timeRanges = [ (23,6), (6,12), (12,18), (18,23) ]
        if 'SWR3' in station:
            for timeRange in timeRanges:
                getGenreChart(stationData, station, drawFigures, timeRange=timeRange)

def getArgPars():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze top artists and songs from parsed radio station data.')
    parser.add_argument('--draw', action='store_true', help='Draw bar graphs for artist and song distributions.')
    parser.add_argument('--no-csv', action='store_true', help='Do not output results to CSV files.')
    parser.add_argument('--parseDir', type=str, required=True,
                        help='Directory containing parsed data from various radio stations.')
    return parser.parse_args()


if __name__ == "__main__":
    args = getArgPars()
    try:
        main(args.draw, not args.no_csv, baseDir=args.parseDir)
    except Exception as e:
        traceback.print_exception(e, color=True)
