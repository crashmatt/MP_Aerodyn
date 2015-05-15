#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals


import math, random, time, string

#import demo
import pi3d

from HUDladder import HUDladder
from LayerItems import LayerText
from LayerItems import LayerVarText
from LayerItems import LayerItems
from LayerItems import LayerNumeric
from LayerItems import LayerShape
from LayerItems import LayerDynamicShape
from LayerItems import LayerStringList
from ScreenGrid import ScreenScale

from Indicator import LinearIndicator
from Indicator import DirectionIndicator

from Box2d import Box2d

import HUDConfig as HUDConfig
import os
from multiprocessing import Queue

#import pdb        pdb.set_trace()
#import pydevd

standalone = False

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
        const = self.const * delta_time
        if const > 1.0:
            const = 1.0;
        self.output = (const * input) + ((1-const) * self.output)
        self.last_filter_time = time_now
        return self.output
    
    def get_output(self):
        return self.output;
    

class Filter(object):
    def __init__(self, damping=0.5, rate_gain=1.0, rate_damp=0.6):
        self.damping = damping;
        self.rate_gain = rate_gain;
        
        self.rate_filter = LowPassFilter(const=rate_damp)
        self.output_filter = LowPassFilter(const=damping)
        self.input_value = 0;
                
        self.system_timestamp = 0
        self.measurement_timestamp = 0
        
    def observation(self, value, rate, measurement_timestamp, system_timestamp):
        self.input_value = value
        self.rate_filter.run_filter(rate, measurement_timestamp)
        self.system_timestamp = system_timestamp
        self.system_timestamp = system_timestamp
                
    def estimate(self, deltatime=0):
        if(deltatime == 0):
            deltatime = time.time() - self.system_timestamp
            estimate = self.input_value + (deltatime * self.rate_filter.get_output() * self.rate_gain)
        return self.output_filter.run_filter(estimate)
    

class HUD(object):
    def __init__(self, simulate=False, master=True, update_queue=None):
        """
        *simulate* = generate random simulation data to display
        *master* Running as master and not a process
        """
        self.quit = False
        
#        self.working_directory = os.getcwd()
        self.working_directory = os.path.dirname(os.path.realpath(__file__))
        print("Working directory = " + self.working_directory)
               
        self.hud_update_frames = 5
        
        self.font_size = 0.15
        self.label_size = 0.125
        self.layer_text_spacing = 16
        self.text_box_height = 30
        
        self.text_alpha = 255
        self.label_alpha = 2
        self.pitch_ladder_alpha = 1
        self.pitch_ladder_text_alpha = 255
        
        self.hud_colour = (0,255,0,255)
        self.textbox_line_colour = self.hud_colour
        self.textbox_fill_colour = (0,0,0,0.75)
        
        self.fps = 20
        self.simulate = simulate
        self.master = master
                
        #Queue of attribute updates each of which is tuple (attrib, object)
        self.update_queue = update_queue

        self.init_vars()
        self.init_graphics()
        self.init_run()

    def init_vars(self):
        self.pitch = 0
        self.roll = 0
        self.pitch_rate = 0
        self.roll_rate = 0
        self.heading_rate = 0
        self.track_rate = 0
        self.track = 0
        self.tas = 0              # true airspeed
        self.ias = 0              # indicated airspeed
        
        self.attitude_timestamp = 0
        self.system_timestamp = time.time()
        
        self.flap = 0
        self.brake = 0
        self.flap_pcnt = 0
        self_brake_pcnt = 0
        
        self.hdop = 99
        self.satellites = 99
        self.aspd_rate = 1
        self.groundspeed = 999
        self.windspeed = 15
        self.heading = 221
        self.home = 120
        self.home_dist = 999
        self.home_dist_scaled = 0
        self.home_dist_units = "m"
        self.vertical_speed = 0.1
        self.asl = 9999             #altitude above sea level
        self.agl = 999              #altitude above ground level
        self.ahl = 999              #altitude above home level
        self.slip = 0               #slip in degrees
        self.mode = "FBW"
        
        self.pitch_filter = Filter(damping=0.75, rate_gain = 0.5)
        self.roll_filter = Filter(damping=0.75, rate_gain = 0.0)

        
