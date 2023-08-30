import cv2 as cv

from vision import Vision
from windowcapturer import WindowCapturer
from time import time

if __name__ == '__main__':
    window_name = "Terraria:"
    vision = Vision()
    capturer = WindowCapturer(window_name)

    vision.start()
    capturer.start()

    loop_time = time()
    while True:
        if capturer.screenshot is None:
            continue

        vision.update(capturer.screenshot)

        if vision.detected_image is None:
            print('stuck here')
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

        cv.imshow('Debug window', vision.detected_image)

        if cv.waitKey(1) == ord('q'):
            cv.destroyAllWindows()
            capturer.stop()
            vision.stop()
            break

    print('Done')
