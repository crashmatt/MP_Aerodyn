#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals


import math, random, time, string

#import demo
import pi3d

from pi3d.constants import *

from HUDladderSimple  import HUDladder, HUDLadderRollIndicator, HUDLadderCenter
from ScreenGrid import ScreenScale
from PointFont  import PointFont
import CPlanes
import FastText

from Indicator import LinearIndicator
from Indicator import DirectionIndicator
from Indicator import RollingIndicator

import HUDConfig as HUDConfig

#from pi3dTiledMap import TiledMap
from pi3dTiledMap import Map
from pi3dTiledMap import CoordSys

import os
from multiprocessing import Queue

import fnmatch

import platform
from pi3dTiledMap.CoordSys import Cartesian
PLATFORM = platform.system()

from HUDFilters import Filter
from HUDFilters import AngleFilter

standalone = False

MAX_INPUT_COMMANDS = 8
SERVO_CENTER_RAW = 1510



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
        self.text_box_line_width = 2
        
        self.text_alpha = 1.0
        self.label_alpha = 1.0
        self.pitch_ladder_alpha = 1
        self.pitch_ladder_text_alpha = 1.0
        
        self.hud_colour = (0.0,1.0,0.0,1.0)
        self.font_colour = (0,255,0,255)
        self.textbox_line_colour = self.hud_colour
        self.textbox_fill_colour = (0.0,0.0,0.0,0.7)
        self.warning_colour = (1.0, 0.0 , 0.0, 1.0)
        
        self.values_updated = True
        
        self.fps = 20
        self.simulate = simulate
        self.master = master
                
        #Queue of attribute updates each of which is tuple (attrib, object)
        self.update_queue = update_queue
        
        self.show_track = False 
        self.show_tiled = False
        self.show_map = True

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
        
        self.input_command_raw = [SERVO_CENTER_RAW] * (MAX_INPUT_COMMANDS+1)
        self.input_command_pct = [0] * (MAX_INPUT_COMMANDS+1)
        self.input_command_inv = [False] * (MAX_INPUT_COMMANDS+1)
        
        self.hdop = 0
        self.satellites = 0
        self.aspd_rate = 1
        self.groundspeed = 0
        self.windspeed_cms = 0
        self.windspeed = 0
        self.wind_direction = 0
        self.aircraft_pos = [0.0, 0.0]  # aircraft position [lon, lat]
        self.heading = 0
        self.home_heading = 0
        self.home_direction = 0
#        self.home_dist = 0
        self.home_dist_scaled = 0
        self.home_dist_units = "m"
        self.home = [0.0, 0.0]       # home [lon, lat]
        self.home_polar = CoordSys.Polar(0.0,0.0)
        self.vertical_speed = 0
        self.asl = 0    	         #altitude above sea level
        self.agl = 0     	         #altitude above ground level
        self.ahl = 0      	        #altitude above home level
        self.slip = 0               #slip in degrees
        self.mode = "UNKNOWN"
        self.warning = ""
        self.no_link = True
        self.brakes_active = False
        self.flap_pos = ""
        
        self.link_quality = 0
        
        self.pitch_filter = AngleFilter(filter_const=5, rate_const=5, rate_gain = 0.5)
        self.roll_filter = AngleFilter(filter_const=5, rate_const=5, rate_gain = 0.0)
        
    def init_graphics(self):
        """ Initialise the HUD graphics """

# Setup display and initialise pi3d
#       if (platform.system() == PLATFORM_PI):
#        	self.DISPLAY = pi3d.Display.create(x=20, y=0, w=700, h=580, frames_per_second=self.fps)
#        else: 
#          	self.DISPLAY = pi3d.Display.create(x=0, y=0, w=640, h=480, frames_per_second=self.fps)
   
#        self.DISPLAY = pi3d.Display.create(x=20, y=0, w=700, h=580, frames_per_second=self.fps, use_pygame=True, samples=4, fullscreen=True, no_frame=False)
        self.DISPLAY = pi3d.Display.create(x=20, y=0, w=640, h=480, frames_per_second=self.fps, use_pygame=True, samples=4, fullscreen=True, no_frame=False)

        self.DISPLAY.set_background(0.0, 0.0, 0.0, 0)      # r,g,b,alpha
        
        self.background_colour=(0,0,0,255)
        self.background_distance=2000
        
        self.grid = ScreenScale(0.025,0.075)

        self.fpv_camera = pi3d.Camera.instance()
        self.text_camera = pi3d.Camera(is_3d=False)
        self.hud_camera = self.text_camera

        #setup textures, light position and initial model position

        #create shaders
        #shader = pi3d.Shader("uv_reflect")
        self.sh2d =  pi3d.Shader("2d_flat")   #For fixed color
