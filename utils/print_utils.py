from difflib import SequenceMatcher
import time

class Logger:

    def __init__(self, file_name=None, suppress=False):
        self.file_name = None
        self.suppress = suppress


    # Method for displaying error messages
    def error(self, message):
        TYPE = "e"
        self._log_to_file(message, TYPE)
        if not suppress:
            print(f"\033[1m\033[91m{message}\033[0m\033[0m")

    # Method for general purpose logging messages
    def log(self, message):
        TYPE = "l"
        self._log_to_file(message, TYPE)
        if not suppress:
            print(f"\033[1m{message}\033[0m")

    # Method for success messages
    def success(self, message):
        TYPE = "s"
        self._log_to_file(message, TYPE)
        if not suppress:
            print(f"\033[1m\033[92m{message}\033[0m\033[0m")

    # Method for survivable errors and general warnings.
    def warn(self, message):
        TYPE = "w"
        self._log_to_file(message, TYPE)
        if not suppress:
            print(f"\033[1m\033[91m{message}\033[0m\033[0m")

    # Not used rn
    def _should_override(self, message, type):
        similarity = SequenceMatcher(None, message, self.previous_message[1]).ratio()
        if similarity > 0.070 and type == self.previous_message[0]:
            return "\r"
        return "\n"

    def _log_to_file(self, message, type):
        if self.file_name is not None:
            with open(self.file_name, "a+") as f:
                f.write(f"{time.time()} - [{upper(type)}] {message}")



    # # ALIASES for easy use...
    #
    # e = error
    # l = log
    # s = success
    # w = warn


if __name__ == "__main__":
    logger = Logger()
    logger.error("This is an example error message!")
    logger.success("This is an example success message!")
    logger.success("This is another example success message!")
