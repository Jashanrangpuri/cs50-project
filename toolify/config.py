import os
import base64

from dotenv import load_dotenv
load_dotenv()

REDIRECT_URI = "http://127.0.0.1:5000/callback"
TOKEN_URL = "https://accounts.spotify.com/api/token"
STATE = os.getenv("SPOTIFY_STATE")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")

auth_string = CLIENT_ID + ":" + CLIENT_SECRET
auth_bytes = auth_string.encode("utf-8")
auth_base64 = base64.b64encode(auth_bytes)
ENCODED_STRING = auth_base64.decode("utf-8")

USER_PLAYLISTS = "https://api.spotify.com/v1/me/playlists"
SAVED_SONGS = "https://api.spotify.com/v1/me/tracks"