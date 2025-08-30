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
            uniqueArtists.add(entry['performer'])
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
        breakpoint()
        return [], response.status_code

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

def simpifyGenreList(artistGenres: list[str]) -> list[str]:
    '''
    Simplify genre list by merging similar genres.
    '''
    # basic simplification map for merging similar genres
    base_genres = ['rock', 'pop', 'hip hop', 'jazz', 'classical', 'electro', 'country', 
                   'blues', 'reggae', 'metal', 'punk', 'folk', 'soul', 'funk', 'disco', 'jazz', 
                   'unknown', 'dance', 'schlager', 'indie', 'r&b', 'reggae', 'afro', 'latin', 'spoken word']
    # special cases
    simplification_map = {
        'rnb': 'r&b','edm': 'electronic','new wave': 'pop','post-hardcore': 'rock','post hardcore': 'rock','singer-songwriter': 'folk','singer songwriter': 'folk',
        'grime': 'hip hop', 'uk grime': 'hip hop', 'neue deutsche welle': 'pop','uk drill': 'hip hop', 'grunge': 'rock', 'motown': 'soul', 'melodic rap': 'hip hop', 
        'synthwave': 'electronic', 'chicago drill': 'hip hop', 'drill': 'hip hop', 'hi-nrg': 'electronic', 'techengue': 'electronic', 'chanson': 'folk', 
        'techengue': 'electronic', 'alté': 'electronic', 'miami bass': 'hip hop', 'americana': 'folk', 'new age': 'classical', 'gabber': 'electronic', 'cold wave': 'rock',
        'americana': 'folk', 'new rave': 'electronic', 'shoegaze': 'rock', 'grime': 'hip hop', 'uk grime': 'hip hop', 'hi-nrg': 'electronic', 'post-grunge': 'rock',
        'big room': 'electronic', 'christmas': 'pop', 'children\'s music': 'pop', 'new jack swing': 'r&b', 'horrorcore': 'hip hop', 'ebm': 'electronic', 
        'darkwave': 'rock', 'industrial': 'rock', 'madchester': 'electronic','big band': 'jazz','variété française': 'pop','hardstyle': 'electronic','musicals': 'pop',
        'polka': 'folk','easy listening': 'pop','orchestra': 'classical','anime': 'pop','honky tonk': 'folk','drum and bass': 'electronic','tekno': 'electronic',
        'bassline': 'electronic','aor': 'rock','dub': 'electronic','quiet storm': 'r&b','bluegrass': 'folk','sertanejo': 'latin','candombe': 'latin', 'bossa nova': 'latin',
        'samba': 'latin', 'nova mpb': 'latin', 'mpb': 'latin', 'forró': 'latin', 'forró tradicional': 'latin', 'arrocha': 'latin', 'piseiro': 'latin','sertanejo universitário': 'latin', 
        'sertanejo tradicional': 'latin', 'mariachi': 'latin', 'son cubano': 'latin', 'salsa': 'latin', 'merengue': 'latin', 'bachata': 'latin','bolero': 'latin', 'tango': 'latin', 
        'cha cha cha': 'latin', 'tejano': 'latin', 'villancicos': 'latin', 'trova': 'latin', 'chanson québécoise': 'latin', 'maluku': 'latin', 'cajun': 'latin', 'brazilian phonk': 'latin',
        'amapiano': 'afro', 'gqom': 'afro', 'azonto': 'afro', 'hiplife': 'afro', 'bongo flava': 'afro', 'kuduro': 'afro', 'shatta': 'afro', 'kizomba': 'afro', 'zouk': 'afro', 
        'kompa': 'afro', 'soca': 'afro','comedy': 'spoken word', 'worship': 'spoken word', 'christian': 'spoken word', 'gospel': 'spoken word','soudtrack': 'classical',
        'uk garage': 'electronic','bhangra': 'folk','chillwave': 'electronic','flamenco': 'folk','downtempo': 'electronic','lounge': 'electronic','brazilian bass': 'electronic',
        'newgrass': 'folk','breakbeat': 'electronic','ska': 'reggae','future bass': 'electronic','lo-fi beats': 'electronic','neo-psychedelic': 'rock','gnawa': 'folk',
        'boogie-woogie': 'jazz','phonk': 'hip hop','drift phonk': 'hip hop','red dirt': 'country','lullaby': 'classical','jungle': 'electronic','raï': 'folk','sea shanties': 'folk',
        'ballroom vogue': 'electronic','chillstep': 'electronic','adult standards': 'pop','arabesk': 'folk','riot grrrl': 'punk','jam band': 'rock','swing music': 'jazz','celtic': 'folk',
        'moombahton': 'electronic','deathcore': 'metal','chamber music': 'classical','vocaloid': 'electronic','idm': 'electronic','big beat': 'electronic','southern gothic': 'folk',
        'native american music': 'folk','canzone napoletana': 'folk','neomelodico': 'folk','ragga': 'reggae','soundtrack': 'classical','iskelmä': 'folk','bounce': 'hip hop','psychobilly': 'rock',
        'freestyle': 'hip hop','nightcore': 'electronic','opera': 'classical','requiem': 'classical','frenchcore': 'electronic','slowcore': 'rock','ambient': 'electronic','drone': 'electronic',
        'glitch': 'electronic','choral': 'classical','minimalism': 'classical','riddim': 'electronic','doo-wop': 'pop','djent': 'metal','opm': 'pop','fado': 'folk','queercore': 'punk',
        'avant-garde': 'classical','agronejo': 'latin','ccm': 'spoken word','gregorian chant': 'classical','medieval': 'classical','noise music': 'electronic','baltimore club': 'electronic',
        'boom bap': 'hip hop',
    } 
    partial_match_map = {
        'hop' : 'hip hop',
        'house' : 'electronic',
        'techno': 'electronic',
        'trance': 'electronic',
        'rap': 'hip hop',
        'hardcore': 'rock',
        'singer-songwriter': 'folk',
        'emo': 'rock',
    }
    simplified_genres = list()
    genreCount = {}
    for artist, genres in artistGenres:
        for genre in genres:
            thisGenres = list()
            if genre in simplification_map:
                if simplification_map[genre] not in thisGenres:
                    thisGenres.append(simplification_map[genre])
            elif any(pm in genre.lower() for pm in partial_match_map):
                for pm in partial_match_map:
                    if pm in genre.lower() and partial_match_map[pm] not in thisGenres:
                        thisGenres.append(partial_match_map[pm])
            elif(any(bg in genre.lower() for bg in base_genres)):
                for bg in base_genres:
                    if bg in genre.lower() and bg not in thisGenres:
                        thisGenres.append(bg)
            else:
                print(f'{genre}, ')
                thisGenres.append(genre)
        simplified_genres.append((artist, thisGenres))
    return list(simplified_genres)

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
        #logging.info(f'Processing artist {idx+1}/{len(uniquArtists)}: {artist}')
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
        with open(jsonPath, 'w', encoding='utf-8') as fp:
            json.dump(artistsWithGenres, fp, ensure_ascii=False, indent=4)
    
    drawGenerePieChart(simpifyGenreList(artistsWithGenres), title='')
    

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