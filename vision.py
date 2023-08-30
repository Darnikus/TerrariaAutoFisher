import math
from threading import Thread, Lock, Event
import cv2
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

    def __init__(self):

        # creating a lock object for thread
        self._lock = Lock()
        self._stop_event = Event()

        self.screenshot = None

        # This will probably need to be changed to an array of detected bobbers in the future
        self.detected_image = None

        self.model = YOLO(self.PATH_TO_MODEL, task='detect')

    # Declaring thread methods
    def start(self):
        """
        Start the detecting thread.
        """

        thread = Thread(target=self.__run)
        thread.start()

    def stop(self):
        """
        Stop the detecting thread.
        """
        self._stop_event.set()

    def update(self, screenshot):
        """
        Update the screenshot while thread is running.

        :param screenshot: A screenshot of the window from WindowCapturer
        """

        self._lock.acquire()
        self.screenshot = screenshot
        self._lock.release()

    def __run(self):
        """
        Main detecting loop.
        """

        while not self._stop_event.is_set():
            if self.screenshot is not None:
                detected_img = self.__detect_image()

                self._lock.acquire()
                self.detected_image = detected_img
                self._lock.release()

    def __detect_image(self):
        """
        Detect a bobber on the image. If the bobber is found, bounding box will be visualized

        :return: The image with bounding box visualization of a bobber, if it's found
        """

        image = self.screenshot
        results = self.model.predict(self.screenshot, stream=True)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                conf = math.ceil((box.conf[0]) * 100) / 100
                if conf >= self.MIN_CONFIDENT_THRESHOLD:
                    # Bounding box visualization
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)

                    # For the text background
                    # Finds space required by the text so that we can put a background with that amount of width.
                    # (w, h), _ = cv2.getTextSize(
                    #     f'{conf}', cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1)
                    # cv2.rectangle(image, (x1 - 5, y1 - h), (x1 + w, y1), (255, 0, 0), -1)

                    # Prints the text
                    cv2.putText(image, f'{conf}',
                                (max(0, (x1 - 5)), max(35, (y1 - 5))), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (36, 255, 12), 1)

        return image
