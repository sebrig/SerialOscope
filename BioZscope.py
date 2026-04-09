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
from Filtres import RealTime_ButterworthFilter

fs = 2e3
n_buffer = int(fs) 
uart = SerialHandler("COM3", 921600)
parser = SerialParser( uart, n_buffer )
csv_writter = None # CSVwritter( ["Amplitude"], "./Recordings/", "amplitude_respiration.csv" )

def calcAmplitude( p_re, p_im ):
    return np.sqrt( p_re**2 + p_im**2 )

def calcPhase( p_re, p_im ):
    return np.rad2deg( np.arctan2( p_im, p_re ) )

def calcAsyncAmplitude( p_shunt, p_bioz ):
    amplitude = np.abs( p_bioz/(p_shunt+1e-12) ) * 1e3
    # print( f"amplitude = {amplitude:00.3f} | [ {p_shunt}, {p_bioz} ]" )
    
    return amplitude

def calcAsyncPhase( p_Qshunt, p_Ishunt, p_Qbioz, p_Ibioz ):
    # amplitude du signal trop faible pour retourner une info fiable
    if abs(p_Qbioz) < 10 and abs(p_Ibioz) < 10:
        return 0

    phase_shunt  = np.rad2deg( np.arctan2(p_Qshunt, p_Ishunt) )
    phase_bioz  = np.rad2deg( np.arctan2(p_Qbioz, p_Ibioz) ) - phase_shunt
    # print( f"phase = {phase_bioz:00.2f} | [ {p_Qshunt}, {p_Ishunt}, {p_Qbioz}, {abs(p_Ibioz)} ]" )
    
    return phase_bioz

class ComputedChannel:
    def __init__(self, p_queues: list[deque], p_func, p_max: int = 1000):
        self.__queues = p_queues
        self.__func = p_func
        self.__result = deque(maxlen=p_max)
        self.__last_processed = 0

    def update(self):
        n = min([len(i) for i in self.__queues])
        if n == 0:
            return 
        
        new_values = n - self.__last_processed % n  # nouvelles valeurs depuis dernier update
        
        for i in range(n - new_values, n):
            params = [j[i] for j in self.__queues]
            self.__result.append(self.__func(*params))
        
        self.__last_processed += new_values

    def getQueue(self) -> deque:
        return self.__result

def on_parse():
    parser.parseNewValues()
    amplitude.update()
    phase.update()

if __name__=="__main__":
    parser.setColumnID(0, "Ishunt")
    parser.setColumnID(1, "Qshunt")
    parser.setColumnID(2, "Ibioz")
    parser.setColumnID(3, "Qbioz")

    Ishunt = ParserColumnHandler( parser, 0 )
    Qshunt = ParserColumnHandler( parser, 1 )
    Ibioz = ParserColumnHandler( parser, 2 )
    Qbioz = ParserColumnHandler( parser, 3 )

    amplitude_lpf = RealTime_ButterworthFilter(p_cutoff=10, p_fs=fs)
    phase_lpf = RealTime_ButterworthFilter(p_cutoff=10, p_fs=fs)

    # amplitude = ComputedChannel(I.getQueue(), Q.getQueue(), calcAmplitude)
    amplitude = ComputedChannel(
        [Ibioz.getQueue(), Qbioz.getQueue()],
        lambda re, im: amplitude_lpf.filter(calcAsyncAmplitude(re, im)),
        p_max=n_buffer
    )

    # phase = ComputedChannel(I.getQueue(), Q.getQueue(), calcPhase)
    phase = ComputedChannel(
        [Ishunt.getQueue(), Qshunt.getQueue(),
        Ibioz.getQueue(), Qbioz.getQueue()],
        lambda Qshunt, Ishunt, Qbioz, Ibioz: phase_lpf.filter(calcAsyncPhase( Qshunt, Ishunt, Qbioz, Ibioz )),
        p_max=n_buffer
    )

    uart.startReadingProcess()

    app = QApplication(sys.argv)

    # Timer global pour parser + calculer
    parse_timer = QTimer()
    parse_timer.timeout.connect(on_parse)
    parse_timer.start(50)

    window1 = QMainWindow()
    widget1 = QScope([( "Amplitude", amplitude.getQueue() )], csv_writter)
    window1.setCentralWidget(widget1)
    window1.setWindowTitle("Oscilloscope 1")
    window1.resize(1200, 600)
    window1.show()

    window2 = QMainWindow()
    widget2 = QScope([( "Phase", phase.getQueue() )])
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

        if csv_writter is not None:
            csv_writter.closeCSVWriter()
        
        widget1.stop()
        widget2.stop()