#        self.matsh = pi3d.Shader("mat_flat")  #For fixed color
        self.matsh = pi3d.Shader("norm_colour")  #For shapes with normal modulated colour and uv modulated alpha
        self.flatsh = pi3d.Shader("uv_flat")

        #Create layers
        self.bitsnpieces = CPlanes.CPlanes(camera=self.hud_camera, x=0, y=0, z=0)
        self.bitsnpieces.set_draw_details(self.matsh, [], 0, 0)

        #Create textures

        print("start creating fonts")
        #fonts
        font_path = os.path.abspath(os.path.join(self.working_directory, 'fonts', 'FreeSansBold.ttf'))
#        self.warningFont = pi3d.Font(font_path, (255,0,0,255))
        self.pointFont = PointFont(font_path, self.font_colour)
        self.hud_text = FastText.FastText(self.pointFont, self.text_camera)

        print("end creating fonts")
        
        print("start creating indicators")
        #Explicit working directory path done so that profiling works correctly. Don't know why. It just is.
        needle_path = os.path.abspath(os.path.join(self.working_directory, 'default_needle.img'))

        x,y = self.grid.get_grid_pixel(-15, 0)
        self.VSI = RollingIndicator(self.text_camera, self.flatsh, self.matsh, self, "vertical_speed", 
                                   indmax=20, indmin=-20, x=x, y=y, z=3, width=30, length=180, 
                                   orientation="V", line_colour=(1.0, 1.0, 1.0, 1.0), fill_colour=(0,0,0,0.75), 
                                   line_thickness = 1, needle_img=None, needle_thickness=8, needle_colour=self.hud_colour)

        #Add slip indicator.  Scale is in degrees
        x,y = self.grid.get_grid_pixel(0, -5)
        self.slip_indicator = LinearIndicator(self.text_camera, self.flatsh, self.matsh, self, "slip", 
                                              indmax=50, indmin=-50, x=x, y=y, z=3, width=21, length=250, 
                                              orientation="H", line_colour=(1.0, 1.0, 1.0, 1.0), fill_colour=(0,0,0,0.75), 
                                              line_thickness = 1, needle_img=needle_path)
        print("end creating indicators")


        print("start creating ladder")
        self.ladder = HUDladder(font=self.pointFont, camera=self.hud_camera, shader=self.flatsh, alpha=self.pitch_ladder_alpha)
        print("end creating ladder")

        print("Create static HUD shapes")
        rollindicator = HUDLadderRollIndicator(camera=None, matsh=None, radius=0.35, line_thickness=3, tick_len=0.02, line_colour=(0.9,0.9,0.9,0.8), standalone=False)
        rollindicator.generate(self.bitsnpieces)
        
        ladderCenter = HUDLadderCenter(camera=None, matsh=None, colour=(1.0, 0.0, 1.0, 1.0), standalone=False)
        ladderCenter.generate(self.bitsnpieces)

        print("Create track map")
        if self.show_map:
            self.track_map = Map.Map(w=512, h=512, z=6.0, alpha=0.95)

        self.background = pi3d.Plane(w=self.DISPLAY.width, h=self.DISPLAY.height, z=self.background_distance,
                                camera=self.hud_camera, name="background", )
        self.background.set_draw_details(self.matsh, [], 0, 0)
        self.background.set_material(self.background_colour)

        print("start creating layers")

