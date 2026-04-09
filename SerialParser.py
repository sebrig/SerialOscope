from SerialHandler import SerialHandler
from collections import deque

class SerialParser:
    """
    Classe permettant de faire manipuler les données
    recu par le UART
    """

    def __init__( self, p_serial : SerialHandler, p_max : int = 100 ):
        self.__serial = p_serial

        self.__values : list = []
        self.__columns : dict = {}
        self.__max = p_max

    def parseNewValues(self):
        for data in self.__serial.getAllData():
            #print( "New data in parser : ", data )

            for i in range(len(data)):
                if i not in self.__columns:
                    self.createColumn( i, i )

                self.__values[i].append( data[i] )

    def getColumnsID(self):
        return [i for i in self.__columns.values()]

    def createColumn(self, p_id, p_column_name ):
        if p_id in self.__columns: return 

        self.__columns[p_id] = p_column_name
        self.__values.append( deque(maxlen=self.__max) )

    def setColumnID(self, p_id, p_column_name):
        if p_id not in self.__columns: 
            self.createColumn( p_id, p_column_name )

        self.__columns[p_id] = p_column_name

    def getColumnsValues(self):
        r_dict = {}
        for i in range(len( self.__values )):
            r_dict[ self.__columns[i] ] = self.__values[i]

        return r_dict

    def getColumnValues(self, p_column_name):
        if p_column_name not in self.__columns.values():
            return None

        return self.getColumnsValues()[p_column_name]

    def dataInBuffer(self):
        r_items_in_buffers = []

        for i in self.__values:
            r_items_in_buffers.append( len(i) )

        return r_items_in_buffers

    def __str__(self):
        r_str = ""

        for i in range(len(self.__values)):
            r_str += f"{self.__columns[i]} : \n\t"

            for j in self.__values[i]:
                r_str += f"{j},"
            
            r_str = r_str[:-1]+'\n'
        
        return r_str

class ParserColumnHandler:
    def __init__(self, p_parser : SerialParser, p_column_id ):
        self.__parser = p_parser
        self.__column_id = p_column_id

    def getColumnName(self):
        return self.__parser.getColumnsID()[self.__column_id]

    def getColumnValue(self):
        return self.__parser.getColumnValues( self.getColumnName() )

    def dataInBuffer(self):
        return self.__parser.dataInBuffer()[self.__column_id]

    def getData(self):
        return self.getColumnValue().pop()

    def getQueue(self):
        return self.getColumnValue()

if __name__ == '__main__':
    import time

    uart = SerialHandler("COM3", 921600)
    parser = SerialParser( uart )

    parser.setColumnID(0, "Time")
    time_val = ParserColumnHandler( parser, 0 )

    parser.setColumnID(1, "Valeur 1")

    uart.startReadingProcess()

    start = time.time()
    while time.time()-start < 1:
        parser.parseNewValues()

    uart.stopReadingProcess()

    print( parser )

    print( time_val.getColumnName() )
    print( time_val.getColumnValue() )

