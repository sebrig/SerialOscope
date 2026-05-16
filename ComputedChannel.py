from collections import deque
from typing import Callable
from typing import TypedDict

from .SerialParser import SerialParser, ParserColumnHandler

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
        
        new_values = n - self.__last_processed
        if new_values <= 0:
            return
        
        for i in range(n - new_values, n):
            params = [j[i] for j in self.__queues]
            self.__result.append(self.__func(*params))
        
        self.__last_processed += new_values

    def getQueue(self) -> deque:
        return self.__result

class ComputedChannel2:
    def __init__(self, p_params : dict[deque], p_callbacks : list[Callable], p_max : int = 1000 ):
        self.__params : list[deque] = p_params
        self.__callbacks : list[Callable] = p_callbacks
        self.__n_values = len( self.__params )
        self.__n_callbacks = len( self.__callbacks )
        
        self.__queues = {}
        for i in self.__callbacks:
            self.__queues[ i.__name__ ] = deque( maxlen=p_max )
        
    def update( self ):
        max_loop = 100

        while len(self.__params[0]) > 0:
            params = []
            for i in range( self.__n_values ):
                params.append( self.__params[i].popleft() )

            for i_func in self.__callbacks:
                self.__queues[ i_func.__name__ ].append( i_func( *params ) )            
            
            max_loop -= 1
            if max_loop <= 0:
                break

    def getCallbacksNames( self ):
        return [i.__name__ for i in self.__callbacks]

    def getQueues( self ):
        return self.__queues

    def getQueue( self, p_name ):
        return self.__queues[ p_name ]