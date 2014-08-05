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
CHANNELS = 2

print ("system platform = " + sys.platform)
if sys.platform == 'darwin':
    CHANNELS = 1

p = pyaudio.PyAudio()


def sine(frequency, time, rate):
    length = int(time * rate)
    factor = float(frequency) * (pi * 2) / rate
    return numpy.sin(numpy.arange(length) * factor)


def cb(in_data, frame_count, time_info, status):
    flags = status
#    print("in_data[0], in_data_len, frame count, status", in_data[0], len(in_data), frame_count, status)
    if flags != 0:
        if flags & pyaudio.paInputOverflow: print("Input Overflow")
        if flags & pyaudio.paInputUnderflow: print("Input Underflow")
        if flags & pyaudio.paOutputOverflow: print("Output Overflow")
        if flags & pyaudio.paOutputUnderflow: print("Output Underflow")
        if flags & pyaudio.paPrimingOutput: print("Priming Output")
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
        self.frequency = 300.0
        
        self.gen_buffer = numpy.zeros(CHUNK * CHANNELS, numpy.float32)
        self.chunks = Queue.Queue(3)
        self.first_chunk = True
        self.amplitude = 0.25
        
        self.stream = p.open(format=pyaudio.paFloat32,
                                  channels=CHANNELS, rate=RATE, output=True, input=True, stream_callback=cb) #self.callback
            
    def callback(self, in_data, frame_count, time_info, status):
        print("in_data[0], in_data_len, frame count, status", in_data[0], len(in_data), frame_count, status)
        try:
            chunk = self.chunks.get_nowait()
            self.chunks.task_done()
            return (chunk, pyaudio.paContinue)
        except:
            print("no chunks available")
            return ( in_data, pyaudio.paContinue)


    def gen_sound(self):
        phase_delta = self.frequency * (float(TABLE_LENGTH) / float(RATE) )
        for i in xrange(0, CHUNK-1):
            self.phase += phase_delta
            if(self.phase >= TABLE_LENGTH):
                self.phase -= TABLE_LENGTH
            self.gen_buffer[i*2] = self.wave[int(self.phase)] * self.amplitude
            self.gen_buffer[(i*2)+1] = self.wave[int(self.phase)] * self.amplitude
            time.sleep(0)   #yield to callback that needs to run quickly

        
        chunk = (self.gen_buffer.astype(numpy.float32).tostring())
        try:
            self.chunks.put_nowait(chunk)
        except:
            print("not enough space in chunk queue")
            
    def run(self):
        endtime = time.time() + 10
        
        while time.time() < endtime:
            if(not self.chunks.full()):
                self.gen_sound()
                self.frequency += 1
            else:
                time.sleep(0.01)
    
#            if(self.first_chunk == True):
#                self.first_chunk = False
            if(self.stream.is_active() == False):
                self.stream.start_stream()
               
#        self.stream.stop_stream()
#        self.stream.close()
#        time.sleep(0.1)
        
        #self.stream.write(self.buffer.astype(numpy.float32).tostring()
        
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
       
        
myvario = soundgen()
myvario.run()
myvario.close()
p.terminate()