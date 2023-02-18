import sys
import os
import re
import time
import socket
from threading import Thread
from playsound import playsound
from PyQt5 import QtWidgets, QtGui, QtCore
import pandas as pd
import windows

class FullscreenImage(QtWidgets.QMainWindow):
    '''
    Fullscreen image widget catching press events
    '''
    def __init__(self, img_path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint) 
        self.press_id = None
        self.press_type = None
        self.reaction_time = None
        self.qimg = QtGui.QImage(img_path)
        self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() and not self.press_id:
            self.reaction_time = time.time()
            self.press_id = int(event.key())
            self.press_type = "keyboard"

    def mousePressEvent(self, event):
        if event.button() and not self.press_id:
            self.reaction_time = time.time()
            self.press_id = int(event.button())
            self.press_type = "mouse"

    def paintEvent(self, qpaint_event):
        painter = QtGui.QPainter(self)
        self.rect = qpaint_event.rect()
        painter.drawImage(self.rect, self.qimg)

class Worker(QtCore.QObject):
    '''
    Worker for running target task in a separate thread
    '''
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(pd.DataFrame)

    def set_params(self, image_path_list, audio_path_list, delays_list,
                   labels, ip, port):
        self.image_path_list = image_path_list
        self.audio_path_list = audio_path_list
        self.delays_list = delays_list
        self.labels = labels
        self.ip = ip
        self.port = port

    def run(self):
        '''
        Shows images and plays audios in a loop with some delays after each iteration.
        All the data about user events will be passed to the main thread in a dictionary.
        '''
        # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client.connect((self.ip, self.port))

        '''
        history = {
            "press_id": [],
            "press_type": [],
            "reaction_time": []
        }
        '''
        buttons, times = [], []
        for img_path, audio_path, labels in zip(self.image_path_list, self.audio_path_list,
                                               self.labels):
            window = FullscreenImage(img_path[0])
            play = Thread(target=playsound, args=(audio_path[0],))
            play.start()
            play.join()
            time.sleep(self.delays_list[0] / 1000)

            iteration_start = time.time()
            window = FullscreenImage(img_path[1])
            play = Thread(target=playsound, args=(audio_path[1],))
            play.start()
            play.join()
            time.sleep(self.delays_list[1] / 1000)

            delta = (window.reaction_time - iteration_start) if window.reaction_time else None

            buttons.append(window.press_id)
            times.append(delta * 1000 if delta else None)

            # history["press_id"].append(window.press_id)
            # history["press_type"].append(window.press_type)
            # history["reaction_time"].append(delta * 1000 if delta else None)  # in ms

            # client.send(str(label).encode('utf-8'))

        # client.close()
        result = pd.read_csv(os.path.join(".", "cfg", "experiment.csv"))
        result['response'] = buttons
        result['response_time'] = times

        self.progress.emit(result)
        self.finished.emit()

class AppMainWindow(QtWidgets.QMainWindow, windows.Ui_MainWindow):
    '''
    Main application class
    '''
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.update_user_info()
        # self.clear_history()

        # draw instructions picture (top widget of the main window)
        scene = QtWidgets.QGraphicsScene()
        pixmap = QtGui.QPixmap(os.path.join(".", "data", "images", "instructions.jpg"))
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        self.instructions_graphics_viewer.setScene(scene)

        # buttons callbacks
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
    
    def clear_history(self):
        '''
        Sets history dictionary values to default values
        '''
        '''
        self.history = {
            "press_id": None,       # pressed keys/buttons history
            "press_type": None,     # types of events (mouse/keyboard)
            "reaction_time": None   # reaction time history (in seconds)
        }
        '''
        pass

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

    def set_buttons_state(self, state):
        '''
        Enables or disables buttons of the main window
        '''
        self.button_1.setEnabled(state)
        self.button_2.setEnabled(state)
    
    def set_history(self, x):
        '''
        Experiment history setter
        '''
        self.history = x
        filename = f"{self.user_info['username']}_{self.user_info['parameter']}_{self.user_info['another_parameter']}.csv"
        x.to_csv(os.path.join(".", "data", filename), index=False)
        print(self.history)

    def build_thread(self, image_path_list, audio_path_list, delays_list, labels, ip, port):
        '''
        Builds thread where main experiment loop will be executed (including performing stimula)
        '''
        self.thread = QtCore.QThread()
        self.worker = Worker()
        self.worker.set_params(image_path_list, audio_path_list, delays_list,
                               labels, ip, port)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.started.connect(lambda: self.set_buttons_state(False))
        self.worker.progress.connect(lambda x: self.set_history(x))
        self.thread.finished.connect(lambda: self.set_buttons_state(True))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # self.thread.finished.connect(lambda: print("Finished a thread!"))

    def test(self):
        '''
        This function is called whenever 'Test' button is pressed.
        Creates a thread which shows one test image and plays an audio with zero delay after stimulus.
        '''
        image_path_list = [os.path.join(".", "data", "images", "test1.bmp")]
        audio_path_list = [os.path.join(".", "data", "audios", "test1.wav")]
        delays_list = [0]
        self.build_thread(image_path_list, audio_path_list, delays_list)
        self.thread.start()
        # self.clear_history()

    def start_experiment(self):
        '''
        This function is called whenever 'Start' button is pressed.
        Creates a thread which shows images and plays audios in a loop with some delays after each iteration.
        '''
        # user's inputs dictionary stuff
        self.update_user_info()
        if not self.user_info_is_correct():
            return
        else:
            self.hide() # hide main application window

        # This data will be read from some files.
        config = pd.read_csv(os.path.join(".", "cfg", "config.csv"))
        experiment = pd.read_csv(os.path.join(".", "cfg", "experiment.csv"))

        images_dir = os.path.join(".", "data", "images")
        audios_dir = os.path.join(".", "data", "audios")

        experiment['image1'] = images_dir + os.sep + experiment['image1']
        experiment['image2'] = images_dir + os.sep + experiment['image2']

        experiment['audio1'] = audios_dir + os.sep + experiment['audio1']
        experiment['audio2'] = audios_dir + os.sep + experiment['audio2']

        delays_list = [config.inner_delay[0], config.outer_delay[0]]

        self.build_thread(
            experiment[['image1', 'image2']].to_numpy(), 
            experiment[['audio1', 'audio2']].to_numpy(), 
            delays_list, experiment[['label1', 'label2']].to_numpy(),
            ip=config.ip[0], port=config.port[0]
        )
        self.thread.start()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    app.exec_()

#if not imported
if __name__ == '__main__':
    main()