#        self.climb_rate = 2.24

#    def post_variable(self, varname, value):
#        if(hasattr(self, varname)):
#            self.update_queue.put_nowait((varname, value))
        
    def init_graphics(self):
        """ Initialise the HUD graphics """

# Setup display and initialise pi3d
        self.DISPLAY = pi3d.Display.create(x=20, y=0, w=700, h=580, frames_per_second=self.fps)
        self.DISPLAY.set_background(0.0, 0.0, 0.0, 0)      # r,g,b,alpha
        
        self.background_colour=(0,0,0,255)
        self.background_distance=2000
        
        self.grid = ScreenScale(0.025,0.075)

        self.fpv_camera = pi3d.Camera.instance()
        self.text_camera = pi3d.Camera(is_3d=False)
        self.hud_camera = self.text_camera

        #setup textures, light position and initial model position

        self.fpv_light = pi3d.Light((0, 0, 1))

        #create shaders
        #shader = pi3d.Shader("uv_reflect")
        self.matsh = pi3d.Shader("mat_flat")  #For fixed color
        self.flatsh = pi3d.Shader("uv_flat")

        #Create layers
        self.dataLayer = pi3d.Layer(camera=self.text_camera, shader=self.flatsh, z=4.8, flip=True)
        self.statusLayer = pi3d.Layer(camera=self.text_camera, shader=self.flatsh, z=4.8, flip=True)
        self.slowLayer = pi3d.Layer(camera=self.text_camera, shader=self.flatsh, z=4.8, flip=True)
        self.staticLayer = pi3d.Layer(camera=self.text_camera, shader=self.flatsh, z=4.8, flip=True)

        #Create textures

        print("start creating fonts")
        #fonts
        #hudFont = pi3d.Font("fonts/FreeSans.ttf", (50,255,50,220))
        font_path = os.path.abspath(os.path.join(self.working_directory, 'fonts', 'FreeSansBold.ttf'))
        self.hudFont = pi3d.Font(font_path, self.hud_colour)   #usr/share/fonts/truetype/freefont/
        self.ladderFont = self.hudFont
        self.textFont = self.hudFont

        print("end creating fonts")
        
        print("start creating indicators")
        #Explicit working directory path done so that profiling works correctly. Don't know why. It just is.
        needle_path = os.path.abspath(os.path.join(self.working_directory, 'default_needle.img'))

        x,y = self.grid.get_grid_pixel(14, 0)
        self.VSI = LinearIndicator(self.text_camera, self.flatsh, self.matsh, self, "vertical_speed", 
                                   indmax=200, indmin=-200, x=x, y=y, z=3, width=18, length=180, 
                                   orientation="V", line_colour=(255,255,255,255), fill_colour=(0,0,0,0.5), 
                                   line_thickness = 1, needle_img=needle_path)

        #Add slip indicator.  Scale is in degrees
        x,y = self.grid.get_grid_pixel(0, -6)
        self.slip_indicator = LinearIndicator(self.text_camera, self.flatsh, self.matsh, self, "slip", 
                                              indmax=5, indmin=-5, x=x, y=y, z=3, width=21, length=250, 
                                              orientation="H", line_colour=(255,255,255,255), fill_colour=(0,0,0,0.75), 
                                              line_thickness = 1, needle_img=needle_path)
        print("end creating indicators")


        print("start creating ladder")
        self.ladder = HUDladder(font=self.hudFont, camera=self.hud_camera, shader=self.flatsh, alpha=self.pitch_ladder_alpha)
        print("end creating ladder")

        self.background = pi3d.Plane(w=self.DISPLAY.width, h=self.DISPLAY.height, z=self.background_distance,
                                camera=self.hud_camera, name="background", )
        self.background.set_draw_details(self.matsh, [], 0, 0)
        self.background.set_material(self.background_colour)

        print("start creating layers")

        text_camera = self.text_camera
        textFont = self.textFont
        flatsh = self.flatsh
        matsh = self.matsh
        hudFont = textFont        
        layer_text_spacing = self.layer_text_spacing
        
        self.dynamic_items = LayerItems()
        self.slow_items = LayerItems()
        self.static_items = LayerItems()
        self.status_items = LayerItems()
        

        # Altitude above ground
        x,y = self.grid.get_grid_pixel(15, 5)
        self.dynamic_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:+04.0f}", dataobj=self,  attr="agl", digits=4, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )
        #AGL text box
        x,y = self.grid.get_grid_pixel(16, 5)   
        self.static_items.add_item( LayerShape(Box2d(camera=self.text_camera, shader=matsh, 
                                                     line_colour=self.textbox_line_colour, fill_colour=self.textbox_fill_colour, 
                                                     w=layer_text_spacing*8, h=self.text_box_height, x=x-5, y=y, z=6, line_thickness=1, justify='C')) )
        #AGL label
        x,y = self.grid.get_grid_pixel(13, 5)
        self.static_items.add_item( LayerText(self.textFont, camera=self.text_camera, shader=self.flatsh, 
                                              text="agl", x=x, y=y, size=self.label_size, alpha=self.label_alpha) )

        
        # True airspeed number
        x,y = self.grid.get_grid_pixel(-19, 5)
        self.dynamic_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:03.0f}", dataobj=self,  attr="tas", digits=3, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )
        #True airspeed label
        x,y = self.grid.get_grid_pixel(-14, 5)
        self.static_items.add_item( LayerText(self.textFont, camera=self.text_camera, shader=self.flatsh, 
                                              text="tas", x=x, y=y, size=self.label_size, alpha=self.label_alpha) )
        # True airspeed text box
        x,y = self.grid.get_grid_pixel(-19, 5)
        self.static_items.add_item( LayerShape(Box2d(camera=self.text_camera, shader=matsh, 
                                                     line_colour=self.textbox_line_colour, fill_colour=self.textbox_fill_colour, 
                                                     w=120, h=self.text_box_height, x=x, y=y, z=6, line_thickness=1, justify='R')) )


        #Groundspeed
        x,y = self.grid.get_grid_pixel(-19, 4)
        self.dynamic_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:03.0f}", dataobj=self,  attr="groundspeed", digits=3, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )
        # Groundspeed text box
        x,y = self.grid.get_grid_pixel(-19, 4)
        self.static_items.add_item( LayerShape(Box2d(camera=self.text_camera, shader=matsh, 
                                                     line_colour=self.textbox_line_colour, fill_colour=self.textbox_fill_colour, 
                                                     w=120, h=self.text_box_height, x=x, y=y, z=6, line_thickness=1, justify='R')) )
        #groundspeed label
        x,y = self.grid.get_grid_pixel(-14, 4)
        self.static_items.add_item( LayerText(self.textFont, camera=self.text_camera, shader=self.flatsh, 
                                              text="gspd", x=x, y=y, size=self.label_size, alpha=self.label_alpha) )


        #fps
        x,y = self.grid.get_grid_pixel(-19, 6)
        self.slow_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:02.1f}", dataobj=self,  attr="av_fps", digits=4, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )
        #FPS label
        x,y = self.grid.get_grid_pixel(-14, 6)
        self.static_items.add_item( LayerText(self.textFont, camera=self.text_camera, shader=self.flatsh, 
                                              text="fps", x=x, y=y, size=self.label_size, alpha=self.label_alpha) )


        #hdop
        x,y = self.grid.get_grid_pixel(-19, -6)
        self.slow_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:02d}", dataobj=self,  attr="hdop", digits=2, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )
        #HDOP label
        x,y = self.grid.get_grid_pixel(-15, -6)
        self.static_items.add_item( LayerText(self.textFont, camera=self.text_camera, shader=self.flatsh, 
                                              text="hdop", x=x, y=y, size=self.label_size, alpha=self.label_alpha) )

        #satellites
        x,y = self.grid.get_grid_pixel(-19, -5)
        self.slow_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:02d}", dataobj=self,  attr="satellites", digits=2, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )
        #satellites label
        x,y = self.grid.get_grid_pixel(-16, -5)
        self.static_items.add_item( LayerText(self.textFont, camera=self.text_camera, shader=self.flatsh, 
                                              text="sat", x=x, y=y, size=self.label_size, alpha=self.label_alpha) )


        #flap
        x,y = self.grid.get_grid_pixel(-19, -4)
        self.slow_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:+02d}", dataobj=self,  attr="flap_pcnt", digits=3, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )

        #brake
        x,y = self.grid.get_grid_pixel(-19, -3)
        self.slow_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:+02d}", dataobj=self,  attr="brake_pcnt", digits=3, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R') )

        #Vertical speed
        x,y = self.grid.get_grid_pixel(13, 3)
        self.dynamic_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:+03.0f}", dataobj=self,  attr="vertical_speed", digits=4, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='C') )        
        # Climb rate text box
        x,y = self.grid.get_grid_pixel(13.5, 3)
        self.static_items.add_item( LayerShape(Box2d(camera=self.text_camera, shader=matsh, 
                                                     line_colour=self.textbox_line_colour, fill_colour=self.textbox_fill_colour, 
                                                     w=layer_text_spacing*5, h=self.text_box_height, x=x, y=y, z=6, line_thickness=1, justify='C')) )

        
        self.dynamic_items.add_item( LayerDynamicShape(self.VSI, phase=0) )
        
        self.dynamic_items.add_item( LayerDynamicShape(self.slip_indicator, phase=0) )
        
                #Explicit working directory path done so that profiling works correctly. Don't know why. It just is.
        pointer_path = os.path.abspath(os.path.join(self.working_directory, 'default_pointer.png'))
        
        
        # Heading number
        x,y = self.grid.get_grid_pixel(5, 5)
        self.dynamic_items.add_item( LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:3.0f}", dataobj=self,  attr="heading", digits=3, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='C') )
        #heading pointer
        x,y = self.grid.get_grid_pixel(9, 5)
        self.dynamic_items.add_item( DirectionIndicator(text_camera, self.flatsh, self.matsh, dataobj=self, attr="heading", 
                                                        x=x, y=y, z=3, pointer_img=pointer_path, phase=2) )
        #Heading text box
        x,y = self.grid.get_grid_pixel(5, 5)
        self.static_items.add_item( LayerShape(Box2d(camera=self.text_camera, shader=matsh,
                                                     line_colour=self.textbox_line_colour, fill_colour=self.textbox_fill_colour,
                                                     w=layer_text_spacing*3.5, h=self.text_box_height, x=x+5, y=y, z=6, 
                                                     line_thickness=1, justify='C')) )
        
        #Home pointer
        x,y = self.grid.get_grid_pixel(-7, 5)
        self.dynamic_items.add_item( DirectionIndicator(text_camera, self.flatsh, self.matsh, dataobj=self, attr="home", 
                                                        x=x, y=y, z=3, pointer_img=pointer_path, phase=2) )
        # Home distance number
        x,y = self.grid.get_grid_pixel(-6, 5)
        self.home_distance_number = LayerNumeric(camera=text_camera, font=textFont, shader=flatsh, alpha=self.text_alpha,
                                                 text="{:03.0f}", dataobj=self,  attr="home_dist_scaled", digits=4, phase=0,
                                                  x=x, y=y, size=self.font_size, spacing=layer_text_spacing, justify='R')
        self.dynamic_items.add_item( self.home_distance_number )
            
        # Home distance units
        x,y = self.grid.get_grid_pixel(-1, 5)
        self.status_items.add_item( LayerVarText(hudFont, text="{:s}", dataobj=self, attr="home_dist_units", camera=text_camera, shader=flatsh, x=x, y=y, z=0.5, size=0.125, phase=None) )


        #Home distance text box
        x,y = self.grid.get_grid_pixel(-2, 5)
        self.static_items.add_item( LayerShape(Box2d(camera=self.text_camera, shader=matsh,
                                                     line_colour=self.textbox_line_colour, fill_colour=self.textbox_fill_colour,
                                                     w=layer_text_spacing*8, h=self.text_box_height, x=x-5, y=y, z=6, 
                                                     line_thickness=1, justify='C')) )

        
        self.static_items.add_item( LayerShape(self.VSI.bezel) )
        self.static_items.add_item( LayerShape(self.slip_indicator.bezel) )
                
                
        #Mode status using list of text strings
        x,y = self.grid.get_grid_pixel(0, 6)
        text_strings = ["MANUAL", "AUTO", "FBW", "STABILIZE", "RTL"]
