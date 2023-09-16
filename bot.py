import time
from abc import ABC, abstractmethod
from multiprocessing import Process, Queue, Event

import cv2
import pyautogui


# Bot states
# 1 - Initializing
# 2 - Throwing a fishing rod
# 3 - Waiting for the fish to bite
# 4 - Catching a fish


class State(ABC):
    """
    Interface of the State pattern.
    """

    @property
    def bot(self) -> 'FisherBot':
        """
        Bot getter.
        :return: bot
        """

        return self._bot

    @bot.setter
    def bot(self, bot: 'FisherBot') -> None:
        """
        Bot setter.
        :param bot: The instance of a bot
        """

        self._bot = bot

    @abstractmethod
    def run(self):
        """
        Interface of state's main loop
        """

        ...


class InitializingState(State):
    """
    Initializing state of the bot. Wait till the model is ready to be used, then change to the Throwing state.
    """

    def run(self):
        if self.bot.tracker is None:
            self.bot.tracker = cv2.TrackerMIL_create()

        if not self.bot.is_model_ready_queue.empty():
            self.bot.set_state(ThrowingState())


class ThrowingState(State):
    """
    Throwing state of the bot. Click left button to throw a bobber and change to the Biting state.
    """

    def run(self):
        pyautogui.mouseDown()
        pyautogui.mouseUp()

        # To slow down the change between the states. Can be deleted if you want
        time.sleep(0.7)
        self.bot.set_state(BitingState())


class BitingState(State):
    """
    Biting state of the bot. Track fish biting the bobber and then change to the Catching state.
    """

    def run(self):
        for target in self.bot.detected_queue.get():
            x1, y1, x2, y2, _ = target
            mid_x, mid_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

            if not self.bot.is_tracker_initialized_event.is_set():
                w, h = x2 - x1, y2 - y1
                self.bot.tracker.init(self.bot.frame_queue.get(), (x1, y1, w, h))
                self.bot.is_tracker_initialized_event.set()
            else:
                success, _ = self.bot.tracker.update(self.bot.frame_queue.get())
                if success:

                    if (mid_x, mid_y) not in self.bot.coordinates:
                        self.bot.coordinates.append((mid_x, mid_y))

                    if len(self.bot.coordinates) > 1:
                        print(self.bot.coordinates)
                        prev_x, prev_y = self.bot.coordinates[-2]
                        diff_x, diff_y = abs(mid_x - prev_x), abs(mid_y - prev_y)

                        if diff_x <= 1 and diff_y <= 1 and not self.bot.is_bobber_stabilized:
                            self.bot.is_bobber_stabilized = True

                        if (diff_x > 2 or diff_y > 1) and (diff_x < 8 or diff_y < 8) and self.bot.is_bobber_stabilized:
                            print("Coordinate difference exceeds"
                                  f"\n diff_x {diff_x}"
                                  f"\n diff_y {diff_y}")

                            self.bot.coordinates.clear()
                            self.bot.is_bobber_stabilized = False

                            self.bot.set_state(CatchingState())


class CatchingState(State):
    """
    Catching state of the bot. Click left button to catch a fish and change to the Throwing state.
    """

    def run(self):
        pyautogui.mouseDown()
        pyautogui.mouseUp()

        # To slow down the change between the states. Can be deleted if you want
        time.sleep(0.7)
        self.bot.set_state(ThrowingState())


class FisherBot:
    """
    Class for catching fish in Terraria.
    """

    _state = None
    """
    State: property of current state 
    """

    MIN_CONFIDENT_THRESHOLD = 0.2
    """
    float: The value of minimum threshold when detected object is being considered
    """

    def __init__(self, frame_queue: Queue, detected_queue: Queue, is_ready_queue: Queue):
        """
        Initialize the FisherBot instance.

        :param: frame_queue: The queue for the process to store frames
        :type: Queue

        :param: detected_queue: The queue for the process to store image (in the future coordinates) with the detected
                               bobber
        :type: Queue

        :param: is_ready_queue: The queue for the process to inform the bot when the model is ready to be used
        :type: Queue
        """

        # process properties
        self._process = None
        self._stop_event = Event()
        self.frame_queue = frame_queue
        self.detected_queue = detected_queue
        self.is_model_ready_queue = is_ready_queue

        # tracker properties
        self.tracker = None
        self.is_tracker_initialized_event = Event()
        self.coordinates = []
        self.is_bobber_stabilized = False

        self.set_state(InitializingState())

    def set_state(self, state: State):
        """
        Set one of the four states: Initializing, Throwing, Biting, Catching

        :param state: An instance of the State pattern's implementations.
        """

        print(f"Bot: Transitioning to {type(state).__name__}")

        self._state = state
        self._state.bot = self

    # process methods
    def start(self):
        """
        Start the bot process
        """

        self._process = Process(target=self._run)
        self._process.start()

    def stop(self):
        """
        Stop the bot process
        """

        self._stop_event.set()
        self._process.terminate()

    def _run(self):
        """
        Main bot loop
        """

        while not self._stop_event.is_set():
            self._state.run()
