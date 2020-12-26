import argparse
import getpass

def main():

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--debug', default=False, required=False, action='store_true', dest="debug", help='debug flag') 
    main_parser = argparse.ArgumentParser()

    # Services
    service_subparsers = main_parser.add_subparsers(title="Service",dest="svc")

    # Spotify
    spotify_parser = service_subparsers.add_parser("spotify", parents=[parent_parser]) 
    spotify_parser.add_argument("--nocache", help="disable tinydb cache",dest="spotify_nocache", action="store_true", default=False)
    spotify_parser.add_argument("--pull", help="pull info from spotify to cache",dest="spotify_pull", action="store_true", default=False)
    spotify_parser.add_argument("--info", dest="spotify_info", action="store_true", default=False)
    spotify_parser.add_argument("--playlist", help="playlist spotify:playlist:id", dest="spotify_playlist", required=True)

    action_subparser = spotify_parser.add_subparsers(title="Actions",dest="action_command") 
    action_parser = action_subparser.add_parser("archive", help="sync with gdrive sheet",parents=[parent_parser]) 
    action_parser.add_argument("--backend", dest="archive_backend", default="google-sheets")
    # Add other service here

    args = main_parser.parse_args()
    if args.debug == True:
        print(args)

    if args.svc == "spotify":
        spotify = Spotify(nocache=args.spotify_nocache,
                          pull=args.spotify_pull)
        if args.spotify_info == True:
            spotify.info(playlist=args.spotify_playlist)

        tracks = spotify.tracks(playlist=args.spotify_playlist)
        if args.action_command == "archive":
            if args.archive_backend == "google-sheets":
                gs = GoogleSheets()
                gs.insert_or_update(tracks)


### Move to other file later
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tinydb import TinyDB, Query

class Spotify():
    spotify = None
    playlist = None
    nocache = False
    pull = False
    db = None

    def __init__(self, nocache=False,pull=False):
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        self.nocache = nocache
        self.pull = pull
        if self.nocache is False:
            self.db = TinyDB('spotify.json')
    
    def info(self, playlist):
        info = None
        if self.nocache is False:
            print("fetch from cache")
            if "info" in self.db.tables():
                table = self.db.table('info')
                # uses the last entry, most updated
                for row in table:
                    info = row

        if info is None or self.pull:
            print("fetch from API")
            info = self.spotify.playlist(playlist_id = playlist,fields="collaborative,description,external_urls,followers,href,id,images,name,owner,primary_color,public,snapshot_id,type,uri")
            if self.nocache is False:
                print("cache value to tinydb")
                self.db.drop_table('info')
                table = self.db.table('info')
                table.insert(info)

        print(info)
        return info

    def tracks(self,playlist):
        tracks = []
        if self.nocache is False:
            print("fetch from cache")
            if "tracks" in self.db.tables():
                table = self.db.table('tracks')
                # uses the last entry, most updated
                for row in table:
                    tracks.append(row)

        if len(tracks) == 0 or self.pull:
            print("fetch from API")
            results = self.spotify.playlist_items(playlist_id=playlist)
            tracks = results['items']
            while results['next']:
                results = self.spotify.next(results)
                tracks.extend(results['items'])
            
            if self.nocache is False:
                print("cache value to tinydb")
                self.db.drop_table('tracks')
                table = self.db.table('tracks')
                table.insert_multiple(tracks)
                
        print(len(tracks))
        return(tracks)


import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tinydb import Query

class GoogleSheets():
    client = None
    def __init__(self, cred=".metallum-ebdc4c739506.json", sheetname="Metal Female Fronted Bands Playlist", worksheet_name="Auto"):
        self.db = TinyDB('google.json')
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds']
        creds = ServiceAccountCredentials.from_json_keyfile_name(cred)
        self.client = gspread.authorize(creds)
    
        # Find a workbook by name and open the first sheet
        # Make sure you use the right name here.
        self.sheet = self.client.open(sheetname).worksheet(worksheet_name)
    
    def insert_or_update(self, tracks):
        header = ['uuid', 'country', 'artist', 'album', 'song', 'vocal', 'style', 'added_at', 'spotify_url', 'metallum_url']
        self.sheet.append_row(header)
        Row = Query()
        data=[]
        for track in tracks:

            uuid_str = str(uuid.uuid5(uuid.NAMESPACE_X500,"{}.{}.{}".format(
                    track['track']['artists'][0]['name'],
                    track['track']['album']['name'],
                    track['track']['name'])))
            row = { "uuid": uuid_str,
                    "country": "", 
                    "artist": track['track']['artists'][0]['name'],
                    "album": track['track']['album']['name'],
                    "song": track['track']['name'],
                    "vocal": "",
                    "style": "Metal",
                    "added_at": track['added_at'],
                    "spotify_url": track['track']['external_urls']['spotify'],
                    "metallum_url": ""}


            location = self.db.search(Row.uuid.matches(uuid_str))
            if self.db.search(Row.uuid.matches(uuid_str)):
                self.db.update(row, Row.uuid == uuid_str)
            else:
                self.db.insert(row)
            data.append(row)

        self.sheet.add_rows(len(data))
        crange = 'A2:{}{}'.format(chr(len(header)+64),len(data))
        cell_range = self.sheet.range(crange)
        flattened_test_data = []
       
        for row in data:
            for column in header:
                flattened_test_data.append(row[column])
    
        for i, cell in enumerate(cell_range):
            cell.value = flattened_test_data[i]
    
        self.sheet.update_cells(cell_range)

if __name__ == "__main__":
    main()