#        normsh = self.normsh
        layer_text_spacing = self.layer_text_spacing
        
        print("start creating layer items")
        
        # Altitude above ground
        x,y = self.grid.get_grid_pixel(-17, 3)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 4, self, "agl", "{:+04.0f}", self.font_size*1.5*4.0, "C", 0.5)
        self.hud_text.add_text_block(text_block)

        #AGL text box
        x,y = self.grid.get_grid_pixel(-17.5, 3)   
        self.bitsnpieces.add_filled_box(layer_text_spacing*6*1.2, self.text_box_height*1.5, x-5.0, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "R")

        #AGL label
        
        # True airspeed number
        x,y = self.grid.get_grid_pixel(12, 3)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 3, self, "tas", "{:03.0f}", self.font_size*1.5*4.0, "C", 0.5)
        self.hud_text.add_text_block(text_block)
      
        #True airspeed label

        # True airspeed text box
        x,y = self.grid.get_grid_pixel(11, 3)
        self.bitsnpieces.add_filled_box(layer_text_spacing*6*1.2, self.text_box_height*1.5, x, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "R")


        #Groundspeed
        x,y = self.grid.get_grid_pixel(12, -4)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 3, self, "groundspeed", "{:03.0f}", self.font_size*4, "C", 0.5)
        self.hud_text.add_text_block(text_block)
        
        # Groundspeed text box
        x,y = self.grid.get_grid_pixel(11, -4)
        self.bitsnpieces.add_filled_box(layer_text_spacing*6*1.2, self.text_box_height*1.5, x, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "R")
        
        #groundspeed label
        x,y = self.grid.get_grid_pixel(15.25, -4)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 4, None, None, "gspd", self.label_size*3.0, "F", 0.01)
        self.hud_text.add_text_block(text_block)


        #fps
        x,y = self.grid.get_grid_pixel(-15, -6)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "av_fps", "{:2.0f}", self.font_size*4*0.75, "C", 0.5)
        self.hud_text.add_text_block(text_block)
        
        #FPS label
        x,y = self.grid.get_grid_pixel(-18, -6)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 4, None, None, "f ps", self.label_size*4.0, "M", 1.0)
        self.hud_text.add_text_block(text_block)


        #link quality
        x,y = self.grid.get_grid_pixel(-16, -4.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 3, self, "link_quality", "{:3d}", self.font_size*4*0.75, "C", 0.5)
        self.hud_text.add_text_block(text_block)
        
        #Link label
        x,y = self.grid.get_grid_pixel(-18, -4.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 5, None, None, "l oss", self.label_size*4.0, "M", 1.0)
        self.hud_text.add_text_block(text_block)


        #hdop
        x,y = self.grid.get_grid_pixel(-15, -5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "hdop", "{:2d}", self.font_size*4*0.75, "C", 0.5)
        self.hud_text.add_text_block(text_block)
                
        #HDOP label
        x,y = self.grid.get_grid_pixel(-18.5, -5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 4, None, None, "hdop", self.label_size*4.0, "M", 1.1)
        self.hud_text.add_text_block(text_block)

        #satellites
        x,y = self.grid.get_grid_pixel(-15, -5.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "satellites", "{:2d}", self.font_size*4*0.75, "C", 0.5)
        self.hud_text.add_text_block(text_block)

        #satellites label
        x,y = self.grid.get_grid_pixel(-18, -5.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 3, None, None, "sat", self.label_size*4.0, "M", 1.0)
        self.hud_text.add_text_block(text_block)


        #flap
        x,y = self.grid.get_grid_pixel(15, -5.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "input_command_pct[6]", "{:+02d}", self.font_size*4*0.75, "C", 0.5)
        self.hud_text.add_text_block(text_block)
        
        self.input_command_inv[6] = True
        #Flap label
        x,y = self.grid.get_grid_pixel(18, -5.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 1, None, None, "F", self.label_size*4.0, "M", 1.1)
        self.hud_text.add_text_block(text_block)


        #brake
        x,y = self.grid.get_grid_pixel(15, -6)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "input_command_pct[7]", "{:+02d}", self.font_size*4*0.75, "C", 0.5)
        self.hud_text.add_text_block(text_block)
        
        #Brake label
        x,y = self.grid.get_grid_pixel(18, -6)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 1, None, None, "B", self.label_size*4.0, "M", 1.1)
        self.hud_text.add_text_block(text_block)

        # Vertical speed
        x,y = self.grid.get_grid_pixel(-16, -3)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 4, self, "vertical_speed", "{:+03.0f}", self.font_size*1.5*4.0, "C", 0.5)
        self.hud_text.add_text_block(text_block)


        # Climb rate text box
        x,y = self.grid.get_grid_pixel(-14, -3)
        self.bitsnpieces.add_filled_box(layer_text_spacing*6*1.2, self.text_box_height*1.5, x, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "C")

