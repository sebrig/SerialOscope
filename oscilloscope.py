####################################################################################################

# User-modifiable variables
PORT = 'COM14'
BATCH_LENGTH = 100 # Number of elements per bulk transfer
PLOT_LENGTH = 1*BATCH_LENGTH # Number of values to display at once
DIR_PATH = r"./Recordings" # Where the csv files will be written

#####################################################################################################


from CSVwritter import CSVwritter
from SerialHandler import SerialHandler

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time
from collections import deque
import schedule


class Oscilloscope:
    """
    Classe permettant d'afficher des donnees recu par uart
    """
    def __init__(self, p_com_port : str, p_save_dir : str, p_save_file=None, p_baudrate=112500 ):
        self.__uart : SerialHandler = SerialHandler( p_com_port, p_baudrate )
        self.__csv_writer : CSVwritter = CSVwritter( ["Time", "Data"], p_save_dir, p_save_file )
        
        self.__time = deque(np.arange(-PLOT_LENGTH, 0, 1), maxlen=PLOT_LENGTH)
        self.__data = deque(np.zeros(PLOT_LENGTH), maxlen=PLOT_LENGTH)


    def _animate(self, i):
        """
        Fonction d'animation pour le plot avec matplotlib.pyplot
        i : int : L'index de l'animation.
        """

        self.line.set_data(self.__time, self.__data)            # update data dans le plot
        self.ax.set_xlim((min(self.__time),max(self.__time)))   # update limites de l'axe x
        return self.line

    def pltAnimation(self) -> bool:
        """
        Lit les valeurs retournées par le port en série et les affiche 
        dans un plot anime 
        Retourne True si l'animation a bien ete executee, False en cas d'erreur
        """

        self.fig, self.ax = plt.subplots()
        self.line = self.ax.plot(self.__time, self.__data)[0]
        plt.show(block=False)

        plt.xlabel("Time (ms)")
        plt.ylabel("Digital value")
        plt.title("Arduino Data")
        plt.legend(["Raw signal"])
        plt.ylim([0, 1024])

        self.ani = animation.FuncAnimation(
            self.fig,
            self._animate, 
            save_count=PLOT_LENGTH, 
            interval=200, 
            blit=False
        )

        return self._run(self._pltAnimationRefresh)

    def _pltAnimationRefresh(self):
        """
        Rafraichit le plot
        """

        plt.draw()
        plt.pause(0.1)

    def _run(self, p_refresh_cb) -> bool:
        """
        Boucle de lecture des données du port en série
        Retourne True si l'animation a bien ete executee, False en cas d'erreur
        """

        self.__uart.startReadingProcess()
        schedule.every(1/60).seconds.do(p_refresh_cb)
        
        run_loop = True

        print("Press CTRL-C to exit.")

        time_since_start = 0
        while run_loop:
            try:
                data = self.__uart.getData()
                print( data )

                self.__time.append( data[0] )
                self.__data.append( data[1] )

                self.__csv_writer.writeColumn( data )

                schedule.run_pending()
                time.sleep(0.01)

            # arret de la boucle si CTRL-C
            except KeyboardInterrupt:
                run_loop = False
        
        self.__uart.stopReadingProcess()
        print("Loop has ended")
        return True
    
    def __del__(self):
        """
        Destructeur de la classe ArduinoPlotter
        """

        self.__uart.stopReadingProcess()
        self.__csv_writer.closeCSVWriter()
        return

if __name__=="__main__":
    oscillo = Oscilloscope( 
        "COM4",
        "./",
        "test.csv"
    )

    oscillo.pltAnimation()