#        string=self.text, camera=self.camera, font=self.font, is_3d=False, x=self.x, y=self.y, z=self.z, size=self.size, justify='C'       
        strList = LayerStringList(hudFont, text_strings=text_strings, text_format="Mode: {:s}", alpha=self.text_alpha,
                                  camera=text_camera, dataobj=self, attr="mode", shader=flatsh,
                                  x=x, y=y, z=1, size=self.font_size, justify='C')
        self.status_items.add_item(strList)
        

        print("finished creating layers")


    def init_run(self):

        self.tick = 0
        self.av_fps = self.fps
        #i_n=0
        self.spf = 1.0 # seconds per frame, i.e. water image change
        self.next_time = time.time() + self.spf

        if self.master:
            # Fetch key presses.
            self.mykeys = pi3d.Keyboard()

        self.hud_update_frame = 0
        self.timestamp = time.clock()

#        self.frameCount = 0
        self.slow_frame_count = 0

    def run_hud(self):

        """ run the HUD main loop """
        while self.DISPLAY.loop_running():
            self.update()
            
            self.run_filters()

            self.dynamic_items.gen_items(self.hud_update_frame)

            if(self.hud_update_frame == 2):
                self.dataLayer.start_layer()               # Draw on the text layer
                self.dynamic_items.draw_items()
                self.dataLayer.end_layer()                 # stop drawing on the text layer    
            elif(self.hud_update_frame == 3):
                if(self.status_items.gen_items(phase=None)):
                    self.statusLayer.start_layer()
                    self.status_items.draw_items()
                    self.statusLayer.end_layer()
                
            elif(self.hud_update_frame == 4):
                self.ladder.gen_ladder()

                if self.static_items.gen_items():
                    self.staticLayer.start_layer()
                    self.static_items.draw_items()
                    self.ladder.draw_center()
                    self.ladder.draw_roll_indicator()
                    self.staticLayer.end_layer()

            if(self.slow_frame_count > 20):
