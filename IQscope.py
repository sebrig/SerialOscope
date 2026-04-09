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

uart = SerialHandler( "COM3", 921600 )
parser = SerialParser( uart, 1000 )


if __name__ == '__main__':
    uart = SerialHandler("COM3", 921600)
    parser = SerialParser(uart, 1000)

    parser.setColumnID(0, "Ishunt")
    parser.setColumnID(1, "Qshunt")
    parser.setColumnID(2, "Ibioz")
    parser.setColumnID(3, "Qbioz")

    Qshunt = ParserColumnHandler(parser, 0)
    Ishunt = ParserColumnHandler(parser, 1)
    Qbioz = ParserColumnHandler(parser, 2)
    Ibioz = ParserColumnHandler(parser, 3)

    uart.startReadingProcess()

    app = QApplication(sys.argv)

    # Timer global pour parser + calculer
    parse_timer = QTimer()
    parse_timer.timeout.connect(parser.parseNewValues)
    parse_timer.start(50)

    window1 = QMainWindow()
    widget1 = QScope([
        ("Ishunt", Ishunt.getQueue()),
        ("Qshunt", Qshunt.getQueue()),
    ])
    window1.setCentralWidget(widget1)
    window1.setWindowTitle("Oscilloscope 1")
    window1.resize(1200, 600)
    window1.show()

    window2 = QMainWindow()
    widget2 = QScope([
        ("Ibioz", Ibioz.getQueue()),
        ("Qbioz", Qbioz.getQueue()),
    ])
    window2.setCentralWidget(widget2)
    window2.setWindowTitle("Oscilloscope 2")
    window2.resize(1200, 600)
    window2.show()

    widget1.start()
    widget2.start()

    try:
        sys.exit(app.exec())
    finally:
        uart.stopReadingProcess()
        widget1.stop()
        widget2.stop()
