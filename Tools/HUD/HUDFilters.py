'''
Created on Jun 26, 2015

@author: matt
'''

import time

class LowPassFilter(object):
    def __init__(self, const=0.5, value = 0.0):
        self.const = const
        self.output = value
        self.last_filter_time = 0
        
    def run_filter(self, input, timestamp=0):
        if timestamp == 0:
            time_now = time.time()
        else:
            time_now = timestamp
        delta_time = time_now - self.last_filter_time
        coeff = self.const * delta_time
        if coeff > 1.0:
            coeff = 1.0;
        self.output = (coeff * input) + ((1-coeff) * self.output)
        self.last_filter_time = time_now
        return self.output
    
    def set_filter(self, value):
        self.output = value
    
    def get_output(self):
        return self.output;
    

class Filter(object):
    def __init__(self, filter_const=0.5, rate_gain=1.0, rate_const=0.6, rate_decay=0.5, max_deltatime=1.0):
        self.rate_gain = rate_gain;
        
        self.rate_filter = LowPassFilter(const=rate_const)
        self.output_filter = LowPassFilter(const=filter_const)
        self.input_value = 0;
                
        self.system_timestamp = 0
        self.measurement_timestamp = 0
        self.max_deltatime = max_deltatime
        
    def observation(self, value, rate, measurement_timestamp, system_timestamp):
        if(measurement_timestamp != self.measurement_timestamp):    # Filter identical measurements
            self.input_value = value
            self.rate_filter.run_filter(rate, measurement_timestamp)
            self.measurement_timestamp = measurement_timestamp
            self.system_timestamp = system_timestamp
                
    def estimate(self, deltatime=0):
        if(deltatime == 0):
            deltatime = time.time() - self.system_timestamp
            if(deltatime > self.max_deltatime):
                deltatime = self.max_deltatime
            coeff = deltatime * self.rate_gain            
            estimate = self.input_value + (self.rate_filter.get_output() * coeff)
        return self.output_filter.run_filter(estimate)
    

class AngleFilter(Filter):
    def __init__(self, filter_const=0.5, rate_gain=1.0, rate_const=0.6, rate_decay=0.5, degrees=True):
        Filter.__init__(self, filter_const, rate_gain, rate_const, rate_decay)
        self.degrees = degrees
        
        if(degrees == False):
            print("RADIANS NOT YET SUPPORTED, DOING DEGREES")
        
    def observation(self, value, rate, measurement_timestamp, system_timestamp):
        # precondition value so it is never more than 360 degrees away from last filter output
        output = self.output_filter.get_output()
        if(value >= output + 360):
            precond = value - 360
        elif(value <= output - 360):
            precond = value + 360
        else:
            precond = value
        
        Filter.observation(self, precond, rate, measurement_timestamp, system_timestamp)
        
        # Adjust filter angle rollover
        output = self.output_filter.get_output()
        if(output > 180):
            self.output_filter.set_filter(output-360)
        elif(output < -180):
            self.output_filter.set_filter(output+360)
            
    def estimate(self, deltatime=0):
        outval = Filter.estimate(self, deltatime)

        # correct for angle rollover
        if(outval > 180.0):
            outval = outval - 360
            self.output_filter.set_filter(outval-360.0)
        elif(outval < -180.0):
            outval = outval +360
            self.output_filter.set_filter(outval+360.0)
            
        return outval