#                if self.slow_items.gen_items(phase=None):
                self.slow_items.gen_items(phase=None)
                if True:
                    self.slowLayer.start_layer()
                    self.slow_items.draw_items()
                    self.slowLayer.end_layer()
                self.slow_frame_count = 0
            else:
                self.slow_frame_count += 1

            
      
# try glScissor for limiting extent of ladder drawing

            self.background.draw()
            self.ladder.draw_ladder(self.roll_filter.estimate(), self.pitch_filter.estimate(), 0)

            self.dataLayer.draw_layer()
            self.statusLayer.draw_layer()
            self.staticLayer.draw_layer()
            self.slowLayer.draw_layer()
  
            if time.time() > self.next_time:
                self.next_time = time.time() + self.spf
                self.av_fps = self.av_fps*0.9 + self.tick/self.spf*0.1 # exp smooth moving average
#                print(av_fps, " FPS, ", pitch, " pitch")
                self.tick = 0
    
            self.tick += 1
  
            self.hud_update_frame += 1
            if(self.hud_update_frame > self.hud_update_frames):
                self.hud_update_frame = 0
  

            #pi3d.screenshot("/media/E856-DA25/New/fr%03d.jpg" % fr)
  #          frameCount += 1

            #If master then check for keyboard press to quit
            if self.master:
                # Fetch key presses.
                self.mykeys = pi3d.Keyboard()
                k = self.mykeys.read()
                if k==27:
                    self.mykeys.close()
                    self.dataLayer.delete_buffers()
                    self.staticLayer.delete_buffers()
                    self.statusLayer.delete_buffers()
                    self.DISPLAY.destroy()
                    quit()
                    break
                elif k==112:    #p for print
                    pi3d.screenshot("hud_screenshot.jpg")
                    
            #If slave process then check for quit flag being set
            else:
                if self.quit:
                    self.dataLayer.delete_buffers()
                    self.staticLayer.delete_buffers()
                    self.statusLayer.delete_buffers()
                    self.DISPLAY.destroy()
            
    def run_filters(self):
        self.pitch_filter.observation(self.pitch, self.pitch_rate,self.attitude_timestamp* 0.001, self.system_timestamp)
        self.roll_filter.observation(self.roll, self.roll_rate,self.attitude_timestamp* 0.001, self.system_timestamp)

    def update(self):
        """" Per cycle update of all values"""
        if self.simulate:
            self.run_sim()
    
    
        if(self.update_queue is not None):
            while (self.update_queue.empty() == False):
                var_update = self.update_queue.get_nowait()
                if hasattr(self, var_update[0]):
                    setattr(self, var_update[0], var_update[1])
