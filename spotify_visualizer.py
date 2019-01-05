# !/usr/bin/env python3
# import apa102
from credentials import USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
import numpy as np
from scipy.interpolate import interp1d
import spotipy
import spotipy.util as util
import threading
import time
import apa102


class SpotifyVisualizer:
    """A class that allows for multithreaded music visualization via the Spotify API and an LED strip.

    This class allows for multithreaded music visualization via the Spotify API and an APA102 LED strip. This code was
    developed and tested using a 240-pixel (4 meter) Adafruit Dotstar LED strip, a Raspberry Pi 3 Model B and my
    personal Spotify account. After initializing an instance of this class, simply call visualize() to begin
    visualization (alternatively, simply run this module). Visualization will continue until the program is interrupted
    or terminated. There are 4 threads: one for visualization, one for periodically syncing the playback position with
    the Spotify API, one for loading chunks of track data, and one to periodically check if the user's current track has
    changed.

    Args:
        num_pixels (int): The number of pixels (LEDs) supported by the LED strip.

    Attributes:
            blue_grad_func (interp1d): A function mapping pitch strengths (range 0->1) to blue values (range 0 -> 255)
            buffer_lock (Lock): A lock for the interpolated buffers.
            data_segments (list): Data segments to be parsed and interpreted (fetched from Spotify API).
            green_grad_func (interp1d): A function mapping pitch strengths (range 0->1) to green values (range 0 -> 255)
            interpolated_loudness_buffer (list): Producer-consumer buffer holding interpolated loudness functions.
            interpolated_pitch_buffer (list): Producer-consumer buffer holding lists of interpolated pitch functions.
            interpolated_timbre_buffer (list): Producer-consumer buffer holding lists of interpolated timbre functions.
            num_pixels (int): The number of pixels (LEDs) on the LED strip.
            permission_scopes (str): A space separated str of the required permission scopes over the user's account.
            playback_pos (float): The current playback position (offset into track in seconds) of the visualization.
            pos_lock (Lock): A lock for playback_pos.
            red_grad_func (interp1d): A function mapping pitch strengths (range 0->1) to red values (range 0 -> 255)
            should_terminate (bool): A variable watched by all child threads (child threads exit if set to True).
            sp_gen (Spotify): Spotify object to handle main thread's interaction with the Spotify API.
            sp_load (Spotify): Spotify object to handle data loading thread's interaction with the Spotify API.
            sp_skip (Spotify): Spotify object to handle skip detection thread's interaction with the Spotify API.
            sp_sync (Spotify): Spotify object to handle synchronization thread's interaction with the Spotify API.
            sp_vis (Spotify): Spotify object to handle visualization thread's interaction with the Spotify API.
            track (dict): Contains information about the track that is being visualized.
            track_duration (float): The duration in seconds of the track that is being visualized.
            strip (APA102): APA102 object to handle interfacing with the LED strip.
    """

    def __init__(self, num_pixels):
        self.blue_grad_func = interp1d(np.array([0.0, 1.01]), np.array([255.0, 0.0]), kind="linear", assume_sorted=True)
        # self.blue_grad_func = interp1d(np.array([0.0, 1/3, 2/3, 1.01]), np.array([255.0, 200.0, 120.0, 0.0]), kind="cubic", assume_sorted=True)
        self.buffer_lock = threading.Lock()
        self.data_segments = []
        self.green_grad_func = interp1d(np.array([0.0, 1.01]), np.array([0.0, 0.0]), kind="linear", assume_sorted=True)
        # self.green_grad_func = interp1d(np.array([0.0, 1/3, 2/3, 1.01]), np.array([0.0, 120.0, 200.0, 255.0]), kind="cubic", assume_sorted=True)
        self.interpolated_loudness_buffer = []
        self.interpolated_pitch_buffer = []
        self.interpolated_timbre_buffer = []
        self.num_pixels = num_pixels
        self.permission_scopes = "user-modify-playback-state user-read-currently-playing user-read-playback-state"
        self.playback_pos = 0
        self.pos_lock = threading.Lock()
        self.red_grad_func = interp1d(np.array([0.0, 1.01]), np.array([0.0, 255.0]), kind="linear", assume_sorted=True)
        # self.red_grad_func = interp1d(np.array([0.0, 1/3, 2/3, 1.01]), np.array([0.0, 0.0, 0.0, 0.0]), kind="cubic", assume_sorted=True)
        self.should_terminate = False
        self.sp_gen = self.sp_load = self.sp_skip = self.sp_sync = self.sp_vis = None
        self.strip = apa102.APA102(num_led=num_pixels, global_brightness=20, mosi = 10, sclk = 11, order='rgb')
        self.track = None
        self.track_duration = None

    def authorize(self):
        """Handle the authorization workflow for the Spotify API
        """
        token = util.prompt_for_user_token(USERNAME,
                                           self.permission_scopes,
                                           SPOTIPY_CLIENT_ID,
                                           SPOTIPY_CLIENT_SECRET,
                                           SPOTIPY_REDIRECT_URI)
        if token:
            # Instantiate multiple Spotify objects, because sharing a Spotify object can block threads
            self.sp_gen = spotipy.Spotify(auth=token)
            self.sp_vis = spotipy.Spotify(auth=token)
            self.sp_sync = spotipy.Spotify(auth=token)
            self.sp_load = spotipy.Spotify(auth=token)
            self.sp_skip = spotipy.Spotify(auth=token)
            text = "Successfully connected to {}'s account.".format(self.sp_gen.me()["display_name"])
            print(SpotifyVisualizer._make_text_effect(text, ["green"]))
        else:
            raise Exception("Unable to authenticate Spotify user.")

    def get_track(self):
        """Fetches current track (waits for a track if necessary), starts it from beginning, and loads some track data.
        """
        text = "Waiting for an active Spotify track to start visualization."
        print(SpotifyVisualizer._make_text_effect(text, ["green", "bold"]))
        while not self.track:
            self.track = self.sp_gen.current_user_playing_track()
            time.sleep(0.5)
        track_name = self.track["item"]["name"]
        artists = ', '.join((artist["name"] for artist in self.track["item"]["artists"]))
        text = "Loaded track: {} by {}.".format(track_name, artists)
        print(SpotifyVisualizer._make_text_effect(text, ["green"]))
        self.track_duration = self.track["item"]["duration_ms"] / 1000
        self._reset_track()
        self._load_track_data()

    def sync(self):
        """Syncs visualizer with Spotify playback. Called asynchronously (worker thread).
        """
        track_progress = self.sp_sync.current_user_playing_track()["progress_ms"] / 1000
        text = "Syncing track to position: {}.".format(track_progress)
        print(SpotifyVisualizer._make_text_effect(text, ["green", "bold"]))
        self.pos_lock.acquire()
        self.playback_pos = track_progress
        self.pos_lock.release()

    def _continue_checking_if_skip(self, wait=0.33):
        """Continuously checks if the user's playing track has changed. Called asynchronously (worker thread).

        If the user's currently playing track has changed (is different from track), then this function pauses the user's
        playback and sets should_terminate to True, resulting in the termination of all worker threads.

        Args:
            wait (float): The amount of time in seconds to wait between each check.
        """
        track = self.sp_skip.current_user_playing_track()
        while track["item"]["id"] == self.track["item"]["id"]:
            time.sleep(wait)
            track = self.sp_skip.current_user_playing_track()
        self.sp_skip.pause_playback()
        self.should_terminate = True
        text = "A skip has occurred."
        print(SpotifyVisualizer._make_text_effect(text, ["blue", "bold"]))

    def _continue_loading_data(self, wait=0.5):
        """Continuously loads and prepares chunks of data. Called asynchronously (worker thread).

        Args:
            wait (float): The amount of time in seconds to wait between each call to _load_track_data().
        """
        while len(self.data_segments) != 0 and not self.should_terminate:
            self._load_track_data()
            time.sleep(wait)
        text = "Killing data loading thread. All data for current track has been loaded."
        print(SpotifyVisualizer._make_text_effect(text, ["red", "bold"]))
        exit(0)

    def _continue_syncing(self, wait=0.05):
        """Repeatedly syncs visualization playback position with the Spotify API.

        Args:
            wait (float): the amount of time in seconds to wait between each sync.
        """
        pos = self.playback_pos
        while round(self.track_duration - pos) != 0 and not self.should_terminate:
            self.sync()
            time.sleep(wait)
            pos = self.playback_pos
        text = "Killing synchronization thread."
        print(SpotifyVisualizer._make_text_effect(text, ["red", "bold"]))
        exit(0)

    def _get_buffers_for_pos(self, pos):
        """Find interpolated functions that have the specified position within their bounds via binary search.

        Args:
            pos (float): The playback position to find interpolated functions for.

        Returns:
             A 3-tuple of interp1d objects (interpolated loudness, pitch and timbre functions) or None if search fails.
        """
        self.buffer_lock.acquire()
        start, end, index, to_return = 0, len(self.interpolated_loudness_buffer) - 1, None, None
        while start <= end:
            mid = start + (end - start) // 2
            l_bound, u_bound, _ = self.interpolated_loudness_buffer[mid]
            if l_bound <= pos <= u_bound:
                index = mid
                break
            if pos < l_bound:
                end = mid-1
            elif pos > u_bound:
                start = mid+1
        if index is not None:
            to_return = (
                    self.interpolated_loudness_buffer[index][-1],
                    self.interpolated_pitch_buffer[index][-1],
                    self.interpolated_timbre_buffer[index][-1]
            )
        self.buffer_lock.release()
        return to_return

    def _load_track_data(self, chunk_length=12):
        """Obtain track data from the Spotify API and run necessary analysis to generate data needed for visualization.

        Each call to this function analyzes the next chunk_length seconds of track data and produces the appropriate
        interpolated loudness, pitch and timbre functions. These interpolated functions are added to their
        corresponding buffers.

        Args:
            chunk_length (float): the number of seconds of track data to analyze.
        """
        # Get track audio data for current song from Spotipy API if necessary
        if not self.data_segments:
            analysis = self.sp_load.audio_analysis(self.track["item"]["id"])
            self.data_segments.append({"start": -0.1, "loudness_start": -25.0, "pitches": 12*[0], "timbre": 12*[0]})
            self.data_segments += analysis["segments"]
            self.data_segments.append({"start": self.track_duration+0.01, "loudness_start": -25.0, "pitches": 12*[0], "timbre": 12*[0]})

        # Extract useful data for the next chunk_length seconds of playback
        s_t, l, pitch_lists, timbre_lists = [], [], [], []
        i = 0
        chunk_start = self.data_segments[0]["start"]
        while i < len(self.data_segments):
            s_t.append(self.data_segments[i]["start"])
            l.append(self.data_segments[i]["loudness_start"])
            pitch_lists.append(self.data_segments[i]["pitches"])
            timbre_lists.append(self.data_segments[i]["timbre"])
            # If we've analyzed chunk_length seconds of data, and there is more than 2 segments remaining, break
            if self.data_segments[i]["start"] > chunk_start + chunk_length and i < len(self.data_segments) - 1:
                break
            i += 1
        chunk_end = self.data_segments[i]["start"] if i < len(self.data_segments) else self.data_segments[-1]["start"]
        # Discard data segments that were just analyzed
        self.data_segments = self.data_segments[i:]

        # Perform data interpolation
        start_times = np.array(s_t)
        loudnesses = np.array(l)
        interpolated_loudness_func = interp1d(start_times, loudnesses, kind='cubic', assume_sorted=True)
        interpolated_pitch_funcs, interpolated_timbre_funcs = [], []
        for i in range(12):
            # Create a separate interpolated pitch function for each of the 12 elements of the pitch vectors
            interpolated_pitch_funcs.append(
                interp1d(
                    start_times,
                    [pitch_list[i] if pitch_list[i] >= 0 else 0 for pitch_list in pitch_lists],
                    kind="cubic",
                    assume_sorted=True
                )
            )
            # Create a separate interpolated timbre function for each of the 12 elements of the timbre vectors
            interpolated_timbre_funcs.append(
                interp1d(
                    start_times,
                    [timbre_list[i] for timbre_list in timbre_lists],
                    assume_sorted=True
                )
            )

        # Add interpolated functions and their bounds to buffers for consumption by visualizer thread
        self.buffer_lock.acquire()
        self.interpolated_loudness_buffer.append((chunk_start, chunk_end, interpolated_loudness_func))
        self.interpolated_pitch_buffer.append((chunk_start, chunk_end, interpolated_pitch_funcs))
        self.interpolated_timbre_buffer.append((chunk_start, chunk_end, interpolated_timbre_funcs))

        # Print information about the data chunk load that was just performed
        title = "--------------------DATA LOAD REPORT--------------------\n"
        data_seg_report = "Data segments remaining: {}.\n".format(len(self.data_segments))
        loudness_report = "Interpolated loudness buffer size: {}.\n".format(len(self.interpolated_loudness_buffer))
        pitch_report = "Interpolated pitch buffer size: {}.\n".format(len(self.interpolated_pitch_buffer))
        timbre_report = "Interpolated timbre buffer size: {}.\n".format(len(self.interpolated_timbre_buffer))
        closer = "--------------------------------------------------------"
        text = title + data_seg_report + loudness_report + pitch_report + timbre_report + closer
        print(SpotifyVisualizer._make_text_effect(text, ["blue"]))
        self.buffer_lock.release()

    @staticmethod
    def _normalize_loudness(loudness, range_max=-4.0, range_min=-54.0):
        """Normalize a loudness value to the range specified.

        Note that the range provided is normalized using a non-linearity function; this tends to provide a more
        appealing visualization.

        Args:
            loudness (float): the loudness value to normalize.
            range_max (float): the upper bound of the range.
            range_min (float): the lower bound of the range.

        Returns:
            The normalized loudness value (float between 0.0 and 1.0) for the specified range.
        """
        if loudness > range_max:
            range_max = loudness
        if loudness < range_min:
            range_min = loudness
        range_size = range_max - range_min
        linear_normalized = (loudness - range_min) / range_size
        return SpotifyVisualizer._non_linearity_function(linear_normalized)
        #return linear_normalized

    @staticmethod
    def _non_linearity_function(value):
        """A non-linearity function to apply to normalized pitch and loudness values

        This non-linearity function helps create more appealing visualizations when applied to normalized pitch and
        loudness values.

        Args:
            value (float): a normalized (between 0.0 and 1.0) pitch or loudness value.

        :return: the value after applying non-linearity (float between 0.0 and 1.0).
        """
        return 1.4 + np.tanh((2*value) - 2.424)

    def _push_visual_to_strip(self, loudness_func, pitch_funcs, timbre_funcs, pos):
        """Displays a visual on LED strip based on the loudness, pitches and timbre at current playback position.

        Args:
            loudness_func (interp1d): Interpolated loudness function.
            pitch_funcs (list): A list of interpolated pitch functions (one pitch function for each major musical key).
            timbre_funcs (list): A list of interpolated timbre functions (one timbre function for each basis function).
        """
        norm_loudness = SpotifyVisualizer._normalize_loudness(loudness_func(pos))
        print("%f: %f" % (pos, norm_loudness))
        length = int(self.num_pixels * norm_loudness)

        # Determine how many pixels to light (growing from center of strip) based on loudness
        mid = self.num_pixels//2
        lower = mid - round(length/2)
        upper = mid + round(length/2)
        self.strip.fill(lower, mid, 0, 0, 255, 100)
        self.strip.fill(mid, upper, 0, 0, 255, 100)

        # Segment strip into 12 zones (1 zone for each of the 12 pitch keys) and determine zone color by pitch strength
        for i in range(8, 12):
            pitch_val = SpotifyVisualizer._non_linearity_function(pitch_funcs[i](pos))# pitch_funcs[i](pos)
            r, g, b = int(self.red_grad_func(pitch_val)), int(self.green_grad_func(pitch_val)), int(self.blue_grad_func(pitch_val))
            if i in range(6):
                start = lower+(i*length//12)
                end = lower+((i+1)*length//12)
            else:
                start = upper - ((11 - i + 1) * length // 12)
                end = upper - ((11 - i) * length // 12)
            self.strip.fill(start, end, r, g, b, 100)

        # Make sure to clear ends of the strip that are not in use and update strip
        self.strip.fill(0, lower, 0, 0, 0, 0)
        self.strip.fill(upper, self.num_pixels, 0, 0, 0, 0)
        self.strip.show()

    @staticmethod
    def _make_text_effect(text, text_effects):
        """"Applies text effects to text and returns it.

        Args:
            text (str): The text to apply effects to.
            text_effects (list): A list of str, each str representing an effect to apply to the text.

        Returns:
            Text (str) with effects applied.
        """
        effects = {
            "green": "\033[92m",
            "red": "\033[91m",
            "blue": "\033[94m",
            "bold": "\033[1m"
        }
        end_code = "\033[0m"
        msg_with_fx = ""
        for effect in text_effects:
            msg_with_fx += effects[effect]
        msg_with_fx += text
        for _ in range(len(text_effects)):
            msg_with_fx += end_code
        return msg_with_fx

    def _reset(self):
        """Reset certain attributes to prepare to visualize a new track.
        """
        self.should_terminate = False
        self.strip.fill(0, self.num_pixels, 0, 0, 0, 0)
        self.strip.show()
        self.track = None
        self.track_id = None
        self.track_duration = None
        self.playback_pos = 0
        self.data_segments = []
        self.interpolated_loudness_buffer = []
        self.interpolated_pitch_buffer = []
        self.interpolated_timbre_buffer = []

    def _reset_track(self):
        """Pauses track and seeks to beginning.
        """
        text = "Starting track from beginning."
        print(SpotifyVisualizer._make_text_effect(text, ["green"]))
        if self.sp_gen.current_playback()["is_playing"]:
            self.sp_gen.pause_playback()
        self.sp_gen.seek_track(0)

    def _visualize(self, sample_rate=0.03):
        """Starts playback on Spotify user's account (if paused) and visualizes the current track.

        Args:
            sample_rate (float): how long to wait (in seconds) between each sample.
        """
        self.buffer_lock.acquire()
        loudness_func = self.interpolated_loudness_buffer[0][-1]
        pitch_funcs = self.interpolated_pitch_buffer[0][-1]
        timbre_funcs = self.interpolated_timbre_buffer[0][-1]
        self.buffer_lock.release()

        if not self.sp_vis.current_playback()["is_playing"]:
            self.sp_vis.start_playback()
        pos = self.playback_pos
        self._push_visual_to_strip(loudness_func, pitch_funcs, timbre_funcs, pos)
        # Visualize until end of track
        pos = self.playback_pos
        while pos <= self.track_duration:
            start = time.perf_counter()
            if self.should_terminate:
                text = "Killing visualization thread."
                print(SpotifyVisualizer._make_text_effect(text, ["red", "bold"]))
                exit(0)
            try:
                pos = self.playback_pos
                self._push_visual_to_strip(loudness_func, pitch_funcs, timbre_funcs, pos)
            # If pitch or loudness value out of range, find the interpolated functions for the current position
            except:
                funcs = self._get_buffers_for_pos(pos)
                if funcs:
                    loudness_func, pitch_funcs, timbre_funcs = funcs
                else:
                    text = "Killing visualization thread."
                    print(SpotifyVisualizer._make_text_effect(text, ["red", "bold"]))
                    exit(0)
            self.pos_lock.acquire()
            self.playback_pos += sample_rate
            self.pos_lock.release()
            end = time.perf_counter()
            # Account for time used to create visualization
            diff = sample_rate - (end - start)
            time.sleep(diff if diff > 0 else 0)

    def visualize(self):
        """Coordinate visualization by spawning the appropriate threads.

        There are 4 threads: one for visualization, one for periodically syncing the playback position with the Spotify
        API, one for loading chunks of track data, and one to periodically check if the user's current track has
        changed.
        """
        self.authorize()
        while True:
            self._reset()
            self.get_track()

            # Start threads and wait for them to exit
            threads = []
            threads.append(threading.Thread(target=self._visualize))
            threads.append(threading.Thread(target=self._continue_loading_data))
            threads.append(threading.Thread(target=self._continue_syncing))
            threads.append(threading.Thread(target=self._continue_checking_if_skip))
            for thread in threads:
                thread.start()
            text = "Started visualization."
            print(SpotifyVisualizer._make_text_effect(text, ["green"]))
            for thread in threads:
                thread.join()
            text = "Visualization finished."
            print(SpotifyVisualizer._make_text_effect(text, ["green"]))


if __name__ == "__main__":
    # Instantiate an instance of SpotifyVisualizer and start visualization
    visualizer = SpotifyVisualizer(240)
    visualizer.visualize()
