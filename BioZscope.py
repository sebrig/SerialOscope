import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from QScope import QScope
import numpy as np
import sys
from time import sleep
from SerialHandler import SerialHandler
from CSVwritter import CSVwritter
from collections import deque
from multiprocessing import Queue
from SerialParser import SerialParser, ParserColumnHandler

uart = SerialHandler("COM3", 921600)
parser = SerialParser( uart, 1000 )

def calcAmplitude( p_re, p_im ):
    return np.sqrt( pre**2 + p_im**2 )

def calcPhase( p_re, p_im ):
    return np.rad2deg( np.arctan( p_im/p_re ) )

if __name__=="__main__":
    parser.setColumnID(0, "I")
    parser.setColumnID(1, "Q")

    I = ParserColumnHandler( parser, 0 )
    Q = ParserColumnHandler( parser, 1 )

    uart.startReadingProcess()

    app = QApplication(sys.argv)

    window1 = QMainWindow()
    widget1 = QScope( parser, [I, Q] )
    window1.setCentralWidget(widget1)
    window1.setWindowTitle("Oscilloscope 1")
    window1.resize(1200, 600)
    window1.show()

    widget1.start()

    try:
        sys.exit(app.exec())
    finally:
        uart.stopReadingProcess()
        widget1.stop()