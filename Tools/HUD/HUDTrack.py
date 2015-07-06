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

rate_colour_map = ( (-20,   (0,0,1.0,1.0)),
#                    (0,     (0.5,0.5,0.5,1.0)),
                    (20,    (1.0,0,0,1.0))     )



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

        #------------------------- self.rate_colours = ( (-20,   (0,0,255,255)),
                    #------------------------------- (0,     (200,200,200,255)),
                    #------------------------------ (20,    (255,0,0,255))     )
        
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
        
       
    def gen_track(self):
        if self.inits_done == 0:
            self.track._start(True)
            self.draw_home()
            self.track._end()
            self.inits_done = 1
    
    def get_rate_colour(self, rate):
        colour = (1.0, 1.0, 1.0, 1.0)
        rate_colour_count = len(self.rate_colours)
        if(rate <= self.rate_colours[0][0]):
            colour = self.rate_colours[0][1]
        elif(rate >= rate_colour_count):
            colour = self.rate_colours[rate_colour_count-1][1]
        else:
            last_rcolour = self.rate_colours[0]
            for rcolour in self.rate_colours:
                if (rcolour[0] >= rate) and (last_rcolour[0] < rate):
                    delta_rate = rcolour[0] - last_rcolour[0]
                    delta_red = rcolour[1][0] - last_rcolour[1][0]
                    delta_grn = rcolour[1][1] - last_rcolour[1][1]
                    delta_blue = rcolour[1][2] - last_rcolour[1][2]
                    ratio = (rate - last_rcolour[0]) / delta_rate
                    red = last_rcolour[1][0] + (delta_red * ratio)
                    green = last_rcolour[1][1] + (delta_grn * ratio)
                    blue = last_rcolour[1][2] + (delta_blue * ratio)
                    colour = (red, green, blue, 1.0)
                last_rcolour = rcolour          
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

            
