from scipy.signal import butter, lfilter, sosfilt, sosfilt_zi, filtfilt, kaiserord, firwin
import numpy as np

class RealTime_ButterworthFilter:
    def __init__(self, p_cutoff: float, p_fs: float, p_order: int = 4):
        """
        p_cutoff : fréquence de coupure en Hz
        p_fs     : fréquence d'échantillonnage en Hz
        p_order  : ordre du filtre
        """
        self.__sos = butter(p_order, p_cutoff, fs=p_fs, output='sos')
        self.__zi = sosfilt_zi(self.__sos) * 0  # état initial

    def filter(self, p_value: float) -> float:
        result, self.__zi = sosfilt(self.__sos, [p_value], zi=self.__zi)
        return result[0]

def butter_bandpass(lowcut, highcut, fs, order=5):
    return butter(order, [lowcut, highcut], fs=fs, btype='band')

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_lowpass(fcut, fs, order=5):
    return butter(order, fcut, fs=fs, btype='low')

def butter_lowpass_filter(data, fcut, fs, order=5):
    b, a = butter_lowpass(fcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def lowpass( f_cut, width, ripple_db, fs):
    numtaps, beta = kaiserord(ripple_db, width / (fs / 2))
    return firwin(numtaps, f_cut / (fs / 2), window=('kaiser', beta))

def lowpass_filter( data,  f_cut, width, ripple_db, fs ):
    taps = lowpass( f_cut, width, ripple_db, fs )

    print(len(data), len(taps))
    
    return filtfilt( taps, 1, data )

def fft( data, fs ):
    fft_values = np.fft.fft( data )
    frequencies = np.fft.fftfreq( len(data), 1/fs )

    amplitude = np.abs(fft_values)
    amplitude = amplitude#[ :int(len(amplitude)/2) ]
    frequencies = frequencies#[ :int(len(frequencies)/2) ]

    return ( frequencies, amplitude )