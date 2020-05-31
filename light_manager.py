import sys
import threading
import time

from Animations.LoadingAnimator import LoadingAnimator
from credentials import AWS_ACCESS_KEY, AWS_SECRET_KEY, USER
from dynamodb_client import DynamoDBClient
from spotify_visualizer import SpotifyVisualizer
from Visualizations.LoudnessLengthEdgeFadeVisualizer import LoudnessLengthEdgeFadeVisualizer

def _init_visualizer(dev_mode, n_pixels, base_color):
    if dev_mode:
        from virtual_visualizer import VirtualVisualizer
        visualization_device = VirtualVisualizer()
    else:
        from driver import apa102
        visualization_device = apa102.APA102(num_led=n_pixels, global_brightness=23, mosi=10, sclk=11, order='rgb')

    visualizer = LoudnessLengthEdgeFadeVisualizer(visualization_device, n_pixels, base_color)
    loading_animator = LoadingAnimator(visualization_device, n_pixels)
    return (visualizer, loading_animator)


def manage(dev_mode):
    """ Lifecycle manager for the program

    In order to restart the lights remotely if an update is required, this level
    of abstraction separates the lifecycle of the lights from the visualization
    logic itself.

    Args:
        dev_mode (boolean): a flag denoting if the program is being run on the
    pi or a developer's machine.

    """
    dynamoDBClient = DynamoDBClient()
    base_color = None # We always want to update the lights on first start.
    visualizer_thread = None
    n_pixels = 240
    visualizer = None
    spotify_visualizer = None

    while True:
        record = dynamoDBClient.get_record()

        settings = record['settings']['M']
        base_color_r = int(settings['baseColorRedValue']['N'])
        base_color_g = int(settings['baseColorGreenValue']['N'])
        base_color_b = int(settings['baseColorBlueValue']['N'])
        new_base_color = (base_color_r, base_color_g, base_color_b)
        if new_base_color != base_color:
            if visualizer:
                visualizer.set_primary_color(new_base_color)
            base_color = new_base_color

        if bool(record['shouldRestart']['BOOL']):
            if spotify_visualizer:
                spotify_visualizer.terminate_visualizer()
                while visualizer_thread.is_alive():
                    print("Waiting for visualizer to terminate...")
                    time.sleep(1)
            dynamoDBClient.update_restart_flag()

        # If the animation has not been instantiated or the thread has
        # completed (i.e. we killed it), we need to reinstantiate and restart.
        if not visualizer_thread or not visualizer_thread.is_alive():
            visualizer, loading_animator = _init_visualizer(developer_mode, n_pixels, base_color)
            spotify_visualizer = SpotifyVisualizer(visualizer, loading_animator)
            visualizer_thread = threading.Thread(target=spotify_visualizer.launch_visualizer, name="visualizer_thread")
            visualizer_thread.start()

        time.sleep(5)

if __name__ == "__main__":
    """ The outmost layer of the system.

    This is the entrypoint to the project and the outmost layer of the system.
    It is required because a GUI can only be run from the main thread, so any
    additional logic must be threadded to avoid blocking. The general structure
    now looks like this:

    - This script (Main thread)
        - manage() above
            - SpotifyVisualizer.launch_visualizer
                - data load
                - visualize
                - ...
    - GUI

    Args:
        developer_mode (boolean): determines if visualizer should be run from
    an actual lights strip or a virtual visualizer.
    """

    args = sys.argv
    if len(args) > 1:
        developer_mode = bool(args[1])
    else:
        developer_mode = False

    manager_thread = threading.Thread(target=manage, name="manager_thread", args=(developer_mode,))
    manager_thread.start()

    # If we are in developer mode, we need to use this main thread to start the
    # VirutalVisualizer GUI. Since VirtualVisualizer is a singleton class, we
    # can just reinstantiate the VirtualVisualizer
    if developer_mode:
        from virtual_visualizer import VirtualVisualizer
        VirtualVisualizer().start_visualization()
