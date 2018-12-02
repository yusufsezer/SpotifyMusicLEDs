# !/usr/bin/env python3
import time
import subprocess
import spotipy
import threading
import spotipy.util as util
import numpy as np
from credentials import USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
from scipy.interpolate import interp1d
import apa102

class SpotifyVisualizer:
    """
    A class that allows for multithreaded music visualization via the Spotify API and an LED Strip
    """

    def __init__(self):
        self.sp = None
        self.playback_pos = 0
        self.track_loaded = False
        self.track = None
        self.track_duration = None
        self.interpolated_loudness_func = None
        self.interpolated_pitch_funcs = None
        self.numpixels = 240
        self.strip = apa102.APA102(num_led=240, global_brightness=20, mosi = 10, sclk = 11, order='rbg')
        self.interpolated_loudness_buffer = []
        self.interpolated_pitch_buffer = []
        self.data_segments = None
        self.light_segments = {i:(20*i, 20*(i+1)-1) for i in range(12)}
        self.segment_colors = {
            0: (0xBF, 0x00, 0x5E),
            1: (0xC2, 0x00, 0xC1),
            2: (0x64, 0x00, 0xC5),
            3: (0x10, 0x00, 0xC9),
            4: (0x00, 0x65, 0xCC),
            5: (0x00, 0xCF, 0xD0),
            6: (0x00, 0xD3, 0x6A),
            7: (0x00, 0xD7, 0x00),
            8: (0x6C, 0xDA, 0x00),
            9: (0xDD, 0xDE, 0x00),
            10: (0xE1, 0x70, 0x00),
            11: (0xE5, 0x00, 0x00)
        }
        self.pos_lock = threading.Lock()
        self.buffer_lock = threading.Lock()

    def authorize(self, scope="user-modify-playback-state"):
        """
        Handle the authorization workflow for the Spotipy API

        :param scope: the scope of access over the user's account to request
        :return: None
        """
        token = util.prompt_for_user_token(USERNAME,
                                           scope,
                                           SPOTIPY_CLIENT_ID,
                                           SPOTIPY_CLIENT_SECRET,
                                           SPOTIPY_REDIRECT_URI)
        if token:
            self.sp = spotipy.Spotify(auth=token)
        else:
            raise Exception("Unable to authenticate Spotify user.")

    def get_track(self):
        """
        Fetches current track (waits for a track if necessary), restarts it from beginning, and loads some track data

        :return: None
        """
        print("Waiting for an active Spotify track.")
        self.track = self.sp.current_user_playing_track()
        while not self.track:
            self.track = self.sp.current_user_playing_track()
            time.sleep(1)
        print("Loaded Track %s" % self.track)
        self._reset_track()
        self._load_track_data()

    def sync(self):
        """
        Syncs visualizer with Spotify playback
        Called asynchronously (worker Thread) as to not block visualization

        :return: None
        """
        track_progress = self.sp.current_user_playing_track()["progress_ms"] / 1000
        print("Syncing track to position: %f" % track_progress)
        self.pos_lock.acquire()
        self.playback_pos = track_progress
        self.pos_lock.release()

    def _continue_loading_data(self, wait=1):
        """
        Loads and prepares the next 7 seconds of song data for visualization
        Called asynchronously (worker thread)

        :param wait: the amount of time in seconds to wait between each call to self._load_track_data()
        :return: None
        """
        while len(self.data_segments) > 0:
            self.buffer_lock.acquire()
            self._load_track_data()
            self.buffer_lock.release()
            time.sleep(wait)

    def _continue_syncing(self, wait=.1):
        """
        Repeatedly syncs visualizer with the playing Spotify track

        :param wait: the amount of time in seconds to wait between each sync
        :return: None
        """
        while len(self.data_segments) > 0:
            self.sync()
            time.sleep(wait)

    def _load_track_data(self):
        """
        Obtain track audio data from Spotipy API and run necessary analysis to generate data needed for visualization
        Each call to this function analyzes the next ~7 seconds of song data

        :return: None
        """
        # Get track audio data for current song from Spotipy API if necessary
        if not self.data_segments:
            analysis = self.sp.audio_analysis(self.track["item"]["id"])
            self.data_segments = analysis["segments"]
            self.track_duration = self.track["item"]["duration_ms"] / 1000

        # Extract useful data for the next 7 seconds of playback
        s_t, l, pitch_lists = [], [], [] # segment start times, loudnesss, pitches
        i = 0
        while True:
            s_t.append(self.data_segments[i]["start"])
            l.append(self.data_segments[i]["loudness_start"])
            pitch_lists.append(self.data_segments[i]["pitches"])
            i += 1
            if i > len(self.data_segments) - 1 or round(self.data_segments[i]["start"]) == round(
                            self.data_segments[0]["start"] + 7):
                self.data_segments = self.data_segments[i - 1:]  # remove the analyzed data from self.data_segments
                break
        start_times = np.array(s_t)
        loudnesses = np.array(l)

        # Perform data interpolation
        try:
            interpolated_loudness_func = interp1d(start_times, loudnesses)
            interpolated_pitch_funcs = []
            for w in range(12):
                interpolated_pitch_funcs.append(
                    interp1d(start_times, [pitch_list[w] if pitch_list[w] >= 0 else 0 for pitch_list in pitch_lists]))
            # Add interpolated functions to buffers to be used when needed
            self.interpolated_loudness_buffer.append(interpolated_loudness_func)
            self.interpolated_pitch_buffer.append(interpolated_pitch_funcs)
        except:
            self.buffer_lock.release()
            print("Finished loading")

    def _reset_track(self):
        """
        Pauses track and seeks to beginning

        :return: None
        """
        print("Starting track from beginning")
        if self.sp.current_playback()["is_playing"]:
            self.sp.pause_playback()
        self.sp.seek_track(0)

    def _visualize(self, sample_rate=0.03):
        """
        Starts playback on Spotify user's account (if necessary) and visualizes the current track

        :param sample_rate: how frequently to sample song data and update visualization
        :return: None
        """
        self.buffer_lock.acquire()
        loudness = self.interpolated_loudness_buffer.pop(0)
        pitches = self.interpolated_pitch_buffer.pop(0)
        self.buffer_lock.release()
        self.strip.fill(0, 240, 0, 0, 0, 0)
        self.strip.show()

        if not self.sp.current_playback()["is_playing"]:
            self.sp.start_playback()

        # Visualize until end of track
        self.pos_lock.acquire()
        pos = self.playback_pos
        self.pos_lock.release()
        while pos <= self.track_duration:
            start = time.clock()
            try:
                self.pos_lock.acquire()
                pos = self.playback_pos
                self.pos_lock.release()
                l = loudness(pos)
                print("%f: %f" % (pos, l))
                vol_range_min = 4
                vol_range = 50
                normalized = (abs(l) - vol_range_min) / vol_range
                length = int(240 * (1 - normalized))
                self.strip.fill(length, 240, 0, 0, 0, 0)
                self.strip.fill(0, length, 0, 240, 0, 100)
                for key in self. light_segments:
                    s, e = self.light_segments[key]
                    r, g, b = self.segment_colors[key]
                    self.strip.fill(s, e, r, g, b, int(100 * pitches[w](pos)))
                self.strip.show()
            # If pitch value out of range, get data for next 7 seconds of song or terminate if song has ended
            except:
                self.buffer_lock.acquire()
                if len(self.interpolated_pitch_buffer) > 0:
                    pitches = self.interpolated_pitch_buffer.pop(0)
                    loudness = self.interpolated_loudness_buffer.pop(0)
                    self.buffer_lock.release()
                else:
                    print("Song Visualization Finished.")
                    self.buffer_lock.release()
                    break
            self.pos_lock.acquire()
            self.playback_pos += sample_rate
            self.pos_lock.release()
            end = time.clock()
            # Account for time used to create visualization
            diff = sample_rate - (end - start)
            time.sleep(diff if diff > 0 else 0)

    def visualize(self):
        """
        Coordinate visualization by spawning multiple threads to handle syncing, data loading, and visualization tasks

        :return: None
        """
        self.authorize()
        self.get_track()
        threads = []
        threads.append(threading.Thread(target=self._visualize))
        threads.append(threading.Thread(target=self._continue_loading_data))
        threads.append(threading.Thread(target=self._continue_syncing))
        for thread in threads:
            thread.start()
        print("Started visualization")
        for thread in threads:
            thread.join()
        print("Visualization finished")


if __name__ == "__main__":
    # Instantiate an instance of SpotifyVisualizer and visualize the currently playing track
    print("Initializing Spotify Visualizer")
    visualizer = SpotifyVisualizer()
    visualizer.visualize()