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
import threading

CHUNK = 1024
TABLE_LENGTH = 1024
RATE = 11025
CHANNELS = 1
SAMPLE_TIME = ( 1 / float(RATE) )

CHUNK_TIME = (float(CHUNK) / float(RATE))

print ("system platform = " + sys.platform)
if sys.platform == 'darwin':
    CHANNELS = 1



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
    if(my_sgen != None):
        return my_sgen.callback(in_data, frame_count, time_info, status)
    else:
        return (None, pyaudio.paComplete)
class soundgen(object):
    '''
    classdocs
    '''

    def __init__(self, pyaudio_inst=None, debug=False):
        '''
        Constructor
        '''
        self.debug = debug
        
        self.wave = sine(1.0, 1.0, RATE)
        self.phase = 0.0
        self.frequency = 200.0
        
        self.attack = 0.001
        self.decay = 0.05
        self.hold = 0.01
        self.period = 0.125
        
        self.pulse_time = 0
        self.pulse_amplitude = 0
        
        self.gen_buffer = numpy.zeros(CHUNK * CHANNELS, numpy.float32)
        self.chunks = Queue.Queue(3)
        self.amplitude = 0.5

        self.stream = None
        
        self.p = pyaudio_inst
        
        self.quietchunk = (self.gen_buffer.astype(numpy.float32).tostring())
        
        self.stop_flag = threading.Event()
        
        self.sgen_thread = threading.Thread(target=self.sgen_app)
        self.sgen_thread.daemon = True
        self.sgen_thread.start()
    
    
    def sgen_app(self):
        self.p = pyaudio.PyAudio()
        self.open_stream()
        self.run()
        self.close_stream()
        self.p.terminate()
        if(self.debug == True): 
            print("sgen app finished")       

       
    def app_running(self):
        return self.sgen_thread.isAlive()
        
    def open_stream(self):
        if(self.debug == True): print("sgen opening stream")
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=CHANNELS, rate=RATE, output=True, stream_callback=cb) #self.callback
        
    def stop(self):
        self.stop_flag.set()
        if(self.debug == True): print("soundgen stop request set")  


    def callback(self, in_data, frame_count, time_info, status):
#        print("in_data[0], in_data_len, frame count, status", in_data[0], len(in_data), frame_count, status)
        if(self.debug == True): print("pyaudio callback")
        try:
            self.outchunk = self.chunks.get_nowait()
            self.chunks.task_done()
            return (self.outchunk, pyaudio.paContinue)
        except:
            if(self.debug == True): print("no chunks available, playing quiet chunk")
            return ( self.quietchunk, pyaudio.paContinue)


# pulsestates A=attack, H=hold, D=decay, E=end

    def gen_sound(self):    
        phase_delta = self.frequency * (float(TABLE_LENGTH) / float(RATE) )
    
        self.pulse_amplitude = 1.0
    
        #=======================================================================
        # #rates per frame step
        # attack_rate = 1 / (float(RATE) * self.attack)
        # decay_rate = 1 / (float(RATE) * self.decay)
        # 
        timeout_step = 0
        #             
        for i in xrange(0, CHUNK-1):
        #     if(self.pulse_time < SAMPLE_TIME):
        #         self.pulse_state = "A"
        #         
        #     if(self.pulse_state == "A"):seconds
        #         self.pulse_amplitude += attack_rate
        #         if(self.pulse_amplitude > 1.0):
        #             self.pulse_amplitude = 1.0
        #             self.pulse_state = 'H'
        #     
        #     if(self.pulse_state == 'H'):
        #         if(self.pulse_time > (self.attack + self.hold)):
        #             self.pulse_state = 'D'
        #               
        #     if(self.pulse_state == "D"):
        #         self.pulse_amplitude -= decay_rate
        #         if(self.pulse_amplitude < 0.0):
        #             self.pulse_amplitude = 0.0
        #             self.pulse_state = 'E'
        #     
        #     self.pulse_time += SAMPLE_TIME
        #     if(self.pulse_time > self.period):
        #         self.pulse_time -= self.period
        #         self.pulse_state = "A"
        #=======================================================================

            self.phase += phase_delta
            if(self.phase >= TABLE_LENGTH):
                self.phase -= TABLE_LENGTH
            value = self.wave[int(self.phase)] * self.amplitude * self.pulse_amplitude
            if(CHANNELS == 2):
                self.gen_buffer[i*2] = value
                self.gen_buffer[(i*2)+1] = value
            else:
                self.gen_buffer[i] = value
                
            timeout_step += 1
            if(timeout_step > 10):
                timeout_step = 0
                time.sleep(0)   #yield to callback that needs to run quickly
 
        return (self.gen_buffer.astype(numpy.float32).tostring())
            
            
    def run(self):
        if(self.stream == None): 
            if(self.debug == True): print("stream not found at start of run, returning")
            return
                
        while not self.stop_flag.is_set():
            if not self.chunks.full():
                chunk = self.gen_sound()                
                try:
                    self.chunks.put_nowait(chunk)
                except:
                    if(self.debug == True): print("chunk queue full")
            else:
                time.sleep(0.01)

            self.frequency += 1
                    
        print("ended soundgen run")
    
        
    def close_stream(self):
        if(self.debug == True): print("sgen closing stream")
        if(self.stream != None):
            self.stream.stop_stream()
            while(self.stream.is_active()):
                time.sleep(0.1)
            self.stream.close()
            if(self.debug == True): print("closed soundgen stream")
    #        self.sgen_thread.join()
        
if __name__ == '__main__':
    
    my_sgen = soundgen(debug=True)
    raw_input("Press Return to exit...")
    #time.sleep(30)
    my_sgen.stop()
    while(my_sgen.app_running()):
        time.sleep(0.5)
    
    print("finished soundgen main")