import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
import numpy as np
import sys
from time import sleep
from SerialHandler import SerialHandler
from CSVwritter import CSVwritter
from collections import deque
from multiprocessing import Queue
from SerialParser import SerialParser, ParserColumnHandler

class QScope(QWidget):
    __COLORS = ['blue', 'red', 'green', 'yellow', 'cyan', 'magenta', 'white', 'orange']

    def __init__(self, p_channels : list[tuple[str, deque]] ):
        """
        p_parser  : SerialParser
        p_channels : liste de tuples (nom, deque) ex: [("shunt1", ma_deque), ...]
        """
        super(QScope, self).__init__(None)

        self.__channels : list[tuple[str, deque]] = p_channels

        # --- Layout ---
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- PyQtGraph ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('black')
        self.plot_widget.setTitle("UART temps réel")
        self.plot_widget.setLabel('left', 'Valeur')
        self.plot_widget.setLabel('bottom', 'Échantillons')
        self.plot_widget.addLegend()

        self.__curves = []
        for i, (name, _) in enumerate(self.__channels):
            color = QScope.__COLORS[i % len(QScope.__COLORS)]
            curve = self.plot_widget.plot(
                pen=pg.mkPen(color=color, width=2),
                name=name
            )
            self.__curves.append(curve)

        layout.addWidget(self.plot_widget)

        # --- Timer de rafraîchissement ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

    def update_plot(self):
        for i, (_, data) in enumerate(self.__channels):
            self.__curves[i].setData(data)

    def start(self):
        self.timer.start(50)

    def stop(self):
        self.timer.stop()

    def __del__(self):
        self.stop()


if __name__ == '__main__':
    uart = SerialHandler("COM3", 921600)
    parser = SerialParser(uart, 1000)

    parser.setColumnID(0, "shunt1")
    parser.setColumnID(1, "shunt2")
    parser.setColumnID(2, "shunt3")
    parser.setColumnID(3, "shunt4")
    parser.setColumnID(4, "bioz1")
    parser.setColumnID(5, "bioz2")
    parser.setColumnID(6, "bioz3")
    parser.setColumnID(7, "bioz4")

    shunt1 = ParserColumnHandler(parser, 0)
    shunt2 = ParserColumnHandler(parser, 1)
    shunt3 = ParserColumnHandler(parser, 2)
    shunt4 = ParserColumnHandler(parser, 3)

    bioz1 = ParserColumnHandler(parser, 4)
    bioz2 = ParserColumnHandler(parser, 5)
    bioz3 = ParserColumnHandler(parser, 6)
    bioz4 = ParserColumnHandler(parser, 7)

    uart.startReadingProcess()

    app = QApplication(sys.argv)

    # Timer global pour parser + calculer
    parse_timer = QTimer()
    parse_timer.timeout.connect(parser.parseNewValues)
    parse_timer.start(50)

    window1 = QMainWindow()
    widget1 = QScope([
        ("shunt1", shunt1.getQueue()),
        ("shunt2", shunt2.getQueue()),
        ("shunt3", shunt3.getQueue()),
        ("shunt4", shunt4.getQueue()),
    ])
    window1.setCentralWidget(widget1)
    window1.setWindowTitle("Oscilloscope 1")
    window1.resize(1200, 600)
    window1.show()

    window2 = QMainWindow()
    widget2 = QScope([
        ("bioz1", bioz1.getQueue()),
        ("bioz2", bioz2.getQueue()),
        ("bioz3", bioz3.getQueue()),
        ("bioz4", bioz4.getQueue()),
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