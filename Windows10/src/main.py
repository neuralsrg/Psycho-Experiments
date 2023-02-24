import sys
import os
import re
import time
import socket
import tempfile
import glob
from threading import Thread

import pandas as pd
import numpy as np
from scipy.io import wavfile
from playsound import playsound
import tkinter
from PIL import Image, ImageTk
from PyQt5 import QtWidgets, QtGui
import serial

import windows

class FullScreenImage:
    def __init__(self):
        self.response_time = None
        self.key = None
        self.button_pressed = False

    def handler(self, e):
        self.button_pressed = True
        self.response_time = (time.time() - self.response_time) * 1000
        self.key = e.char

    def showPIL(self, pilImage, t):
        root = tkinter.Tk()
        pause_var = tkinter.StringVar()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.overrideredirect(1)
        root.geometry("%dx%d+0+0" % (w, h))
        root.focus_set()    
        canvas = tkinter.Canvas(root,width=w,height=h)
        canvas.pack()
        canvas.configure(background='black')
        imgWidth, imgHeight = pilImage.size
        if imgWidth > w or imgHeight > h:
            ratio = min(w/imgWidth, h/imgHeight)
            imgWidth = int(imgWidth*ratio)
            imgHeight = int(imgHeight*ratio)
            pilImage = pilImage.resize((imgWidth,imgHeight), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(pilImage)
        imagesprite = canvas.create_image(w/2,h/2,image=image)
        root.bind("<KeyPress>", self.handler)
        root.after(t, lambda: root.destroy())
        self.response_time = time.time()
        root.mainloop()
        if not self.button_pressed:
            self.response_time = None


class AppMainWindow(QtWidgets.QMainWindow, windows.Ui_MainWindow):
    '''
    Main application class
    '''
    def __init__(self, config_path, client, ser):
        super().__init__()
        self.setupUi(self)
        self.update_user_info()

        self.write_history = True
        self.config_path = config_path
        self.client = client
        self.ser = ser
        self.response_time = None
        self.last_pressed_key = None

        # draw instructions picture (top widget of the main window)
        scene = QtWidgets.QGraphicsScene()
        pixmap = QtGui.QPixmap(os.path.join(".", "data", "images", "instructions.png"))
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

    def img_audio_pair(self, image, audio, t, second_flag):
        '''
        Shows a pair of image and audio as a stimulus
        '''
        image_screen = FullScreenImage()
        pilImage = Image.open(image)
        play = Thread(target=playsound, args=(audio,))
        show = Thread(target=image_screen.showPIL, args=(pilImage, t))
        play.start()
        show.start()
        play.join()
        show.join()
        self.response_time = image_screen.response_time
        self.last_pressed_key = image_screen.key

    def test(self):
        '''
        This function is called whenever 'Test' button is pressed.
        Creates a thread which shows one test image and plays an audio with zero delay after stimulus.
        '''
        self.write_history = False
        try:
            # config = pd.read_csv(os.path.join(".", "cfg", "config.csv"))
            experiment = pd.read_csv(self.config_path)
        except:
            error = windows.Message("ERROR!", "Unable to read config or experiment file(s)!")
            error.show()
            return

        image_path_list = [[os.path.join(".", "data", "images", "test1.bmp")] * 2]
        audio_path_list = [[os.path.join(".", "data", "audios", "test1.wav")] * 2]
        delays_list = [experiment.inner_delay[0], experiment.outer_delay[0]]

        for img_path, audio_path, label in zip(image_path_list, audio_path_list, delays_list):
            for i, stim_t in zip([0, 1], [experiment.first_stim, experiment.second_stim]):
                fs, s = wavfile.read(audio_path[i])
                s = s[:int(fs * stim_t[0] / 1000)]
                filename = os.path.join(os.path.dirname(audio_path[i]), next(tempfile._get_candidate_names()) + '.wav')
                wavfile.write(filename, fs, s)
                self.img_audio_pair(img_path[i], filename, int(stim_t[0]), False)
                os.remove(filename)
                time.sleep(delays_list[i] / 1000)

    def start_experiment(self):
        '''
        This function is called whenever 'Start' button is pressed.
        Creates a thread which shows images and plays audios in a loop with some delays after each iteration.
        '''
        def send_message(message):
            if message:
                self.ser.rts = True
                self.client.send(bytes(str(message),"utf-8") + bytes("\n","utf-8"))
                self.ser.rts = False

        self.write_history = True
        # user's inputs dictionary stuff
        self.update_user_info()
        if not self.user_info_is_correct():
            return

        # This data will be read from some files.
        try:
            # config = pd.read_csv(os.path.join(".", "cfg", "config.csv"))
            experiment = pd.read_csv(self.config_path)
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

        outer_delay_ceil = experiment['outer_delay_ceil'][0]
        labels = experiment[['label1', 'label2']].to_numpy()

        images_dir = experiment[['image1', 'image2']].to_numpy()
        audios_dir = experiment[['audio1', 'audio2']].to_numpy()

        delays_list = [experiment.inner_delay[0], experiment.outer_delay[0]]

        buttons, times = [], []
        for img_path, audio_path, label in zip(images_dir, audios_dir, labels):
            for i, stim_t in zip([0, 1], [experiment.first_stim[0], experiment.second_stim[0]]):
                fs, s = wavfile.read(audio_path[i])
                s = s[:int(fs * stim_t / 1000)]
                filename = os.path.join(os.path.dirname(audio_path[i]), next(tempfile._get_candidate_names()) + '.wav')
                wavfile.write(filename, fs, s)
                try:
                    sender = Thread(target=send_message, args=(label[i],))
                    sender.start()
                except:
                    pass
                self.img_audio_pair(img_path[i], filename, int(stim_t), bool(i))
                os.remove(filename)
                time.sleep(delays_list[i] / 1000)
            time.sleep(np.random.randint(low=0, high=outer_delay_ceil) / 1000)
            buttons.append(self.last_pressed_key)
            times.append(self.response_time)

        result = pd.read_csv(self.config_path)
        result['response'] = buttons
        result['response_time'] = times

        res_dir = os.path.join(".", "results")
        if not os.path.isdir(res_dir):
            os.mkdir(res_dir)

        filename = f"{self.user_info['username']}_{self.user_info['parameter']}_{self.user_info['another_parameter']}.csv"
        x = pd.DataFrame(result)
        cols = x.columns.to_list()
        cols = cols[:6] + cols[-2:] + cols[6: 11]
        x = x[cols]
        self.history = x
        x.to_csv(os.path.join(res_dir, filename), index=False)
        print(self.history)

        self.destroy()
        self.app.quit()
        

def main(config_file, client, ser):
    app = QtWidgets.QApplication(sys.argv)
    window = AppMainWindow(config_path=config_file, client=client, ser=ser)
    window.app = app
    window.show()
    app.exec_()

#if not imported
if __name__ == '__main__':
    socket_data = pd.read_csv(os.path.join(".", "src", "socket_config.csv"))
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ser = serial.Serial('COM3', 19200, timeout=1)
    ser.rts, ser.dtr = False, False
    try:
        client.connect((socket_data.ip[0], socket_data.port[0]))
    except:
        pass

    cfg_dir = os.path.join(".", "cfg")  # config files directory
    for config_file in glob.glob(os.path.join(cfg_dir, "*.csv")):  # for all config files listed in cfg_dir
        main(config_file=config_file, client=client, ser=ser)
    
    try:
        client.close()
    except:
        pass
