from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(750, 400)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.baseLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.baseLayout.setObjectName("baseLayout")

        self.instructions_graphics_viewer = QtWidgets.QGraphicsView(self.centralwidget)
        self.instructions_graphics_viewer.setObjectName("instructions_graphics_viewer")
        self.baseLayout.addWidget(self.instructions_graphics_viewer)

        self.inputsLayout = QtWidgets.QHBoxLayout()
        self.inputsLayout.setObjectName("inputsLayout")

        self.inputLayout_1 = QtWidgets.QVBoxLayout()
        self.inputLayout_1.setObjectName("inputLayout_1")
        self.input_label_1 = QtWidgets.QLabel(self.centralwidget)
        self.input_label_1.setObjectName("input_label_1")
        self.inputLayout_1.addWidget(self.input_label_1)
        self.text_input_1 = QtWidgets.QLineEdit(self.centralwidget)
        self.text_input_1.setObjectName("text_input_1")
        self.inputLayout_1.addWidget(self.text_input_1)
        self.inputsLayout.addLayout(self.inputLayout_1)

        self.inputLayout_2 = QtWidgets.QVBoxLayout()
        self.inputLayout_2.setObjectName("inputLayout_2")
        self.input_label_2 = QtWidgets.QLabel(self.centralwidget)
        self.input_label_2.setObjectName("input_label_2")
        self.inputLayout_2.addWidget(self.input_label_2)
        self.text_input_2 = QtWidgets.QLineEdit(self.centralwidget, placeholderText="Optional field")
        self.text_input_2.setObjectName("text_input_2")
        self.inputLayout_2.addWidget(self.text_input_2)
        self.inputsLayout.addLayout(self.inputLayout_2)

        self.inputLayout_3 = QtWidgets.QVBoxLayout()
        self.inputLayout_3.setObjectName("inputLayout_3")
        self.input_label_3 = QtWidgets.QLabel(self.centralwidget)
        self.input_label_3.setObjectName("input_label_3")
        self.inputLayout_3.addWidget(self.input_label_3)
        self.text_input_3 = QtWidgets.QLineEdit(self.centralwidget, placeholderText="Optional field")
        self.text_input_3.setObjectName("text_input_3")
        self.inputLayout_3.addWidget(self.text_input_3)
        self.inputsLayout.addLayout(self.inputLayout_3)
        self.baseLayout.addLayout(self.inputsLayout)

        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName("buttonsLayout")
        self.button_1 = QtWidgets.QPushButton(self.centralwidget)
        self.button_1.setObjectName("button_1")
        self.buttonsLayout.addWidget(self.button_1)
        self.button_2 = QtWidgets.QPushButton(self.centralwidget)
        self.button_2.setObjectName("button_2")
        self.buttonsLayout.addWidget(self.button_2)
        self.baseLayout.addLayout(self.buttonsLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 634, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "PsychoApp"))
        self.input_label_1.setText(_translate("MainWindow", "Username"))
        self.input_label_2.setText(_translate("MainWindow", "Parameter"))
        self.input_label_3.setText(_translate("MainWindow", "Another parameter"))
        self.button_1.setText(_translate("MainWindow", "Start"))
        self.button_2.setText(_translate("MainWindow", "Next experiment"))

class Message:
    def __init__(self, msg1="ERROR!", msg2="ERROR!"):
        self.msg = QtWidgets.QMessageBox()
        self.msg.setIcon(QtWidgets.QMessageBox.Information)
        self.msg.setWindowTitle(msg1)
        self.msg.setText(msg2)
    
    def show(self):
        self.msg.exec_()
