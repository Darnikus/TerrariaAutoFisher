import cv2 as cv
from windowcapturer import WindowCapturer
from time import time

if __name__ == '__main__':
    window_name = "Terraria:"
    capturer = WindowCapturer(window_name)
    loop_time = time()

    capturer.start()

    while True:
        if capturer.screenshot is None:
            continue

        cv.imshow('123', capturer.screenshot)

        # show loop fps
        print('FPS {}'.format(1 / (time() - loop_time)))
        loop_time = time()

        if cv.waitKey(1) == ord('q'):
            cv.destroyAllWindows()
            capturer.stop()
            break

    print('Done')
