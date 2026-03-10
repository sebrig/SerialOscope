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

    def __init__(self, p_parser : list[SerialParser], p_channels : ParserColumnHandler ):
        super(QScope, self).__init__(None)

        self.__parser : SerialParser = p_parser
        self.__channels : ParserColumnHandler = p_channels

        self.__plot_length = 5000
        
        self.__time = deque(maxlen=self.__plot_length)
        self.__data = [deque(maxlen=self.__plot_length) for i in enumerate(self.__channels)]

        # --- Layout ---
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- PyQtGraph ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('black')
        self.plot_widget.setTitle("UART temps réel")
        self.plot_widget.setLabel('left', 'Valeur')
        self.plot_widget.setLabel('bottom', 'Échantillons')
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='blue', width=2))
        self.plot_widget.addLegend()

        self.__curves = []
        for i, ch in enumerate(self.__channels):
            color = QScope.__COLORS[i % len(QScope.__COLORS)]
            curve = self.plot_widget.plot(
                pen=pg.mkPen(color=color, width=2),
                name=ch.getColumnName() 
            )
            self.__curves.append(curve)
        
        
        layout.addWidget(self.plot_widget)
    
        # --- Timer de rafraîchissement ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.__time_since_start = 0
    
    def update_plot(self):
        self.__parser.parseNewValues()
        
        while self.__channels[0].dataInBuffer() > 0:
            self.__time.append( self.__time_since_start )
            
            for i, ch in enumerate(self.__channels):
                self.__data[i].append( ch.getData() )
            
            self.__time_since_start += 1
        
        for i, ch in enumerate(self.__channels):
            self.__curves[i].setData(self.__time, self.__data[i])

    def start(self):
        self.timer.start( 50 )

    def stop(self):
        self.timer.stop()

    def __del__(self):
        self.stop()


if __name__ == '__main__':
    uart = SerialHandler("COM3", 921600)
    writter = CSVwritter( ["Idx", "Value"], "./", "test.csv" )
    parser = SerialParser( uart, 1000 )

    parser.setColumnID(0, "shunt1")
    parser.setColumnID(1, "shunt2")
    parser.setColumnID(2, "shunt3")
    parser.setColumnID(3, "shunt4")
    parser.setColumnID(4, "bioz1")
    parser.setColumnID(5, "bioz2")
    parser.setColumnID(6, "bioz3")
    parser.setColumnID(7, "bioz4")

    shunt1 = ParserColumnHandler( parser, 0 )
    shunt2 = ParserColumnHandler( parser, 1 )
    shunt3 = ParserColumnHandler( parser, 2 )
    shunt4 = ParserColumnHandler( parser, 3 )

    bioz1 = ParserColumnHandler( parser, 4+0 )
    bioz2 = ParserColumnHandler( parser, 4+1 )
    bioz3 = ParserColumnHandler( parser, 4+2 )
    bioz4 = ParserColumnHandler( parser, 4+3 )
    
    uart.startReadingProcess()

    app = QApplication(sys.argv)

    window1 = QMainWindow()
    widget1 = QScope( parser, [shunt1, shunt2, shunt3, shunt4] )
    window1.setCentralWidget(widget1)
    window1.setWindowTitle("Oscilloscope 1")
    window1.resize(1200, 600)
    window1.show()

    window2 = QMainWindow()
    widget2 = QScope( parser, [bioz1, bioz2, bioz3, bioz4] )
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