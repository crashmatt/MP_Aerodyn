'''
Created on 11 Jul 2014

@author: matt
'''
import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
import math
import time
from ScreenGrid import ScreenScale
from Line2d import Line2d

class HUDTrack(object):
    '''
    Responsible for creating and drawing a track on a moving map
        

    '''

    def __init__(self, font, camera, shader, alpha=1.0):
        '''
        Constructor
        *camera* 2d camera for drawing ladder sprites
        *shader* flatsh for drawing ladder bars
        '''
        from pi3d.Display import Display
        
#        self.screenSize = screenSize
        self.font = font
        self.line_thickness = 3
               
        self.roll = 0
        self.pitch = 0
        self.heading = 0
        self.xpos = 0
        self.ypos = 0
        self.range = 500
        
        # 2d camera for generating sprites
        self.camera = camera    #pi3d.Camera(is_3d=False)
        self.shader = shader
        
        # camera for viewing the placed sprites. Owned by the track since it moves
        self.camera2d = pi3d.Camera(is_3d = False)
        
        self.flatsh = shader    #pi3d.Shader("uv_flat")
        self.matsh = pi3d.Shader("mat_flat")

        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
        
        self.track = OffScreenTexture("track", h=self.range, w=self.range)
        
        self.inits_done = 0
       
       
    def add_segment(self, x, y, colour):
        """ Draw the flight track segment"""
        if self.inits_done > 0:                   
            self.track._start(False)
            segment = Line2d(self.camera, self.matsh, ((self.xpos,self.ypos), (x, y)), self.line_thickness)
            segment.set_draw_details(self.matsh, [], 0, 0)
            segment.set_material(colour)
            segment.draw()
        else:
            self.track._start(True)
            home = pi3d.Disk(self.camera, radius=20, sides = 8, name="home" , z=5)
            self.inits_done = 1
    
        self.xpos = x
        self.ypos = y
        self.track._end()
        
    def draw_item:
        
      
            
