import time
import spotipy
import threading
import spotipy.util as util
import numpy as np
from credentials import USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
from scipy.interpolate import interp1d

class SpotifyVisualizer():

    def __init__(self):
        self.sp = None
        self.playback_pos = 0
        self.track_loaded = False
        self.track = None
        self.track_duration = None
        self.interpolated_loudness_buffer = []
        self.interpolated_pitch_buffer = []
        self.segments = None

    def authorize(self, scope="user-modify-playback-state"):
        """
        Handle the authorization workflow for the Spotipy API

        :param scope: the scope of access over the user's account to request
        :return: None
        """

        token = util.prompt_for_user_token(USERNAME, scope, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)
        if token:
            self.sp = spotipy.Spotify(auth=token)
        else:
            raise Exception("Unable to authenticate Spotify user.")

    def _reset_track(self):
        """
        Pauses track and seeks to beginning

        :return: None
        """

        if self.sp.current_playback()["is_playing"]:
            self.sp.pause_playback()
        self.sp.seek_track(0)

    def _continue_loading_data(self):
        while len(self.segments) > 0:
            time.sleep(3)
            self._load_track_data()

    def _load_track_data(self):
        """
        Obtain track audio data from Spotipy API and run necessary analysis to generate data needed for visualization

        :return: None
        """

        print("____________________________STARTED LOADING MORE DATA_______________________")

        # Get track audio data for current song from Spotipy API if necessary
        if not self.segments:
            analysis = self.sp.audio_analysis(self.track["item"]["id"])
            self.segments = analysis["segments"]
            self.track_duration = self.track["item"]["duration_ms"]/1000

        # Extract useful data for the next 7 seconds of playback
        i = 0
        s_t = []
        l = []
        pitch_lists = []
        while True:
            t = self.segments[i]["start"]
            l_ = self.segments[i]["loudness_start"]
            p = self.segments[i]["pitches"]
            s_t.append(t)
            l.append(l_)
            pitch_lists.append(p)
            i += 1
            if i > len(self.segments) - 1 or round(self.segments[i]["start"])  == round(self.segments[0]["start"] + 7):
                self.segments = self.segments[i-1:] # remove the analyzed data from segments
                break
        start_times = np.array(s_t)
        loudnesses = np.array(l)

        # Perform data interpolation
        interpolated_loudness_func = interp1d(start_times, loudnesses)
        interpolated_pitch_funcs = []
        for w in range(12):
            interpolated_pitch_funcs.append(interp1d(start_times, [pitch_list[w] for pitch_list in pitch_lists], kind="cubic"))

        # Add interpolated functions to buffers to be used when needed
        self.interpolated_loudness_buffer.append(interpolated_loudness_func)
        self.interpolated_pitch_buffer.append(interpolated_pitch_funcs)
        print(len(self.interpolated_loudness_buffer))

        print("************************************FINISHED LOADING MORE DATA********************************")

    def load_curr_track(self):
        """
        Fetches current track (waits for a track if necessary) and calls reset_track() and load_track_data()

        :return: None
        """
        self.track = self.sp.current_user_playing_track()
        while not self.track:
            self.track = self.sp.current_user_playing_track()
            print("Waiting for an active Spotify track.")
            time.sleep(1)
        self._reset_track()
        self._load_track_data()

    def is_synced_at_time(self, t=None, margin=1.0):
        """
        Check whether or not the position of the Spotify playback is within margin seconds of t

        :param t: time we want to by synced at. If None, uses visualizer's current playback time
        :param margin: upper bound on the acceptable difference between Spotify playback and visualizer playback
        :return: boolean
        """

        if t is None:
            t = self.playback_pos
        start = time.perf_counter()
        playback_time = self.sp.current_playback()["progress_ms"] / 1000
        end = time.perf_counter()
        diff = abs((playback_time - 3*(end - start)) - t)
        print("Sync difference: ", diff, diff < margin)
        return diff < margin

    def sync_within_margin(self, t=None, margin=1.0):
        """
        If Spotify playback is not within margin seconds of t, then sync the visualizer with Spotify playback

        :param t: time we want to be synced at. If None, uses visualizer's current playback time
        :param margin: upper bound on the acceptable difference between Spotify playback and visualizer playback
        :return: None
        """

        if t is None:
            t = self.playback_pos
        if not self.is_synced_at_time(t, margin):
            self.sync()

    def sync(self):
        """
        Syncs visualizer playback with Spotify playback

        :return: None
        """

        start = time.perf_counter()
        playback_time = self.sp.current_playback()["progress_ms"] / 1000
        end = time.perf_counter()
        t = playback_time + 0.3*(end - start)
        self.playback_pos = t if t > 0 else 0

    def visualize(self, sample_rate=0.03):
        """
        Starts playback on Spotify user's account (if necessary) and visualizes the current track in sync with playback

        :param sample_rate: how frequently to sample song data
        :return: None
        """
        loudness = self.interpolated_loudness_buffer.pop(0)
        threading.Thread(target=self._continue_loading_data).start()

        if not self.sp.current_playback()["is_playing"]:
            self.sp.start_playback()
        while self.playback_pos <= self.track_duration:
            start = time.perf_counter()
            self.playback_pos += sample_rate
            if abs(round(self.playback_pos))%1 == 0 and abs(self.playback_pos-round(self.playback_pos)) < sample_rate/2:
                thread = threading.Thread(target=self.sync_within_margin, kwargs={"margin": 0.1})
                thread.start()

            # Attempt to print interpolated loudness
            try:
                print(self.playback_pos, ": ", loudness(self.playback_pos))
            # If loudness value out of range, get data for next 15 seconds of song or terminate if song has ended
            except:
                if len(self.interpolated_loudness_buffer) > 0:
                    loudness = self.interpolated_loudness_buffer.pop(0)
                else:
                    print("Song Visualization Finished.")
                    break
            end = time.perf_counter()
            diff = sample_rate - (end-start)
            time.sleep(diff if diff > 0 else 0)

if __name__ == "__main__":
    # Instantiate an instance of SpotifyVisualizer and visualize the currently playing track
    print("Initializing Spotify Visualizer")
    visualizer = SpotifyVisualizer()
    print("Authorizing")
    visualizer.authorize()
    print("Loading Track Data")
    visualizer.load_curr_track()
    print("Syncing")
    visualizer.sync()
    print("Starting visualization")
    visualizer.visualize()