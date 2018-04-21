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
        self.interpolated_loudness_func = None
        self.interpolated_pitch_funcs = None

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

        :return; None
        """

        if self.sp.current_playback()["is_playing"]:
            self.sp.pause_playback()
        self.sp.seek_track(0)

    def _load_track_data(self):
        """
        Obtain track audio data from Spotipy API and run necessary analysis to generate data needed for visualization

        :return: None
        """

        # Get track audio data for current song from Spotipy API
        analysis = self.sp.audio_analysis(self.track["item"]["id"])
        segments = analysis["segments"]
        self.track_duration = self.track["item"]["duration_ms"]/1000

        # Extract useful data
        s_t = [segment["start"] for segment in segments]
        start_times = np.array(s_t)
        l = [segment["loudness_start"] for segment in segments]
        loudnesses = np.array(l)

        # Perform data interpolation
        self.interpolated_loudness_func = interp1d(start_times, loudnesses)
        pitch_lists = [segment["pitches"] for segment in segments]
        self.interpolated_pitch_funcs = []
        for w in range(12):
            self.interpolated_pitch_funcs.append(interp1d(start_times, [pitch_list[w] for pitch_list in pitch_lists], kind="cubic"))

    def load_curr_track(self):
        """
        Fetches current track (waits for a track if necessary) and calls reset_track() and load_track_data()

        :return: None
        """
        self.track = self.sp.current_user_playing_track()
        while not self.track:
            self.track = self.sp.current_user_playing_track()
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
        print("DIFF: ", diff, diff < margin)
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

        if not self.sp.current_playback()["is_playing"]:
            self.sp.start_playback()
        while self.playback_pos <= self.track_duration:
            start = time.perf_counter()
            self.playback_pos += sample_rate
            if abs(round(self.playback_pos))%1 == 0 and abs(self.playback_pos-round(self.playback_pos)) < sample_rate/2:
                thread = threading.Thread(target=self.sync_within_margin, kwargs={"margin": 0.1})
                thread.start()
            print(self.playback_pos, ": ", self.interpolated_loudness_func(self.playback_pos))
            end = time.perf_counter()
            time.sleep(sample_rate - (end-start))

if __name__ == "__main__":
    # Instantiate an instance of SpotifyVisualizer and visualize the currently playing track
    visualizer = SpotifyVisualizer()
    visualizer.authorize()
    visualizer.load_curr_track()
    visualizer.sync()
    visualizer.visualize()