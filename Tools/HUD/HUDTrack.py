'''
Created on 11 Jul 2014

@author: matt
'''
import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
from pi3d.shape.FlipSprite import FlipSprite
import math
import time
from ScreenGrid import ScreenScale
from Line2d import Line2d
import colorsys

rate_colour_map = ( (-40,   (0.0,0.0,1.0)),
                    (10,     (0.0,1.0,1.0)),
                    (0,     (0.0,1.0,0.0)),
                    (10,     (1.0,1.0,0.0)),
                    (40,    (1.0,0.0,0.0))   )



class HUDTrack(object):
    '''
    Responsible for creating and drawing a track on a moving map
        

    '''
    def __init__(self, camera, shader, alpha=1.0):
        '''
        Constructor
        *camera* 2d camera for drawing track map
        *shader* flatsh for drawing track segments
        '''
        from pi3d.Display import Display
        
#        self.screenSize = screenSize
        self.line_thickness = 3
        
        self.home_colour = (0,0,1.0,0.5)
        
        self.rate_colours = rate_colour_map
                       
        self.roll = 0
        self.pitch = 0
        self.heading = 0
        self.xpos = 0
        self.ypos = 0
        self.range = 500
        
        self.climbrate  = 0
        self.heading    = 0
        
        #home|tracking|follow
        self.map_mode = "follow"
        
        # 2d camera for generating sprites
        self.camera = camera    #pi3d.Camera(is_3d=False)
        self.shader = shader
        
        # camera for viewing the track. Owned by the track since it can move
        self.camera2d = pi3d.Camera(is_3d = False)
        
        self.flatsh = shader    #pi3d.Shader("uv_flat")
        self.matsh = pi3d.Shader("mat_flat")

        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
        
        self.track = OffScreenTexture("track",  w=self.screen_width, h=self.screen_height)
        self.sprite = FlipSprite(camera=camera, w=self.screen_width, h=self.screen_height, z=5, flip=True)
        
        self.inits_done = 0
        
        self.hue = 0.0       
       
    def gen_track(self):
        if self.inits_done == 0:
            self.track._start(True)
            self.draw_home()
            self.track._end()
            self.inits_done = 1
            
    def interpolate_ratio(self, ratio, y1, y2):
        delta = y2 - y1
        return (ratio * delta) + y1
        
    def interpolate(self, x, x1, x2, y1, y2):
        deltax = x2 - x1
        ratio = (x - x1) / deltax
        deltay = y2 - y1
        return (ratio * deltay) + y1
    
    def get_rate_colour(self, rate):
        colour = (1.0, 1.0, 1.0, 1.0)

        if(rate <= -20):
            colour = (0.0, 0.0, 1.0)
        elif(rate >= 20):
            colour = (1.0, 0.0, 0.0)
        else:
            hue = 0.333
            if rate >= 0:
                hue = self.interpolate(rate, 0, 20, 0.333, 0.0)
            else:
                hue = self.interpolate(rate, 0, -20, 0.666, 0.0)
            colour = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        return colour
    
       
    def add_segment(self, x, y, climbrate, heading):
        """ Draw the flight track segment"""
        if self.inits_done == 1:
            self.inits_done = 2
        elif self.inits_done == 2:
            self.track._start(False)
            rate_colour = self.get_rate_colour(climbrate)
            segment = Line2d(camera=self.camera, matsh=self.matsh, points=((x,y),(self.xpos,self.ypos)), thickness=3, colour=rate_colour )
            segment.draw()
            self.track._end()
    
        self.xpos = x
        self.ypos = y
        self.climbrate = climbrate
        self.heading = heading
        
    def draw_home(self):
        #home = pi3d.Disk(self.camera, radius=20, sides = 8, name="home" , z=5)
        #home.set_draw_details(self.matsh, [], 0, 0)
        #home.set_material(self.home_colour)
        #home.draw(self.matsh, camera=self.camera)

#        bar_shape = pi3d.Disk(camera=self.camera, radius=200, sides =12)
        bar_shape = pi3d.Plane(camera=self.camera,  w=20, h=20)
        bar_shape.set_draw_details(self.matsh, [], 0, 0)
        bar_shape.set_material(self.home_colour)
        bar_shape.position( 0,  0, 5)
        bar_shape.draw()

        
    def draw_track(self, camera=None, alpha=1):
        if(self.map_mode == "tracking"):
            camera = self.camera2d
            camera.reset()
            camera.position((self.xpos, self.ypos, 0))
        elif(self.map_mode == "follow"):
            camera = self.camera2d
            camera.reset()
            camera.rotateZ(self.heading)
            camera.position((self.xpos, self.ypos, 0))
        self.sprite.set_alpha(alpha)
        self.sprite.draw(self.shader, [self.track], camera=camera)

            
