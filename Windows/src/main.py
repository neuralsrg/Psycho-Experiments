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
from PyQt5 import QtWidgets, QtGui, QtCore
import serial

import windows


class BlackScreen(QtWidgets.QMainWindow):
    '''
    Background black screen widget to hide Desktop
    '''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint) 
        self.qimg = QtGui.QImage(os.path.join(".", "data", "inner", "black.png"))
        self.showFullScreen()

    def paintEvent(self, qpaint_event):
        painter = QtGui.QPainter(self)
        self.rect = qpaint_event.rect()
        painter.drawImage(self.rect, self.qimg)
    

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
        self.root = None
        self.can_press = False
        self.buttons = []
        self.times = []
        self.response_time = None
        self.key = None

        # draw instructions picture (top widget of the main window)
        scene = QtWidgets.QGraphicsScene()
        pixmap = QtGui.QPixmap(os.path.join(".", "data", "inner", "instructions.png"))
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        self.instructions_graphics_viewer.setScene(scene)

        # buttons callbacks
        self.button_1.clicked.connect(self.start_experiment)
        self.button_2.clicked.connect(self.next_experiment)

        #black screen (background)
        self.black_screen = BlackScreen()

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
        if not self.user_info["username"]:
            error = windows.Message("ERROR!", "Passed username can't be empty!")
            error.show()
            return False
        elif not all([(re.match(r'^[A-Za-z0-9_]+$', s.strip().replace(' ', '_')) or not s) for s in self.user_info.values()]):
            error = windows.Message("ERROR!", "Passed fields can include nothing but letters, numbers, spaces and the '_' symbol!")
            error.show()
            return False
        else:
            return True

    def handler(self, e):
        '''
        Handles Tkinter keypress events
        '''
        if self.can_press:
            self.can_press = False
            self.response_time = int((time.time() - self.start_time) * 1000)
            self.key = f"{e.keycode} ({e.keysym})"

    def build_visuals(self):
        '''
        Creates Tkinter visuals for experiment images
        '''
        self.root = tkinter.Tk()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.overrideredirect(1)
        self.root.config(cursor="none")
        self.root.geometry("%dx%d+1+1" % (w, h))
        self.root.bind("<KeyPress>", self.handler)

        self.canvas = tkinter.Canvas(self.root, width=w, height=h,
                                highlightthickness=0, highlightcolor='black')
        self.canvas.pack()
        self.canvas.configure(background='black')
        self.active_image = self.canvas.create_image(w/2, h/2, image=None)

    def deactivate(self):
        '''
        Stop handling keypress
        '''
        self.can_press = False

    def send_message(self, message):
        self.ser.rts = 1
        time.sleep(0.005)
        self.client.send(bytes("S:", "utf-8") + bytes(str(message), "utf-8") + bytes("\n", "utf-8"))
        self.ser.rts = 0

    def wait(self, data, i):
        '''
        Pause between stimula parts
        '''
        self.can_press = False
        if (i == 0):
            r = 0
            t = self.delays_list[0] + r
            self.root.after(int(t), self.stimulus, data, 1)
        else:
            r = np.random.randint(low=0, high=self.outer_delay_ceil)
            t = self.delays_list[1] + r
            self.root.after(int(t), self.img_audio_loop)

    def stimulus(self, data, i):
        '''
        Performs one pair of image and audio, saves responses
        '''
        if (i == 1):
            if self.key == "27 (Escape)":
                self.root.destroy()
                return
            self.buttons.append(self.key)
            self.times.append(self.response_time)
        img_path, audio_path, labels = data
        fs, s = wavfile.read(audio_path[i])
        s = s[:int(fs * self.stim_t_list[i] / 1000)]
        filename = os.path.join(".", "data", "temp", next(tempfile._get_candidate_names()) + '.wav')
        wavfile.write(filename, fs, s)

        pilImage = Image.open(img_path[i])

        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        imgWidth, imgHeight = pilImage.size
        if imgWidth > w or imgHeight > h:
            ratio = min(w/imgWidth, h/imgHeight)
            imgWidth = int(imgWidth*ratio)
            imgHeight = int(imgHeight*ratio)
            pilImage = pilImage.resize((imgWidth,imgHeight), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(pilImage)

        t = int(self.stim_t_list[i])
        self.root.after(int(t), self.wait, data, i)

        self.key = None
        self.response_time = None

        if labels[i]:
            sender = Thread(target=self.send_message, args=(labels[i],))
            sender.start()

        self.can_press = True
        self.start_time = time.time()
        self.canvas.delete("all")
        self.active_image = self.canvas.create_image(w/2, h/2, image=self.image)
        self.canvas.update()
        ps = Thread(target=playsound, args=(filename,))
        ps.start()

        self.root.after(int(self.stim_t_list[i]), self.deactivate)

    def img_audio_loop(self, first_run=False):
        '''
        Read data element then start performing next stimula pair
        '''
        if not first_run:
            if self.key == "27 (Escape)":
                self.root.destroy()
                return
            self.buttons.append(self.key)
            self.times.append(self.response_time)
        try:
            data = next(self.data_iter)
        except StopIteration:
            self.root.destroy()
            return

        self.root.after(0, self.stimulus, data, 0)

    def next_experiment(self):
        '''
        This function is called whenever 'Next experiment' button is pressed.
        Destroys this window for the next experiment.
        '''
        print(False)
        self.destroy()
        self.app.quit()

    def start_experiment(self):
        '''
        This function is called whenever 'Start' button is pressed.
        Creates a thread which shows images and plays audios in a loop with some delays after each iteration.
        '''
        self.buttons = []
        self.times = []

        # user's inputs dictionary stuff
        self.update_user_info()
        if not self.user_info_is_correct():
            return

        # This data will be read from some files.
        try:
            experiment = pd.read_csv(self.config_path)
        except:
            error = windows.Message("ERROR!", "Unable to read config or experiment file(s)!")
            error.show()
            return

        self.buttons = []
        self.times = []

        images_dir = os.path.join(".", "data", "images")
        audios_dir = os.path.join(".", "data", "audios")

        experiment['image1'] = images_dir + os.sep + experiment['image1']
        experiment['image2'] = images_dir + os.sep + experiment['image2']

        experiment['audio1'] = audios_dir + os.sep + experiment['audio1']
        experiment['audio2'] = audios_dir + os.sep + experiment['audio2']

        image_path_list = experiment[['image1', 'image2']].values.tolist()
        audio_path_list = experiment[['audio1', 'audio2']].values.tolist()
        labels_list = experiment[['label1', 'label2']].values.tolist()
        self.data_iter = iter(zip(image_path_list, audio_path_list, labels_list))

        self.stim_t_list = [experiment.first_stim[0], experiment.second_stim[0]]
        self.outer_delay_ceil = experiment['outer_delay_ceil'][0]
        self.delays_list = [experiment.inner_delay[0], experiment.outer_delay[0]]
        
        self.hide()
        self.build_visuals()
        self.root.after(10, self.img_audio_loop, True)
        self.root.mainloop()

        res = [(str(elem[0]) +  ',' + str(elem[1]) + '\n') for elem in zip(self.buttons, self.times)]
        filename = self.user_info['username']
        if self.user_info['parameter']:
            filename += '_' + self.user_info['parameter']
        if self.user_info['another_parameter']:
            filename += '_' + self.user_info['another_parameter']
        filename += ".csv"
        with open(os.path.join(".", "results", filename), 'w') as f:
            f.write("key,response_time" + '\n')
            for row in res:
                f.write(row)

        print(False)
        self.destroy()
        self.app.quit()

    def closeEvent(self, event):
        '''
        Handle quit
        '''
        print(True)
        self.black_screen.hide()

def checker(path):
    data = pd.read_csv(path)
    for objective in ["image1", "image2", "audio1", "audio2"]:
        files = os.listdir(os.path.join(".", "data", objective[:-1] + 's'))
        for needed in data[objective]:
            flag = False
            for f in files:
                if f == needed:
                    flag = True
                    break
            if not flag:
                raise FileNotFoundError(f"{objective} file {needed} not found")

def experiment(config_file, client, ser, path):
    checker(path)
    app = QtWidgets.QApplication(sys.argv)
    window = AppMainWindow(config_path=config_file, client=client, ser=ser)
    window.setWindowTitle(path)
    window.app = app
    window.show()
    app.exec_()

def main(path):
    socket_data = pd.read_csv(os.path.join(".", "src", "socket_config.csv"))
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ser = serial.Serial(
        port=socket_data.serial_port[0],
        baudrate=9600,
        bytesize=8,
        stopbits=1,
        timeout=None,
    )
    ser.rts = 0
    ser.dtr = 0
    client.connect((socket_data.ip[0], socket_data.port[0]))
    experiment(config_file=path, client=client, ser=ser, path=path)
    
    try:
        client.close()
    except:
        pass

path = sys.argv[1]
main(path)
