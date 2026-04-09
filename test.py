import numpy as np
import matplotlib.pyplot as plt
import Filtres 

data = np.genfromtxt( "./Recordings/amplitude_respiration.csv", delimiter=',', skip_header=1 )

fs = 1250 

freq, fft = Filtres.fft( data, fs )
plt.plot(freq[1:int(len(freq)/2)], fft[1:int(len(freq)/2)])
plt.semilogx()
plt.show()

# fcut = 5
# width = 10
# ripple_db = 80
# data = Filtres.lowpass_filter( data, fcut, width, ripple_db, fs )

low_cut = 4
high_cut = 12
data = Filtres.butter_bandpass_filter( data, low_cut, high_cut, fs, order=4 )

plt.plot( data )
plt.show()

freq, fft = Filtres.fft( data, fs )
plt.plot(freq[1:int(len(freq)/2)], fft[1:int(len(freq)/2)])
plt.semilogx()
plt.show()