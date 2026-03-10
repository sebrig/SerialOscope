import serial
from multiprocessing import Process, Queue, Value
from queue import Empty

class SerialHandler:
    """
    Classe permettant de rececvoir des paquets python
    """

    def __init__(self, p_com_port : str,  p_baudrate:int=115200 ):
        self.__com_port = p_com_port
        self.__baudrate = p_baudrate
        self.__serial_object = None

        self.__reading_queue = Queue()
        self.__running_flag = Value('b', False)
        self.__reading_process = None

    def connect(self) -> bool:
        """
        Ouvre la connexion avec le port en série
        p_baudrate : int : Le baudrate de la connexion
        Retourne True si la connexion est établie, False sinon
        """

        self.__serial_object = serial.Serial(
            port=self.__com_port,
            baudrate=self.__baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout = 1
        )         

        print( f"UART is now connected on port {self.__com_port}" )      
        
        return self.__serial_object != None

    def disconnect(self):
        """
        Déconnecte le port en série
        """

        if self.__serial_object is None:
            return
        
        self.__serial_object.close()
        
        print( "Serial port is now disconnected" )
        return

    def readSerialLine(self):
        """
        Lit une ligne du port en série dont la structure est la suivante:
            val1,val2,...,valN\n
        Retourne un iterateur (val1, val2, ...)
        """

        try:
            msg = self.__serial_object.readline().decode().strip().split(',')
            for i in range(len(msg)):
                yield int(msg[i])
        except:
            return None

    def _readingProcess( self, data_queue : Queue, running_flag : Value ):
        self.connect()
        while running_flag.value:
            data = [i for i in self.readSerialLine()]
            #print( "received data : ", data )
            data_queue.put( data )

        print( "UART : Reading loop has ended" )
        self.disconnect()

    def getData(self):
        return self.__reading_queue.get()

    def getAllData(self):
        items = []
        while True:
            try:
                items.append(self.__reading_queue.get_nowait())
            except Empty:
                break
        return items

    def dataInBuffer(self):
        return self.__reading_queue.qsize()

    def startReadingProcess(self):
        self.__running_flag.value = True
        self.__reading_process = Process(target=self._readingProcess, args=(self.__reading_queue,self.__running_flag))
        self.__reading_process.start()

        return True

    def stopReadingProcess(self):
        self.__running_flag.value = False
        if self.__reading_process:
            self.__reading_process.join(timeout=1)  # attend max 1 seconde
            if self.__reading_process.is_alive():
                self.__reading_process.terminate()
                self.__reading_process.join()

if __name__=="__main__":
    import time

    uart = SerialHandler( "COM3", p_baudrate=921600 )
    uart.startReadingProcess()

    start = time.time()
    while time.time()-start < 3:
        data = uart.getAllData()
        print( "Data popped from process : ", data)

    uart.stopReadingProcess()