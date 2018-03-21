import time
import spotipy
import threading
import spotipy.util as util
import numpy as np
from credentials import USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
from scipy.interpolate import spline
from functools import reduce
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

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
s = np.array(s_t)
# l = [segment["loudness_start"] for segment in segments]
p = list(reduce(lambda x, y: x + y, (segment["pitches"] for segment in segments)))
p_lists = [segment["pitches"] for segment in segments]
# p_lists_2 = [[(li[x]+li[x+1])/2 for x in range(6)] for li in p_lists]
# print(p_lists_2)
p_averages = np.array([reduce(lambda x, y: x + y, segment["pitches"])/12 for segment in segments])
beats = reduce(lambda x, y: x+y, [[beat["start"], (beat["start"]+beat["duration"]/3), (beat["start"]+2*beat["duration"]/3)] for beat in analysis["beats"]])
beat_vals = reduce(lambda x, y: x+y, [[beat["confidence"], beat["confidence"]*(2/3), beat["confidence"]*(1/3)] for beat in analysis["beats"]])
p_times_smooth = np.linspace(s.min(), s.max(), num=len(s), endpoint=True)
p_average_smooth = interp1d(p_times_smooth, p_averages)

pitches = np.array(p)
# start_times = np.array(s_t)
# print(p)
# print(segments[0]["pitches"], segments[1]["pitches"])
# pitch_start_times = np.array([segment["start"]+(i*segment["duration"]/12) for segment in segments for i in range(12)])
# plt.plot(p_times_smooth, p_average_smooth(p_times_smooth))
# plt.show()
# plt.ion()
# plt.ylim((0, 1))
# rects = plt.bar(range(12), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], align='center')
# for x in range(len(p_lists)):
#     for i in range(12):
#         rects[i].set_height(p_lists[x][i])
#     print(s_t[x])
#     plt.pause(0.01)




# loudnesses = np.array(l)
start_times_smooth = np.linspace(s.min(), s.max(), s_t[-1]*15)
pitches_lists_smooth = []
for w in range(12):
    pitches_lists_smooth.append(interp1d(s_t, [li[w] for li in p_lists], kind="cubic"))
# for w in range(6):
#     pitches_lists_smooth.append(interp1d(s_t, [li[w] for li in p_lists_2], kind="cubic"))
# pitch_start_times_smooth = np.linspace(pitch_start_times.min(), pitch_start_times.max(), pitch_start_times[-1])
# pitch_start_times_smooth = np.linspace(pitch_start_times.min(), pitch_start_times.max(), num=len(pitch_start_times), endpoint=True)
# loudnesses_smooth = spline(start_times, loudnesses, start_times_smooth)
# pitches_smooth = spline(pitch_start_times, pitches, pitch_start_times_smooth)
# pitches_smooth = interp1d(pitch_start_times_smooth, pitches, kind="cubic")
# loudness_dict = dict(zip([round(k, 2) for k in start_times_smooth], loudnesses_smooth))
# pitches_smooth = interp1d(pitch_start_times, pitches, kind='cubic')
# plt.plot(pitch_start_times, p)
# plt.plot(pitch_start_times_smooth, pitches_smooth(pitch_start_times_smooth))
# plt.show()
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Pause playback, sync, and resume playback
# curr_time = sp.current_playback()["progress_ms"] / 1000
# pos = 0
# if curr_time > 0:
#     sp.pause_playback()
#     curr_time = sp.current_playback()["progress_ms"]/1000
#     for i in range(len(start_times_smooth)):
#         if start_times_smooth[i] > curr_time:
#             pos = i
#             break
#     sp.seek_track(int(start_times_smooth[pos]*1000))
#     sp.start_playback()

def is_synced_at_time(time=0):
    playback_time = sp.current_playback()["progress_ms"] / 1000
    return abs(playback_time - time) < 0.03

def sync():
    sp.pause_playback()
    playback_time = sp.current_playback()["progress_ms"] / 1000
    for i in range(len(start_times_smooth)):
        if abs(start_times_smooth[i] - playback_time) < 0.03:
            start_times_pos = i
            break
        else:
            start_times_pos = 0
    sp.seek_track(int(start_times_smooth[start_times_pos] * 1000))
    return start_times_pos

def play(pos):
    plt.ion()
    plt.ylim((0, 1))
    rects = plt.bar([0 for x in range(12)], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], align='center')
    penalty = 0
    t = round(start_times_smooth[pos], 2)
    sp.start_playback()
    while t <= start_times_smooth[-1]:
        start = time.perf_counter()
        # print("{0:.2f}".format(t), ": ", loudness_dict[t])
        for x in range(len(p_lists)):
            for i in range(12):
                rects[i].set_height(p_lists[x][i])
            print(t)
            plt.pause(0.01)
        stop = time.perf_counter() - start
        time.sleep(0.03 - stop - penalty if 0.03 - stop - penalty > 0 else 0)
        penalty = 0
        # if 29.97 <= rt <= 30.03 or 34.97 <= rt <= 35.03 or 39.97 <= rt <= 40.03:
        if 0.03 - stop - penalty < 0:
            penalty += abs(0.03 - stop)
            print(penalty, " penalty")
        t = round(t + 0.03, 2)

def play_visualize(pos=0):
    plt.ion()
    plt.ylim((0, 1.2))
    rects = plt.bar(range(12), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], align='center')
    # rects = plt.bar([0], [1])
    penalty = 0
    sp.start_playback()
    for i in range(len(start_times_smooth)):
    # for i in range(len(beats)):
        start = time.perf_counter()
        for j in range(0, 12):
            rects[j].set_height(pitches_lists_smooth[j](start_times_smooth[i]))
        # rects[0].set_height(beat_vals[i])
        plt.pause(0.01)
        print(start_times_smooth[i])
        diff = start_times_smooth[i+1]-start_times_smooth[i]
        # diff = beats[i+1] - beats[i]
        stop = time.perf_counter() - start
        time.sleep(diff - stop - penalty if diff - stop - penalty > 0 else 0)
        penalty = 0
        if diff - stop - penalty < 0:
            penalty += abs(diff - stop)
            print(penalty, " penalty")


# synced_pos = sync()
play_visualize()
# print(p)
# print(segments[0]["start"], segments[0]["duration"], segments[0]["pitches"])


# Iterate through track data
# Should add occasional check to make sure still in sync
# Otherwise, in very long songs, there may be some drift
# penalty = 0
# t = start_times_smooth[pos-1]
# penalty = 0
# while t <= start_times_smooth[-1]:
#     start = time.perf_counter()
#     rt = round(t, 2)
#     print("{0:.2f}".format(rt), ": ", loudness_dict[rt])
#     stop = time.perf_counter() - start
#     time.sleep(0.03-stop-penalty if 0.03-stop-penalty > 0 else 0)
#     penalty = 0
#     # if 29.97 <= rt <= 30.03 or 34.97 <= rt <= 35.03 or 39.97 <= rt <= 40.03:
#     if 0.03 - stop - penalty < 0:
#         penalty += abs(0.03 - stop)
#         print(penalty)
#     t += 0.03