'''
Get weekly top lists of artists and songs from the parsed playlists of various radio stations.
'''

import os
import json
import logging
import datetime
import requests
import time
from bdb import BdbQuit

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

HEADERS = {"User-Agent": "SongMetadataApp/1.0 (contact@example.com)"}

def search_song(title, artist=None):
    query = f'{artist} {title}' if artist else title
    #query = query.replace(' ', '%20')
    url = f"https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json&limit=1"
    r = requests.get(url, headers=HEADERS)
    if r is None:
        logging.warning(f'musicbrainz query failed for {title} - {artist} status: No response')
        return None
    data = r.json()
    if (r.status_code != 200):
        logging.warning(f'musicbrainz query failed for {title} - {artist} status: {r.status_code}, count: {data.get("recording-count", 0)}')
        return None
    if not data.get("recordings"):
        logging.info(f'No recordings found for {title} - {artist}')
        return None
    if len(data["recordings"]) == 0:
        logging.info(f'No recordings found for {title} - {artist}')
    return data["recordings"][0] if data.get("recordings") else None

def get_release_group_genres(release_group_id):
    url = f"https://musicbrainz.org/ws/2/release-group/{release_group_id}?inc=genres+url-rels&fmt=json"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    if r.status_code != 200:
        logging.warning(f'musicbrainz release group query failed for {release_group_id} status: {r.status_code}')
        return None
    genres = [g["name"] for g in data.get("genres", [])]

    # If no genres, check for Wikidata link
    if not genres and "relations" in data:
        for rel in data["relations"]:
            if rel["type"] == "wikidata":
                wikidata_id = rel["url"]["resource"].split("/")[-1]
                genres = get_genres_from_wikidata(wikidata_id)
                break
    return genres

def get_genres_from_wikidata(entity_id):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
    r = requests.get(url)
    data = r.json()
    claims = data["entities"][entity_id]["claims"]
    genres = []
    if "P136" in claims:  # genre property
        for g in claims["P136"]:
            genre_id = g["mainsnak"]["datavalue"]["value"]["id"]
            label = data["entities"].get(genre_id, {}).get("labels", {}).get("en", {}).get("value")
            if label:
                genres.append(label)
    return genres

def get_song_metadata(title, artist=None):
    song = search_song(title, artist)
    if not song:
        return None

    release = song["releases"][0] if "releases" in song else None
    release_group_id = release["release-group"]["id"] if release else None

    genres = []
    if release_group_id:
        genres = get_release_group_genres(release_group_id)
    
    if not genres:
        logging.info(f'No genres found for {title} - {artist}')
        return None

    return {
        "title": song["title"],
        "artist": song["artist-credit"][0]["name"],
        "genres": genres if genres else ["Unknown"]
    }



def main(baseDir: str):
    loadedData, stations  = loadLib.loadJsonFiles(baseDir)
    # flatten loaded data into a simple list of dicts
    loadedData = loadLib.harmonizeData(loadedData)

    if not loadLib.checkDictStructure(loadedData):
        raise ValueError('Incompatible data structures found in loaded data. Please harmonize first.')
    
    songsWithGenres = []
    # try to load existing data
    jsonPath = os.path.join(loadLib.getOutputDir(), 'song_genres.json')
    if os.path.exists(jsonPath):
        with open(jsonPath, 'r+', encoding='utf-8') as fp:
            songsWithGenres = json.load(fp)
        logging.info(f'Loaded {len(songsWithGenres)} existing song genres from {jsonPath}')


    
    uniqueSongs = getUniquieSongs(loadedData)
    logging.info(f'Found {len(uniqueSongs)} unique songs in the loaded data.')

    for song in uniqueSongs:
        # only query for songs we do not have yet
        if any(s[0] == song[0] and s[1] == song[1] for s in songsWithGenres):
            continue
        try:
            generes = get_song_metadata(song[1].lower(), song[0].lower())
        except Exception as e:
            logging.error(f'Error fetching metadata for {song[0]} - {song[1]}: {e}')
            generes = None
        if generes:
            songsWithGenres.append((song[0], song[1], generes))
        else:
            logging.warning(f'No metadata found for song: {song[0]} - {song[1]}')
        logging.info(f'Processed {len(songsWithGenres)}/{len(uniqueSongs)} songs')
        # save progress every 100 songs
        if len(songsWithGenres) % 100 == 0:
            with open(jsonPath, 'w+', encoding='utf-8') as fp:
                json.dump(songsWithGenres, fp, ensure_ascii=False, indent=4)
            logging.info(f'Saved song genres to {jsonPath}')
        time.sleep(1) # be nice to the API



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