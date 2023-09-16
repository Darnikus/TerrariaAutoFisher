import math
from multiprocessing import Process, Queue, Event

from ultralytics import YOLO


class Vision:
    """
    Class for detecting bobber on a screenshot.
    """

    PATH_TO_MODEL = "bdV8n_openvino_model"
    """
    str: The path to model (quite obvious)
    """

    MIN_CONFIDENT_THRESHOLD = 0.2
    """
    float: The value of minimum threshold when detected object is being considered
    """

    def __init__(self, frame_queue: Queue, detected_queue: Queue, is_ready_queue: Queue):
        """
        Initialize the Vision instance.

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
        self._frame_queue = frame_queue
        self._detected_queue = detected_queue

        self._is_ready_queue = is_ready_queue
        self._is_ready = False

        self._model = YOLO(self.PATH_TO_MODEL, task='detect')

    # Declaring process methods
    def start(self):
        """
        Start the detecting process.
        """

        self._process = Process(target=self._run)
        self._process.start()

    def stop(self):
        """
        Stop the detecting process.
        """

        self._stop_event.set()
        self._process.terminate()

    def _run(self):
        """
        Main detecting loop.
        """

        while not self._stop_event.is_set():
            if not self._frame_queue.empty():
                detected_img = self.__detect_image()
                self._is_ready = True
                self._detected_queue.put(detected_img)

    def __detect_image(self) -> list:
        """
        Detect a bobber on the image.

        :return: The list of tuples which stores detected bobbers coordinates and confidence in format (x1, y1, x2,
                 y2, conf)
        :rtype: list
        """

        image = self._frame_queue.get()
        target = []

        # verbose False to hide prediction log
        results = self._model.predict(image, stream=True, verbose=False, conf=self.MIN_CONFIDENT_THRESHOLD)

        for r in results:
            for box in r.boxes:
                conf = math.ceil((box.conf[0]) * 100) / 100
                x1, y1, x2, y2 = [int(i) for i in box.xyxy[0]]
                target.append(
                    (x1, y1, x2, y2, conf)
                )

        if not self._is_ready:
            self._is_ready_queue.put(True)
        return target
