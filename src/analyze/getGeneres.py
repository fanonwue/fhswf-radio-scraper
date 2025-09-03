import os
import json
import logging
import datetime
import requests
import time
from bdb import BdbQuit
from matplotlib import pyplot as plt

# local imports
import loadLib

def getUniquieSongs(data: list[dict]) -> list[tuple[str,str]]:
    '''
    Get a set of unique song titles from the data list of dicts.
    '''
    uniqueSongs = set()
    for entry in data:
        if 'title' in entry:
            uniqueSongs.add((entry['performer'],entry['title']))
    uniqueSongs = list(uniqueSongs)
    return uniqueSongs

def getUniquieArtists(data: list[dict]) -> list[str]:
    '''
    Get a set of unique artists from the data list of dicts.
    '''
    uniqueArtists = set()
    for entry in data:
        if 'performer' in entry:
            for artist in loadLib.splitArtists(entry['performer']):
                uniqueArtists.add(artist)
    uniqueArtists = list(uniqueArtists)
    return uniqueArtists

def getAccessToken(client_id: str, client_secret: str) -> str:
    auth_url = "https://accounts.spotify.com/api/token"
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    if auth_response.status_code != 200:
        raise Exception(f"Failed to obtain access token: {auth_response.status_code} - {auth_response.text}")

    auth_data = auth_response.json()
    return auth_data['access_token']

def getArtistGenres(artist: str, headers: dict) -> tuple[list[str], int]:
    '''
    Get artist genres from Spotify API.
    NOTE: Spotify API does not provide song-specific genres, only artist genres.
    '''
    search_url = "https://api.spotify.com/v1/search"
    params = {
        'q': artist,
        'type': 'artist',
        'limit': 1
    }
    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code != 200:
        logging.warning(f'Spotify artist search failed for {artist} status: {response.status_code}')
        return [], response.status_code

    data = response.json()
    if not data.get('artists') or not data['artists'].get('items'):
        logging.info(f'No artist found for {artist}')
        return ['Unknown'], response.status_code

    artist_data = data['artists']['items'][0]
    genres = artist_data.get('genres', [])
    if not genres:
        return ['Unknown'], response.status_code

    return genres, response.status_code

def drawGenerePieChart(artistGenres: list[tuple[str,list[str]]], title=''):
    genreCount = {}
    for artist, genres in artistGenres:
        for genre in genres:
            if genre not in genreCount:
                genreCount[genre] = 0
            genreCount[genre] += 1

    labels = list(genreCount.keys())
    sizes = list(genreCount.values())

    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(title)
    plt.tight_layout()
    outFile = title.replace(' ','_') + '_genres.png'
    logging.info(f'Saving figure as {outFile}')
    plt.savefig(outFile)
    plt.show()

def main(baseDir: str):
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')

    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("Spotify CLIENT_ID and CLIENT_SECRET must be set as environment variables.")
    
    loadedData, stations  = loadLib.loadJsonFiles(baseDir)
    # flatten loaded data into a simple list of dicts
    loadedData = loadLib.harmonizeData(loadedData)

    if not loadLib.checkDictStructure(loadedData):
        raise ValueError('Incompatible data structures found in loaded data. Please harmonize first.')
    
    artistsWithGenres = []
    # try to load existing data
    jsonPath = os.path.join(loadLib.getOutputDir(), 'song_genres_sf.json')
    if os.path.exists(jsonPath):
        with open(jsonPath, 'r+', encoding='utf-8') as fp:
            artistsWithGenres = json.load(fp)
        logging.info(f'Loaded {len(artistsWithGenres)} existing song genres from {jsonPath}')
    else:
        logging.info(f'No existing song genres found at {jsonPath}. Starting fresh.')

    uniquArtists = getUniquieArtists(loadedData)
    logging.info(f'Found {len(uniquArtists)} unique artists in the loaded data.')

    access_token = getAccessToken(CLIENT_ID, CLIENT_SECRET)
    headers = {"Authorization": f"Bearer {access_token}"}

    for idx, artist in enumerate(uniquArtists):
        # only query for songs we do not have yet
        if (idx % 50) == 0 and idx > 0:
            logging.info(f'Processing artist {idx+1}/{len(uniquArtists)}: {artist}')
        if any(s[0] == artist for s in artistsWithGenres):
            continue
        try:
            genres, status_code = getArtistGenres(artist.lower(), headers)
            if status_code == 429:
                logging.warning('Rate limited by Spotify API. Waiting for 60 seconds before retrying.')
                time.sleep(60)
                access_token = getAccessToken(CLIENT_ID, CLIENT_SECRET)
                headers = {"Authorization": f"Bearer {access_token}"}
                genres, status_code = getArtistGenres(artist.lower(), headers)
            if status_code != 200:
                logging.error(f'Failed to fetch genres for artist: {artist}, status code: {status_code}')
                continue
        except Exception as e:
            logging.error(f'Error fetching metadata for {artist}: {e}')
            genres = ['Unknown']
        if genres:
            artistsWithGenres.append((artist, genres))
            #logging.info(f'Found genres for artist {artist}: {genres}')
        else:
            logging.warning(f'No genres found for artist: {artist}')
        # Save progress after each artist to avoid data loss
        if (idx % 10) == 0:
            with open(jsonPath, 'w', encoding='utf-8') as fp:
                json.dump(artistsWithGenres, fp, ensure_ascii=False, indent=4)
    
    # Final save of all data
    with open(jsonPath, 'w', encoding='utf-8') as fp:
        json.dump(artistsWithGenres, fp, ensure_ascii=False, indent=4)
    
    drawGenerePieChart(loadLib.simpifyGenreList(artistsWithGenres), title='')
    drawGenerePieChart(artistsWithGenres, title='Genre raw all artists')
    

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
    except KeyboardInterrupt:
        logging.info('Exiting program. Keyboard Interrupt.')
        exit(0)