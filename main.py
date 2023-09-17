import logging
from multiprocessing import Queue

import cv2 as cv
import keyboard

from bot import FisherBot
from vision import Vision
from windowcapturer import WindowCapturer


def draw_visualization(image, coordinates):
    """
    Draw a bounding box on detected object.

    :param: image: The captured screenshot
    :type: numpy.ndarray

    :param: coordinates: The list of tuples which stores detected bobbers coordinates and confidence in format (x1,
                         y1, x2, y2, conf)
    :type: list

    :return: The captured screenshot with visualization
    :rtype: numpy.ndarray
    """

    for coord in coordinates:
        x1, y1, x2, y2, conf = coord
        mid_x, mid_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

        # Bounding box visualization
        cv.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)

        # For the text background
        # Finds space required by the text so that we can put a background with that amount of width.
        # (w, h), _ = cv2.getTextSize(
        #     f'{conf}', cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1)
        # cv2.rectangle(image, (x1 - 5, y1 - h), (x1 + w, y1), (255, 0, 0), -1)

        # Prints the text
        cv.putText(image, f'{conf}',
                   (max(0, (x1 - 5)), max(35, (y1 - 5))), cv.FONT_HERSHEY_SIMPLEX, 0.4, (36, 255, 12), 1)

        # Draw a marker in the center of the bounding box
        cv.drawMarker(image, (mid_x, mid_y), (0, 0, 255), markerType=cv.MARKER_DIAMOND,
                      markerSize=4)

        cv.putText(image, f'Center X: {mid_x}', (100, 220), cv.FONT_HERSHEY_SIMPLEX, 0.8,
                   (0, 255, 0),
                   2)
        cv.putText(image, f'Center Y: {mid_y}', (100, 250), cv.FONT_HERSHEY_SIMPLEX, 0.8,
                   (0, 255, 0),
                   2)

        # cv.putText(vision.detected_image, "FPS: " + str(round(fps, 0)), (10, 50), cv.FONT_HERSHEY_SIMPLEX,
        #            1.5, (0, 255, 0))

    return image


if __name__ == '__main__':
    DEBUG = True

    if DEBUG:
        format_text = "%(asctime)s %(name)s %(levelname)s %(message)s"
    else:
        format_text = "%(asctime)s %(message)s"

    logging.basicConfig(level=logging.INFO, format=format_text, datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('To pause the bot press CTRL + ALT\n To exit press ALT + Q')

    window_name = "Terraria:"
    frame_queue = Queue(maxsize=1)
    detected_queue = Queue(maxsize=2)

    # kludgy way to detect when the model is ready
    is_ready_queue = Queue(maxsize=1)

    vision = Vision(frame_queue, detected_queue, is_ready_queue)
    capturer = WindowCapturer(window_name, frame_queue)
    bot = FisherBot(frame_queue, detected_queue, is_ready_queue)

    vision.start()
    capturer.start()
    bot.start()

    # loop_time = time()
    while True:
        if frame_queue.empty():
            continue

        # show loop fps is faster than model process a picture
        # try:
        #     fps = 1 / (time() - loop_time)
        # except ZeroDivisionError:
        #     fps = 0
        # print('FPS {}'.format(round(fps)))
        # loop_time = time()

        if DEBUG:
            # display debug window
            cv.imshow('Debug window', draw_visualization(frame_queue.get(), detected_queue.get()))

        if keyboard.is_pressed("alt+q"):
            cv.destroyAllWindows()
            capturer.stop()
            vision.stop()
            bot.stop()
            logging.info('Goodbye, that was a great fishing.')
            exit(0)

        cv.waitKey(1)
