import numpy as np
import win32gui, win32ui, win32con
from threading import Thread, Lock, Event


class WindowCapturer:
    """
    Class for capturing a window's screenshot and retrieving screen position.
    """

    BORDER_PIXELS = 8
    """
    int: The number of border pixels to exclude from the captured window.
    """

    TITLEBAR_PIXELS = 30
    """
    int: The number of title pixels to exclude from the captured window.
    """

    def __init__(self, window_name: str):
        """
        Initialize the WindowCapturer instance.

        :param window_name: The partial name of the window to capture.
                            It can even be a full name, but because the Terraria window name changes every time,
                            it's recommended to use the immutable part of it.
        :type: str

        :raises Exception: If the window isn't found.
        """

        # creating a lock object for thread
        self._lock = Lock()
        self._stop_event = Event()

        self.screenshot = None

        self.hwnd = self.__get_hwnd_by_partial_name(window_name)
        if not self.hwnd:
            raise Exception('Window is not found: {}'.format(window_name))

        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.width = window_rect[2] - window_rect[0]
        self.height = window_rect[3] - window_rect[1]

        # window width and height with cutting borders and a title
        self.width -= (self.BORDER_PIXELS * 2)
        self.height = self.height - self.TITLEBAR_PIXELS - self.BORDER_PIXELS
        self.cropped_x = self.BORDER_PIXELS
        self.cropped_y = self.TITLEBAR_PIXELS

        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

    # Declaring thread methods
    def start(self):
        """
        Start the capturing thread.
        """

        thread = Thread(target=self.__run)
        thread.start()

    def stop(self):
        """
        Stop the capturing thread.
        """

        self._stop_event.set()

    def __run(self):
        """
        Main capturing loop.
        """

        while not self._stop_event.is_set():
            screenshot = self.__get_screenshot()

            self._lock.acquire()
            self.screenshot = screenshot
            self._lock.release()

    def get_screen_position(self, position):
        """
        Translate a pixel position on a screenshot image to a pixel position on the screen.

        WARNING: if you move the window being captured after execution is started, this will
        return incorrect coordinates, because the window position is only calculated in
        the __init__ constructor.

        :param position: The pixel position on the screenshot image (x, y).
        :type position: tuple

        :return: The translated pixel position on the screen (x, y).
        :rtype: tuple
        """

        return position[0] + self.offset_x, position[1] + self.offset_y

    def __get_screenshot(self):
        """
        Capture the window's screenshot.

        :return: The captured screenshot as a NumPy array.
        :rtype: numpy.ndarray
        """

        # get the window data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        data_bit_map = win32ui.CreateBitmap()
        data_bit_map.CreateCompatibleBitmap(dcObj, self.width, self.height)
        cDC.SelectObject(data_bit_map)
        cDC.BitBlt((0, 0), (self.width, self.height), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # data_bit_map.SaveBitmapFile(cDC, 'debug.bmp')
        signed_ints_array = data_bit_map.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype='uint8')
        img.shape = (self.height, self.width, 4)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(data_bit_map.GetHandle())

        # drop the alpha channel to cv.matchTemplate() not throw an error
        # maybe it will be deleted later
        img = img[..., :3]

        img = np.ascontiguousarray(img)

        return img

    @staticmethod
    def __get_hwnd_by_partial_name(partial_name):
        """
        Get the window handle by its partial name.

        :param partial_name (str): The partial name of the window.

        :return: int: The window handle (HWND) if found, None otherwise.
        """

        hwnds = []

        def callback(hwnd, hwnd_list):
            if partial_name.lower() in win32gui.GetWindowText(hwnd).lower():
                hwnd_list.append(hwnd)
            return True

        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None
