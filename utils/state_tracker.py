from enum import Enum
from utils.print_utils import Logger


class VisualizerStates(Enum):
    AUTH = 0
    DATA_LOAD = 1
    LOAD_AND_VISUALIZE = 2
    VISUALIZE = 3
    TERMINATE = 4


class VisualizerStateTracker():

    def __init__(self):
        self.logger = Logger()
        self.state = None

    def set_state(self, new_state):
        if self.state != new_state:
            report(new_state)
        self.state = new_state

    def get_state(self):
        return self.state

    def report(self):
        if self.state == VisualizerState.AUTH:
            self.logger.log("Authenticating with spotify...")
        elif self.state == VisualizerState.DATA_LOAD:
            self.logger.log("Beginning to load song data...")
        elif self.state == VisualizerState.LOAD_AND_VISUALIZE:
            self.logger.success("Data loading sufficient, starting visualization...")
        elif self.state == VisualizerState.VISUALIZE:
            self.logger.success("Finished loading song.")
        elif self.state == VisualizerState.TERMINATE:
            self.logger.warn("Termination request recieved. Preparing to terminate all threads...")

    # Will return true unless we've decided to terminate.
    def __bool__(self):
        return self.state == VisualizerStates.TERMINATE
