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

fs = 200
n_buffer = int( fs )
csv = CSVwritter( ["Q","I","current_max"], "./Recordings/", "mcu_measures.csv" )
uart = SerialHandler("COM3", 112500, csv)
parser = SerialParser( uart, n_buffer )


def calcAmplitude( p_re, p_im, K ):
    calcAmplitude.counter += 1

    amplitude = np.sqrt( p_re**2 + p_im**2 ) * K
    calcAmplitude.sum_mean += amplitude

    if calcAmplitude.counter % calcAmplitude.mean_window == 0:
        print( f"amplitude =    {calcAmplitude.sum_mean/calcAmplitude.mean_window:00.3f}" )
        calcAmplitude.sum_mean = 0

    return amplitude

calcAmplitude.counter = 0
calcAmplitude.sum_mean = 0
calcAmplitude.mean_window = fs

def calcPhase( p_re, p_im, offset ):
    calcPhase.counter += 1

    phase = np.rad2deg( np.arctan2( p_im, p_re ) ) + offset
    calcPhase.sum_mean += phase
    
    if calcPhase.counter % calcPhase.mean_window == 0:
        print( f"phase =        {calcPhase.sum_mean/calcPhase.mean_window:00.3f}" )
        calcPhase.sum_mean = 0

    return phase

calcPhase.counter = 0
calcPhase.sum_mean = 0
calcPhase.mean_window = fs

def calcAsyncAmplitude( p_shunt, p_bioz ):
    amplitude = np.abs( p_bioz/(p_shunt+1e-12) ) * 1e3 * 0.5
    print( f"amplitude = {amplitude:00.3f} | [ {p_shunt}, {p_bioz} ]" )

    if amplitude > 150:
        return calcAsyncAmplitude.last_val

    calcAsyncAmplitude.last_val = amplitude
    
    return amplitude
calcAsyncAmplitude.last_val = 0

def calcAsyncPhase( p_Qshunt, p_Ishunt, p_Qbioz, p_Ibioz ):
    phase_bioz = 0

    # amplitude du signal trop faible pour retourner une info fiable
    if abs(p_Qbioz) > 10 and abs(p_Ibioz) > 10:
        phase_shunt  = np.rad2deg( np.arctan2(p_Qshunt, p_Ishunt) )
        phase_bioz  = np.rad2deg( np.arctan2(p_Qbioz, p_Ibioz) ) - phase_shunt
        # print( f"phase = {phase_bioz:00.2f} | [ {p_Qshunt}, {p_Ishunt}, {p_Qbioz}, {abs(p_Ibioz)} ]" )

    return phase_bioz

class ComputedChannel:
    def __init__(self, p_queues: list[deque], p_func, p_max: int = 1000 ):
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
    parser.setColumnID(0, "Q")
    parser.setColumnID(1, "I")
    parser.setColumnID(2, "current_max")

    Q = ParserColumnHandler( parser, 0 )
    I = ParserColumnHandler( parser, 1 )
    current_max = ParserColumnHandler( parser, 2 )

    amplitude_lpf = RealTime_ButterworthFilter(p_cutoff=1, p_fs=fs)
    phase_lpf = RealTime_ButterworthFilter(p_cutoff=1, p_fs=fs)

    # amplitude = ComputedChannel(I.getQueue(), Q.getQueue(), calcAmplitude)
    amplitude = ComputedChannel(
        [I.getQueue(), Q.getQueue()],
        # lambda re, im: amplitude_lpf.filter(calcAsyncAmplitude(re, im)),
        # lambda re, im : amplitude_lpf.filter(calcAsyncAmplitude( re, im )),
        lambda re, im : calcAmplitude( re, im, 45.666e-3 ),
        p_max=n_buffer
    )

    # phase = ComputedChannel(I.getQueue(), Q.getQueue(), calcPhase)
    phase = ComputedChannel(
        [Q.getQueue(), I.getQueue()],
        # lambda Qshunt, Ishunt, Qbioz, Ibioz: phase_lpf.filter(calcAsyncPhase( Qshunt, Ishunt, Qbioz, Ibioz )),
        # lambda Qshunt, Ishunt, Qbioz, Ibioz : phase_lpf.filter(calcAsyncPhase( Qshunt, Ishunt, Qbioz, Ibioz )),
        lambda re, im : calcPhase( re, im, -3.481 ),
        p_max=n_buffer
    )

    uart.startReadingProcess()

    app = QApplication(sys.argv)

    # Timer global pour parser + calculer
    parse_timer = QTimer()
    parse_timer.timeout.connect(on_parse)
    parse_timer.start(50)

    window1 = QMainWindow()
    widget1 = QScope([( "Amplitude", amplitude.getQueue() )])
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
        close_timer = QTimer()
        close_timer.setSingleShot(True)
        close_timer.timeout.connect(app.quit)
        close_timer.start(95_000)  # 10 secondes
        sys.exit(app.exec())
    finally:
        uart.stopReadingProcess()

        if csv is not None:
            csv.closeCSVWriter()

        widget1.stop()
        widget2.stop()