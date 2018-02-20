import time
import spotipy
import spotipy.util as util
from credentials import USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
import numpy as np
from scipy.interpolate import spline

scope = "user-modify-playback-state"

token = util.prompt_for_user_token(USERNAME, scope, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)

if token:
    sp = spotipy.Spotify(auth=token)

track = sp.current_user_playing_track()
while track == None:
    track = sp.current_user_playing_track()
    time.sleep(1)

analysis = sp.audio_analysis(track["item"]["id"])
segments = analysis["segments"]


# ~~~~~ Should thread this code ~~~~~
s_t = [segment["start"] for segment in segments]
l = [segment["loudness_start"] for segment in segments]
start_times = np.array(s_t)
loudnesses = np.array(l)
start_times_smooth = np.linspace(start_times.min(), start_times.max(), s_t[-1]*100)
loudnesses_smooth = spline(start_times, loudnesses, start_times_smooth)
loundess_dict = dict(zip([round(k, 2) for k in start_times_smooth], loudnesses_smooth))
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Pause playback, sync, and resume playback
curr_time = sp.current_playback()["progress_ms"] / 1000
pos = 0
if curr_time > 0:
    sp.pause_playback()
    curr_time = sp.current_playback()["progress_ms"]/1000
    for i in range(len(start_times_smooth)):
        if start_times_smooth[i] > curr_time:
            pos = i
            break
    sp.seek_track(int(start_times_smooth[pos]*1000))
    sp.start_playback()

# Iterate through track data in real-time
# Should add occasional check to make sure still in sync
# Otherwise, in very long songs, there may be some drift
penalty = 0
t = start_times_smooth[pos-1]
penalty = 0
while t <= start_times[-1]:
    start = time.perf_counter()
    rt = round(t, 2)
    stop = time.perf_counter() - start
    time.sleep(0.03-stop-penalty if 0.03-stop-penalty > 0 else 0)
    penalty = 0
    if 29.97 <= rt <= 30.03 or 34.97 <= rt <= 35.03 or 39.97 <= rt <= 40.03:
        print(rt)
    if 0.03 - stop - penalty < 0:
        penalty += abs(0.03 - stop)
        print(penalty)
    t += 0.03