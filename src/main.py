import sys
import os
import re
import time
import socket
import tempfile
from scipy.io import wavfile
from threading import Thread
from playsound import playsound
from PyQt5 import QtWidgets, QtGui, QtCore
import pandas as pd
import numpy as np
import windows

class FullscreenImage(QtWidgets.QMainWindow):
    '''
    Fullscreen image widget catching press events
    '''
    def __init__(self, img_path, parent=None, pause_screen=False):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint) 
        self.press_id = None
        self.press_type = None
        self.reaction_time = None
        self.pause_flag = pause_screen
        self.qimg = QtGui.QImage(img_path)
        self.showFullScreen()

    def keyPressEvent(self, event):
        SPACE = 32
        if event.key() and not self.press_id and int(event.key()) != SPACE:
            self.reaction_time = time.time()
            self.press_id = int(event.key())
            self.press_type = "keyboard"
        elif event.key() and int(event.key()) == SPACE:
            self.pause_flag = not self.pause_flag
            if self.pause_flag:
                pause_msg = windows.Message("PAUSE", "Current experiment will be paused after this iteration")
                pause_msg.show()

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
                   labels, stim_times, outer_delay_ceil, ip, port, test):
        self.image_path_list = image_path_list
        self.audio_path_list = audio_path_list
        self.delays_list = delays_list
        self.labels = labels
        self.stim_times = stim_times
        self.outer_delay_ceil = outer_delay_ceil
        self.ip = ip
        self.port = port
        self.test_flag = test

    def pause(self):
        window = FullscreenImage(
            os.path.join(".", "data", "images", "pause.png"),
            pause_screen=True
        )
        while window.pause_flag:
            pass

    def terminate(self, result=None):
        self.progress.emit(result)
        self.finished.emit()

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
            # first stimul

            # cut file
            try:
                fs, s = wavfile.read(audio_path[0])
                s = s[:int(fs * self.stim_times[0] / 1000)]
                filename = os.path.join(os.path.dirname(audio_path[0]), next(tempfile._get_candidate_names()) + '.wav')
                wavfile.write(filename, fs, s)
            except:
                error = window.Message("ERRROR!", f"Unable to create temporary .wav (file {audio_path[0]} probably doesn't exist)! " +
                                                   "This experiment will be terminated...")
                error.show()
                self.terminate()
                return

            window = FullscreenImage(img_path[0])
            play = Thread(target=playsound, args=(filename,))
            play.start()
            play.join()
            os.remove(filename)  # remove temporary file
            time.sleep(self.delays_list[0] / 1000)
            if window.pause_flag:
                self.pause()

            # second stimul

            # cut file
            try:
                fs, s = wavfile.read(audio_path[1])
                s = s[:int(fs * self.stim_times[1] / 1000)]
                filename = os.path.join(os.path.dirname(audio_path[1]), next(tempfile._get_candidate_names()) + '.wav')
                wavfile.write(filename, fs, s)
            except:
                error = window.Message("ERRROR!", f"Unable to create temporary .wav (file {audio_path[1]} probably doesn't exist)! " +
                                                   "This experiment will be terminated...")
                error.show()
                self.terminate()
                return

            iteration_start = time.time()
            window = FullscreenImage(img_path[1])
            play = Thread(target=playsound, args=(filename,))
            play.start()
            play.join()
            os.remove(filename)  # remove temporary file
            time.sleep(self.delays_list[1] / 1000)
            time.sleep(np.random.randint(low=0, high=self.outer_delay_ceil) / 1000)

            delta = (window.reaction_time - iteration_start) if window.reaction_time else None

            buttons.append(window.press_id)
            times.append(delta * 1000 if delta else None)
            if window.pause_flag:
                self.pause()

            # history["press_id"].append(window.press_id)
            # history["press_type"].append(window.press_type)
            # history["reaction_time"].append(delta * 1000 if delta else None)  # in ms

            # client.send(str(label).encode('utf-8'))

        # client.close()
        result = pd.read_csv(os.path.join(".", "cfg", "experiment.csv"))
        if not self.test_flag:
            result['response'] = buttons
            result['response_time'] = times

        self.terminate(result)


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
        res_dir = os.path.join(".", "results")
        if not os.path.isdir(res_dir):
            os.mkdir(res_dir)

        filename = f"{self.user_info['username']}_{self.user_info['parameter']}_{self.user_info['another_parameter']}.csv"
        x.to_csv(os.path.join(res_dir, filename), index=False)
        print(self.history)

    def build_thread(self, image_path_list, audio_path_list, delays_list,
                     labels, stim_times, outer_delay_ceil, ip, port, test=False):
        '''
        Builds thread where main experiment loop will be executed (including performing stimula)
        '''
        self.thread = QtCore.QThread()
        self.worker = Worker()
        self.worker.set_params(image_path_list, audio_path_list, delays_list,
                               labels, stim_times, outer_delay_ceil, ip, port, test)
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
        try:
            config = pd.read_csv(os.path.join(".", "cfg", "config.csv"))
            experiment = pd.read_csv(os.path.join(".", "cfg", "experiment.csv"))
        except:
            error = windows.Message("ERROR!", "Unable to read config or experiment file(s)!")
            error.show()
            return

        image_path_list = [[os.path.join(".", "data", "images", "test1.bmp")] * 2]
        audio_path_list = [[os.path.join(".", "data", "audios", "test1.wav")] * 2]
        delays_list = [config.inner_delay[0], config.outer_delay[0]]

        try:
            self.build_thread(image_path_list, audio_path_list,
                delays_list, experiment[['label1', 'label2']].to_numpy(),
                config[['first_stim', 'second_stim']].to_numpy().ravel(),
                config['outer_delay_ceil'][0],
                ip=config.ip[0], port=config.port[0], test=True
            )
        except:
            error = windows.Message("ERROR!", "Unable to build thread task (passed data is probably incorrect)!")
            error.show()
            return

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
        try:
            config = pd.read_csv(os.path.join(".", "cfg", "config.csv"))
            experiment = pd.read_csv(os.path.join(".", "cfg", "experiment.csv"))
        except:
            error = windows.Message("ERROR!", "Unable to read config or experiment file(s)!")
            error.show()
            return

        images_dir = os.path.join(".", "data", "images")
        audios_dir = os.path.join(".", "data", "audios")

        experiment['image1'] = images_dir + os.sep + experiment['image1']
        experiment['image2'] = images_dir + os.sep + experiment['image2']

        experiment['audio1'] = audios_dir + os.sep + experiment['audio1']
        experiment['audio2'] = audios_dir + os.sep + experiment['audio2']

        delays_list = [config.inner_delay[0], config.outer_delay[0]]

        try:
            self.build_thread(
                experiment[['image1', 'image2']].to_numpy(), 
                experiment[['audio1', 'audio2']].to_numpy(), 
                delays_list, experiment[['label1', 'label2']].to_numpy(),
                config[['first_stim', 'second_stim']].to_numpy().ravel(),
                config['outer_delay_ceil'][0],
                ip=config.ip[0], port=config.port[0]
            )
        except:
            error = windows.Message("ERROR!", "Unable to build thread task (passed data is probably incorrect)!")
            error.show()
            return

        self.thread.start()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    app.exec_()

#if not imported
if __name__ == '__main__':
    main()