#        self.dynamic_items.add_item( LayerDynamicShape(self.VSI, phase=0) )
#        self.static_items.add_item( LayerShape(self.VSI.bezel) )

        
#        self.dynamic_items.add_item( LayerDynamicShape(self.slip_indicator, phase=0) )
#        self.static_items.add_item( LayerShape(self.slip_indicator.bezel) )
        
        #Explicit working directory path done so that profiling works correctly. Don't know why. It just is.
        pointer_path = os.path.abspath(os.path.join(self.working_directory, 'default_pointer.png'))
        
        
        # Heading number
        x,y = self.grid.get_grid_pixel(5, 5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 3, self, "heading", "{:03.0f}", self.font_size*4, "C", 0.5)
        self.hud_text.add_text_block(text_block)

        #heading pointer
#        x,y = self.grid.get_grid_pixel(9, 5)
#        self.dynamic_items.add_item( DirectionIndicator(text_camera, self.flatsh, self.matsh, dataobj=self, attr="heading", 
#                                                        x=x, y=y, z=3, pointer_img=pointer_path, phase=2) )

        #Heading text box
        x,y = self.grid.get_grid_pixel(5, 5)
        self.bitsnpieces.add_filled_box(layer_text_spacing*6*1.2, self.text_box_height, x+5.0, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "C")
        
        #Home pointer
#        x,y = self.grid.get_grid_pixel(-8, 5)
#        self.dynamic_items.add_item( DirectionIndicator(text_camera, self.flatsh, self.matsh, dataobj=self, attr="home_direction", 
#                                                        x=x, y=y, z=3, pointer_img=pointer_path, phase=2) )

        # Home distance number
        x,y = self.grid.get_grid_pixel(-5, 5)
        self.home_distance_number = FastText.TextBlock(x, y, 1.0, 0.0, 4, self, "home_dist_scaled", "{:03.0f}", self.font_size*4, "C", 0.5)
        self.hud_text.add_text_block(self.home_distance_number)
        
        # Home distance units
        x,y = self.grid.get_grid_pixel(-1, 5)
#        self.status_items.add_item( LayerVarText(hudFont, text="{:s}", dataobj=self, attr="home_dist_units", camera=text_camera, shader=flatsh, x=x, y=y, z=0.5, size=0.125, phase=None) )
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "home_dist_units", "{:s}", self.label_size*4.0, "M", 1.1)
        self.hud_text.add_text_block(text_block)
        
        #Home distance text box
        x,y = self.grid.get_grid_pixel(-2, 5)
        self.bitsnpieces.add_filled_box(layer_text_spacing*6*1.2, self.text_box_height, x-5.0, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "C")


        
        #Wind pointer
#        x,y = self.grid.get_grid_pixel(12, 4.5)
#        self.slow_items.add_item( DirectionIndicator(text_camera, self.flatsh, self.matsh, dataobj=self, attr="wind_direction", 
#                                                        x=x, y=y, z=3, pointer_img=pointer_path, phase=2) )
        # Windspeed number
        x,y = self.grid.get_grid_pixel(14, 4.5)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 2, self, "windspeed", "{:2.0f}", self.font_size*1.5*4.0, "C", 0.5)
        self.hud_text.add_text_block(text_block)
        
        # Windspeed text box
        x,y = self.grid.get_grid_pixel(14, 4.5)
        self.bitsnpieces.add_filled_box(layer_text_spacing*3*1.5, self.text_box_height*1.5, x-5.0, y, 1.0, self.textbox_fill_colour, self.textbox_line_colour, self.text_box_line_width, "R")
        
        
        #Mode status
        x,y = self.grid.get_grid_pixel(10, 6)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 9, self, "mode", "{:s}", self.font_size*4.0, "F", 0.06, self.text_alpha)
        self.hud_text.add_text_block(text_block)
        
        #Warning status
        x,y = self.grid.get_grid_pixel(-5, 6)
        text_block = FastText.TextBlock(x, y, 1.0, 0.0, 10, self, "warning", "{:s}", self.font_size*4.0, "F", 0.06, self.text_alpha)
        self.hud_text.add_text_block(text_block)

        
        self.bitsnpieces.init()

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
        

    def run_hud(self):

        """ run the HUD main loop """
        while self.DISPLAY.loop_running():
            self.update()
             
            self.run_filters()
             
            if self.show_map:
                self.track_map.add_segment()
                if(self.hud_update_frame == 4):
                    self.track_map.gen_map()

            self.ladder.draw_ladder(self.roll_filter.estimate(), self.pitch_filter.estimate(), 0)
      
            if self.show_map:
                self.track_map.draw()
                
            self.background.draw()
            
            if self.values_updated:
                self.hud_text.regen()
                self.values_updated = False
                
            self.bitsnpieces.draw()
            
            self.hud_text.draw()

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
                    self.DISPLAY.destroy()
                    quit()
                    break
                elif k==112:    #p for print
                    pi3d.screenshot("hud_screenshot.jpg")
                    
            #If slave process then check for quit flag being set
            else:
                if self.quit:
                    self.staticLayer.delete_buffers()
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
                if('[' in var_update[0]):
                    update_parts = var_update[0].split('[')
                    if(len(update_parts) == 2):
                        if hasattr(self, update_parts[0]):
                            thearray = getattr(self, update_parts[0])
                            index = int(update_parts[1].replace("]", ""))
                            thearray[index] = var_update[1]
