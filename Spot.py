import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

scope = "user-read-currently-playing user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


async def get_spotify_track():
    try:
        results = sp.current_user_playing_track()
        return results
    except:
        print("failed to get results")
        return None