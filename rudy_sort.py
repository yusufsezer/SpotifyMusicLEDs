import spotipy
import spotipy.util as util
from rudy_credentials import USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI

scope = "user-top-read"

token = util.prompt_for_user_token(USERNAME, scope, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

if token:
    sp = spotipy.Spotify(auth=token)

print(sp.current_user_top_artists()["items"][1]["name"])