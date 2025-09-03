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

def splitArtists(artistField: str) -> list[str]:
    '''
    Split artist field into individual artists based on common delimiters.
    '''
    delimiters = ['FEAT','FEAT.', '|', '&', '/', ' X ', ', ']
    for delim in delimiters:
        if delim in artistField:
            thisArtists = [artist.strip() for artist in artistField.split(delim)]
            artists = []
            for artist in thisArtists:
                artists.extend(splitArtists(artist))
            return artists
    # remove trailing dots and spaces
    return [artistField.strip().strip('.').strip()]

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
        'boom bap': 'hip hop', 'japanese vgm': 'electronic', 'mathcore': 'metal', 'footwork': 'electronic', 'lo-fi': 'electronic', 'go-go': 'funk', 'manele': 'folk', 'hard bop': 'jazz', 
        'dansktop': 'folk', 'southern gospel': 'spoken word', 'devotional': 'spoken word', 'bhajan': 'spoken word', 'melbourne bounce': 'electronic', 'screamo': 'rock', 
        'space music': 'electronic', 'dansband': 'folk', 'dubstep': 'electronic', 'drumstep': 'electronic', 'experimental': 'electronic', 'dark ambient': 'electronic', 'vaporwave': 'electronic',
        'laïko': 'folk','entehno': 'folk','asakaa': 'hip hop','highlife': 'afro','tollywood': 'pop','sandalwood': 'pop','kollywood': 'pop','3 step': 'electronic','tecnobrega': 'electronic',
        'crunk': 'hip hop','moroccan chaabi': 'folk','chilean mambo': 'latin','k-ballad': 'pop','sexy drill': 'hip hop','cumbia': 'latin','cumbia sonidera': 'latin','khaleeji': 'folk',
        'axé': 'latin','cumbia norteña': 'latin','norteño': 'latin','mizrahi': 'folk','shibuya-kei': 'electronic','brazilian gospel': 'spoken word','hyphy': 'hip hop','traditional music': 'folk',
        'desi': 'folk','malay': 'folk','bollywood': 'pop',
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