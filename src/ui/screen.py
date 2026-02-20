#LBIRARRIES
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextBrowser, QLineEdit, QPushButton, QTabWidget, 
    QLabel, QFormLayout, QSpinBox, QComboBox
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont, QTextCursor

#TODO UI UZERINE UGRASILCAK FINAL HALI DEGIL 
class Screen(QMainWindow):
    textCommand = Signal(str)    # Kullanıcı bir sey yazarsa
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yerel Desktop Asistani")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        
        self.isListening = False

        self.setupUI()
        self.applyStyles()

    def setupUI(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout(self.centralWidget)

        self.tabs = QTabWidget()
        self.mainLayout.addWidget(self.tabs)

        self.chat = QWidget()
        self.setupCHAT()
        self.tabs.addTab(self.chat, "Sohbet")

        self.log = QWidget()
        self.setupLOG()
        self.tabs.addTab(self.log, "System Logs")

        self.settings = QWidget()
        self.setupSETTINGS()
        self.tabs.addTab(self.settings, "Ayarlar")

    def setupCHAT(self):
        layout = QVBoxLayout(self.chat)

        self.chatDisp = QTextBrowser()
        self.chatDisp.setOpenExternalLinks(True)
        layout.addWidget(self.chatDisp)

        inputLayout = QHBoxLayout()
        
        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("Bir komut yazın")
        self.inputField.returnPressed.connect(self.sendButton)
        
        self.sendBTN = QPushButton("Gönder")
        self.sendBTN.setCursor(Qt.PointingHandCursor)
        self.sendBTN.clicked.connect(self.sendButton)

        inputLayout.addWidget(self.inputField)
        inputLayout.addWidget(self.sendBTN)

        layout.addLayout(inputLayout)

    def setupLOG(self):
        layout = QVBoxLayout(self.log)
    
        self.logDisp = QTextBrowser()
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.logDisp.setFont(font)
        
        layout.addWidget(self.logDisp)
        
        self.clearLogBTN = QPushButton("Loglari Temizle")
        self.clearLogBTN.clicked.connect(self.logDisp.clear)
        layout.addWidget(self.clearLogBTN)

    def setupSETTINGS(self):
        layout = QFormLayout(self.settings)
        
        self.comboModel = QComboBox()
        self.comboModel.addItems(["DEFAULT LLM"])
        
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 60)
        self.timeout.setValue(10)
        self.timeout.setSuffix(" sn")

        layout.addRow(QLabel("LLM Modeli:"), self.comboModel)
        layout.addRow(QLabel("Timeout:"), self.timeout)

    def sendButton(self):
        text = self.inputField.text().strip()
        if text:
            self.apendChat("Sen", text, color="#2980b9")
            self.textCommand.emit(text)
            self.inputField.clear()
            

    @Slot(str, str, str)
    def apendChat(self, sender: str, message: str, color: str = "#2c3e50"):
        html = f'<b><font color="{color}">{sender}:</font></b> {message}'
        self.chatDisp.append(html)
        
        cursor = self.chatDisp.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chatDisp.setTextCursor(cursor)

    @Slot(str)
    def appendLOG(self, log_message: str):
        self.logDisp.append(log_message)
        
        cursor = self.logDisp.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.logDisp.setTextCursor(cursor)

    def applyStyles(self): #TODO STILLERI TASIMAYI UNUTMA KODLARI DUZENLE
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #bdc3c7;
            }
            QTabWidget::pane {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #dcdde1;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
                font-weight: bold;
            }
        """)