#                            setattr(self, "input_command_raw"[:index], var_update[1])
                            
                else:
                    if hasattr(self, var_update[0]):
                        setattr(self, var_update[0], var_update[1])
                        if var_update[0] == "home":
                            if self.show_map:
                                self.track_map.set_map_origin(var_update[1])
#                self.update_queue.task_done()
                self.values_updated = True
        else:
            pass
#            print("queue does not exist")

        self.update_maps()
        self.home_dist_scale()
        self.channel_scale()
        self.calc_home_direction()
        self.brake_condition()
        self.flap_condition()
        self.windspeed_scale()
        self.status_condition()
        
    def update_maps(self):
        if self.show_tiled or self.show_map:
            pos = Cartesian(polar=self.home_polar.reverse())
            self.track_map.set_map_focus(pos)
            self.track_map.set_aircraft_pos(pos)
            self.track_map.set_climbrate(self.vertical_speed)
            if self.flap_pos == "FLAP DOWN":
                self.track_map.set_zoom_target(1.5, 1.0)
            elif self.flap_pos == "FLAP UP":
                self.track_map.set_zoom_target(0.75, 1.0)
            else:
                self.track_map.set_zoom_target(1.0, 1.0)
        
    def windspeed_scale(self):
        self.windspeed = self.windspeed_cms * 0.01
        
    def status_condition(self):
        if(self.no_link):
            self.warning = "NO LINK"
        if(self.link_quality > 30):
            self.warning = "LINK WARN"
        elif(self.brakes_active == True):
            self.warning = "BRAKES"
        elif(self.flap_pos != ""):
            self.warning = self.flap_pos
        else:
            self.warning = ""
            
    def flap_condition(self):
        if(self.input_command_pct[6] > 5):
            self.flap_pos = "FLAP DOWN"
        elif(self.input_command_pct[6] < -5):            
            self.flap_pos = "FLAP UP"
        else:
            self.flap_pos = ""
        
        
    def brake_condition(self):
        if(self.input_command_pct[7] > 5):
            self.brakes_active = True
        else:
            self.brakes_active = False
        
        
    def calc_home_direction(self):
        self.home_heading = self.home_polar.angle + 180
        self.home_direction = self.home_heading - self.heading
        if(self.home_direction > 360):
            self.home_direction = self.home_direction - 360
        elif(self.home_direction < -360):
            self.home_direction = self.home_direction + 360
        
    def channel_scale(self):
        for channel in range(0,MAX_INPUT_COMMANDS):
            self.input_command_pct[channel] = int((100 / 500) * (self.input_command_raw[channel] - SERVO_CENTER_RAW))
            if(self.input_command_inv[channel]):
                self.input_command_pct[channel] = -self.input_command_pct[channel]
    
    def home_dist_scale(self):
        """ Scale from home distance in meters to other scales depending on range"""
        home_dist = self.home_polar.distance
        if(home_dist >=1000):
            self.home_dist_scaled = home_dist * 0.001
            self.home_dist_units = "km"
            if(self.home_dist_scaled > 9.9):
                self.home_distance_number.text_format = "{:02.1f}"
            else:
                self.home_distance_number.text_format = "{:01.2f}"
        else:
            self.home_dist_scaled = int(home_dist)
            self.home_dist_units = "m"
            self.home_distance_number.text_format = "{:03.0f}"
        
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
