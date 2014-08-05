'''
Created on 4 Aug 2014

@author: matt
'''
import pyaudio
import numpy
from math import *
import time
import Queue
import sys

CHUNK = 1024
TABLE_LENGTH = 1024
RATE = 11025
CHANNELS = 1

print ("system platform = " + sys.platform)
if sys.platform == 'darwin':
    CHANNELS = 1

p = pyaudio.PyAudio()


def sine(frequency, time, rate):
    length = int(time * rate)
    factor = float(frequency) * (pi * 2) / rate
    return numpy.sin(numpy.arange(length) * factor)


def cb(in_data, frame_count, time_info, status):
    return myvario.callback(in_data, frame_count, time_info, status)

class soundgen(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.wave = sine(1.0, 1.0, RATE)
        self.phase = 0.0
        self.frequency = 200.0
        
        self.gen_buffer = numpy.zeros(CHUNK, numpy.float32)
        self.chunks = Queue.Queue(2)
        self.first_chunk = True
                
        self.stream = p.open(format=pyaudio.paFloat32,
                                  channels=CHANNELS, rate=RATE, output=True, input=True, stream_callback=cb) #self.callback
            
    def callback(self, in_data, frame_count, time_info, status):
        chunk = self.chunks.get(True, 1.0)
        self.chunks.task_done()
        return (chunk, pyaudio.paContinue)

    def gen_sound(self):
        phase_delta = self.frequency * (float(TABLE_LENGTH) / float(RATE) )
        for i in xrange(0, CHUNK-1):
            self.phase += phase_delta
            if(self.phase >= TABLE_LENGTH):
                self.phase -= TABLE_LENGTH
            self.gen_buffer[i] = self.wave[int(self.phase)]
        
        chunk = (self.gen_buffer.astype(numpy.float32).tostring())
        self.chunks.put(chunk, True, 0.5)
        
    def run(self):

        for i in xrange(0,100):
            if(self.chunks.empty()):
                self.gen_sound()
            else:
                time.sleep(0.05)
    
#            if(self.first_chunk == True):
#                self.stream.start_stream()
#                self.first_chunk = False
               
#        self.stream.stop_stream()
#        self.stream.close()
#        time.sleep(0.1)
        
        #self.stream.write(self.buffer.astype(numpy.float32).tostring()
        
myvario = soundgen()
myvario.run()
p.terminate()