#                self.update_queue.task_done()
        else:
            pass
#            print("queue does not exist")

        self.home_dist_scale()
        self.channel_scale()
        
    def channel_scale(self):
        self.flap_pcnt = int((100 / 500) * (self.flap - 1510))
        self.brake_pcnt = int((100 / 500) * (self.brake - 1510))

    
    def home_dist_scale(self):
        """ Scale from home distance in meters to other scales depending on range"""
        if(self.home_dist >=1000):
            self.home_dist_scaled = self.home_dist * 0.001
            self.home_dist_units = "km"
            if(self.home_dist_scaled > 9.9):
                self.home_distance_number.textformat = "{:02.1f}"
            else:
                self.home_distance_number.textformat = "{:01.2f}"
        else:
            self.home_dist_scaled = int(self.home_dist)
            self.home_dist_units = "m"
            self.home_distance_number.textformat = "{:03.0f}"
        
    def run_sim(self):
        frametime = 1 / self.av_fps
        self.pitch += self.pitch_rate * frametime
        self.roll += self.roll_rate * frametime
        self.agl += self.vertical_speed * frametime
        self.heading += self.heading_rate * frametime
        self.tas += self.aspd_rate * frametime
        self.ias += self.aspd_rate * frametime
        self.vertical_speed =  random.randrange(-200, 200, 1)
        self.slip = float(random.randrange(-50,50)) * 0.1
        self.home += self.heading_rate * frametime
        self.home_dist += self.groundspeed *(1/3.6) * frametime
        
            
        # Temporary
        if(self.pitch > 70):
            self.pitch -= 140
        elif(self.pitch < -70):
            self.pitch += 140
        
        if(self.roll > 360):
            self.roll -= 360
        elif(self.roll < -360):
            self.roll += 360

        if(self.heading > 360):
            self.heading -= 360
        elif(self.heading < 0):
            self.heading -= 360
            
        if(self.home > 360):
            self.home -= 360
        elif(self.home < 0):
            self.home -= 360
            
if(standalone == True):
    print("=====================================================")
    print("press escape to escape")
    print("=====================================================")

    hud=HUD(True)
    hud.run_hud()
