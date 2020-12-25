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

    action_subparser = spotify_parser.add_subparsers(title="action",dest="action_command") 
    action_parser = action_subparser.add_parser("cache", help="second",parents=[parent_parser]) 
    # Add other service here

    args = main_parser.parse_args()
    if args.debug == True:
        print(args)

    if args.svc == "spotify":
        spotify = Spotify(nocache=args.spotify_nocache,
                          pull=args.spotify_pull)
        if args.spotify_info == True:
            spotify.info(playlist=args.spotify_playlist)

        spotify.run()


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

    def cache(self):
        print("cache")

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
                table = self.db.table('info')
                table.insert(info)

        print(info)

    def run(self):
        print("run")

# spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
# 
# results = spotify.artist_albums(birdy_uri, album_type='album')
# albums = results['items']
# while results['next']:
#     results = spotify.next(results)
#     albums.extend(results['items'])
# 
# for album in albums:
#  

if __name__ == "__main__":
    main()
