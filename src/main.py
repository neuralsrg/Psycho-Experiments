import sys
import os
import re
import time
import cv2
import screeninfo
from playsound import playsound
from PyQt5 import QtWidgets, QtGui
import pandas as pd

import windows


class AppMainWindow(QtWidgets.QMainWindow, windows.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.update_user_info()

        self.fullscreen_window_name = "projector" # name for cv2 window
        self.cv2_building_delay = 0.025 # delay between building a window and first image displaying
                                        # if it is too small, first image will not be displayed (black screen bug, not enough time to load something)
                                        # if it is too large, it will become very noticeable (black screen before first image)

        # set instructions picture (top widget on the main window)
        scene = QtWidgets.QGraphicsScene()
        pixmap = QtGui.QPixmap("./images/instructions.jpg")
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        self.instructions_graphics_viewer.setScene(scene)

        # left and right buttons callbacks
        self.button_1.clicked.connect(self.start_experiment)
        self.button_2.clicked.connect(self.test)

    def update_user_info(self):
        '''
        Reads user inputs (line edits) and update dictionary
        '''
        self.user_info = {
            "username": self.text_input_1.text().strip().replace(' ', '_'),
            "parameter": self.text_input_2.text().strip().replace(' ', '_'),
            "another_parameter": self.text_input_3.text().strip().replace(' ', '_')
        }

    def user_info_is_correct(self):
        '''
        Check if all the inputs (line edits) were filled in with correct strings
        '''
        if not all(self.user_info.values()):
            error = windows.Message("ERROR!", "Passed data shouldn't include any empty fields!")
            error.show()
            return False
        elif not all([re.match(r'^[A-Za-z0-9_]+$', s.strip().replace(' ', '_')) for s in self.user_info.values()]):
            error = windows.Message("ERROR!", "Passed fields can include nothing but letters, numbers, spaces and the '_' symbol!")
            error.show()
            return False
        else:
            return True

    def build_cv2_fullscreen(self):
        '''
        Build screen before experiment session (loop)
        '''
        SCREEN_ID = 0
        screen = screeninfo.get_monitors()[SCREEN_ID]
        # width, height = screen.width, screen.height
        cv2.namedWindow(self.fullscreen_window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.moveWindow(self.fullscreen_window_name, screen.x - 1, screen.y - 1)
        cv2.setWindowProperty(self.fullscreen_window_name, cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN)
        time.sleep(self.cv2_building_delay) # check init for more info

    def img_audio_pair(self, img_filename: str, audio_filename: str, delay: float):
        '''
        Performs one stimulus (a pair of image and audio), then waits for <delay> seconds

        img_filename: image path
        audio_filename: audio path
        delay: delay after stimulus in seconds
        '''
        cv2img = cv2.imread(img_filename, cv2.IMREAD_COLOR)
        cv2.imshow(self.fullscreen_window_name, cv2img)
        cv2.waitKey(1) # 1ms delay => sleep should be a bit less => delay = delay - 1ms
        playsound(audio_filename)
        time.sleep(delay)

    def test(self):
        '''
        This function is called whenever 'Test' button is pressed.
        Shows one test image and plays one test audio with zero delay after stimulus.
        '''
        self.hide()
        self.build_cv2_fullscreen()
        self.img_audio_pair(
            os.path.join(".", "images", "test1.bmp"),
            os.path.join(".", "audios", "test1.wav"),
            0
        )
        cv2.destroyAllWindows()
        self.show()

    def start_experiment(self):
        '''
        This function is called whenever 'Start' button is pressed.
        Builds fullscreen, then shows images and plays audios in a loop with some delays after each iteration.
        '''
        # user's inputs dictionary stuff
        self.update_user_info()
        if not self.user_info_is_correct():
            return
        else:
            self.hide() # hide main application window

        #self.hide() # hide main application window

        # This data will be read from some files. Feel free to change it.
        pairs_data = pd.read_csv('./cfg/pairs.csv')
        cfg_data = pd.read_csv('./cfg/config.csv')

        # image_paths = ["./images/test1.bmp", "./images/test2.jpeg", "./images/test3.png"]
        # audio_paths = ["./audios/test1.wav", "./audios/test2.mp3", "./audios/test3.ogg"]

        image_paths = pairs_data['image'].values
        audio_paths = pairs_data['sound'].values

        # delays = [1, 1, 1]
        # delays = [(elem - 0.001) for elem in delays] # we'll use 1 ms delay from cv2.waitKey(1)
        inner_delay, outer_delay = cfg_data['inner_delay'], cfg_data['outer_delay']

        self.build_cv2_fullscreen()
        for img_filename, audio_filename in zip(image_paths, audio_paths): # main experiment loop
            self.img_audio_pair(img_filename, audio_filename, inner_delay)
            self.img_audio_pair(img_filename, audio_filename, outer_delay)

        cv2.destroyAllWindows()
        msg = windows.Message("SUCCESS!", f"Thank you for participating, {self.user_info['username']}!")
        msg.show()
        self.show()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    app.exec_()

#if not imported
if __name__ == '__main__':
    main()
