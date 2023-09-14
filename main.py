from multiprocessing import Queue
from time import time
import cv2 as cv

from vision import Vision
from windowcapturer import WindowCapturer

if __name__ == '__main__':
    DEBUG = True

    window_name = "Terraria:"
    frame_queue = Queue(maxsize=1)
    detected_queue = Queue(maxsize=1)

    vision = Vision(frame_queue, detected_queue)
    capturer = WindowCapturer(window_name, frame_queue)

    vision.start()
    capturer.start()

    loop_time = time()
    while True:
        if capturer.frame_queue.empty():
            continue

        # show loop fps is faster than model process a picture
        try:
            fps = 1 / (time() - loop_time)
        except ZeroDivisionError:
            fps = 0

        # cv.putText(vision.detected_image, "FPS: " + str(round(fps, 0)), (10, 50), cv.FONT_HERSHEY_SIMPLEX,
        #            1.5, (0, 255, 0))
        # print('FPS {}'.format(round(fps)))
        loop_time = time()

        if DEBUG:
            # display debug window
            cv.imshow('Debug window', vision.detected_queue.get())

        if cv.waitKey(1) == ord('q'):
            cv.destroyAllWindows()
            capturer.stop()
            vision.stop()
            break

    print('Done')
