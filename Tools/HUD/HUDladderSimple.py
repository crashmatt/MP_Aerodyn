'''
Created on 11 Jul 2014

@author: matt
'''
import pi3d
from CLines import CLines
import math
import time
from ScreenGrid import ScreenScale
import numpy as np
import CPlanes

class HUDladder(object):
    '''
    Responsible for creating and drawing a HUD pitch ladder according to aircraft attitude
    
    Uses a HUDLadderBar object to draw individual bars of the ladder
    Places the bars as sprites in the ladder pattern
    Does ladder movement by moving and rotating the camera
    
    Owns the HUDLadderCenter object that draws the static aircraft marker. It does not draw it as
    part of the ladder since it does not move and it can be drawn on a static layer
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
               
        self.roll = 0
        self.pitch = 0
        self.heading = 0
        self.track = 0
        
        self.degstep = 20
        self.screenstep = 0.3           # ratio of screen height
        self.bar_gap = 0.05             # ratio of screen width
        self.font_scale = 0.08          # relative to original font size
        self.font_bar_gap = 0.07        # ratio of screen width
        self.alpha = alpha              # 0 to 255?
        self.maxDegrees = 80
        self.fadingpos_start = 0.25
        self.fadingpos_end = 0.4
        
        
        # 2d camera for generating sprites
        self.camera = camera    #pi3d.Camera(is_3d=False)
        self.shader = shader
        
        # camera for viewing the placed sprites. Owned byt the ladder since it moves
#        self.camera2d = pi3d.Camera(is_3d = False)
        
#       self.flatsh = shader    #pi3d.Shader("uv_flat")
        self.matsh = pi3d.Shader("mat_flat")
        self.normsh = pi3d.Shader("norm_colour_fade")

        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
 
        self.bar_count = int(math.ceil(self.maxDegrees / self.degstep))
        self.pixelsPerBar = self.screenstep * self.screen_height
        
#        self.center = HUDLadderCenter(self.camera, self.matsh)
#        self.roll_indicator = HUDLadderRollIndicator(self.camera, self.matsh, line_thickness=3, standalone=True)
        
        self.ladder = CPlanes.CPlanes(camera=camera, x=0, y=0, z=0)

        self.bar_shader = pi3d.Shader(vshader_source = """
precision mediump float;
attribute vec3 vertex;
attribute vec3 normal;
uniform mat4 modelviewmatrix[2];
uniform vec3 unib[4];
varying vec3 vars[2];

void main(void) {
  gl_Position = modelviewmatrix[1] * vec4(vertex, 1.0);
  gl_PointSize = unib[2][2];
  vars[0][0] = length(gl_Position.xy);
  vars[1] = normal;
}
""",
fshader_source = """
precision mediump float;
uniform vec3 unib[4];
uniform vec3 unif[20];
varying vec3 vars[2];

void main(void) {
  gl_FragColor = vec4( vars[1], 1.0 ); 
  gl_FragColor.a = clamp(1.2-vars[0][0], 0.1, 0.8) * unif[5][2];
}
""")

        half_ladder_steps = int(math.ceil(90.0 / self.degstep))
        
        for step in range(0, (2*half_ladder_steps) + 2):
            bar = (step - half_ladder_steps) 
            angle = bar * self.degstep
            ypos = angle * self.pixelsPerBar / self.degstep
            width = self.screen_width * self.get_bar_width(angle)
            colour = self.get_bar_colour(angle)
            thickness = self.get_bar_thickness(angle)
            
            self.ladder.add_filled_box(width, thickness, 0.0, ypos, 5.5, colour, (0.0, 0.0, 0.0, 0.8), thickness)
            
        self.ladder.set_draw_details(self.normsh, [], 0, 0)
        self.ladder.init()
       
       
    def draw_ladder(self, roll, pitch, yaw):
        """ Draw the ladder. roll, pitch, yaw parameters in degrees"""
        pixel_pitch = -pitch * self.pixelsPerBar / self.degstep
        ypos = pixel_pitch * math.cos(math.radians(roll))
        xpos = -pixel_pitch * math.sin(math.radians(roll))
        self.ladder.rotateToZ(roll)
        self.ladder.position(xpos, ypos, 0.0)
        self.ladder.draw()
        
#------------------------------------------------------------------------------ 
            #--------------------------------------------- for bar in self.bars:
                #------- if(bar.degree < highpitch) and (bar.degree > lowpitch):
                    # screenpos = (bar.degree - pitch) * self.screenstep / self.degstep
                    #---------------------------------------- if(screenpos < 0):
                        #-------------------------------- screenpos = -screenpos
                    #--------------------- if(screenpos < self.fadingpos_start):
                        #------------------------------------- fade = self.alpha
                    #--------------------- elif(screenpos > self.fadingpos_end):
                        #---------------------------------------------- fade = 0
                    #----------------------------------------------------- else:
                        # fade = self.alpha * (screenpos - self.fadingpos_end) / (self.fadingpos_start - self.fadingpos_end)
#------------------------------------------------------------------------------ 
                    #-------------------- bar.draw_bar(self.camera2d, alpha=1.0)
                    
    def gen_ladder(self):
        pass
                    
    def draw_center(self):
        pass
#        self.center.draw()
        
    def draw_roll_indicator(self):
        pass
#        self.roll_indicator.draw()


    # The following functions return values controlling the look and feel of the bar    

    def get_bar_colour(self, angle):
        if(angle == 0):
            return (1.0, 1.0, 1.0, 1.0)
        elif(angle > 0):
            return (0.0, 1.0, 0.0, 1.0)
        else:
            return (1.0, 0.0, 0.0, 1.0)
        
    def get_bar_hue(self, angle):
        if(angle == 0):
            return 0.5
        elif(angle > 0):
            return 0
        else:
            return 1.0
        
    
    def get_bar_width(self, angle):
        if(angle == 0):
            return 0.45
        else:
            return 0.35
    
    def get_bar_thickness(self, angle):
        if(angle == 0):
            return 6
        else:
            return 4
        
    def get_bar_gap(self):
        return 0.06
    
    def get_font_size(self):
        if(self.degree == 0):
            return 0.2
        else:
            return 0.175
    
    def get_font_bar_gap(self):
        return 0.03
    
    def get_bar_pattern(self):
        """ return a tuple (gaps, gap_size) describing line pattern"""
        if(self.degree >= 0):
            return (0, 0)
        else:
            return (2, 0.25)



class HUDLadderCenter(object):
    def __init__(self, camera, matsh, colour=(1.0,1.0,1.0,1.0), standalone=False):
        
        self.z=1.0
        self.colour = colour

        if standalone:
            self.camera = camera
            self.normsh = pi3d.Shader("norm_colour")
            self.center = CPlanes.CPlanes(camera=camera, x=0, y=0, z=0) 
            self.center.set_alpha(1.0)
            self.center.set_draw_details(self.normsh, [], 0, 0)
            
            self.generate(self.center)
            self.center.init()
        
    
    def generate(self, planes):
        """
        *plane*: A CPlanes object to add the shape to 
        """
        planes.add_line((0.0, 0.0, self.z), (0, 20.0 ,self.z), 4, self.colour)
        planes.add_line((-60.0, 0.0, self.z), (60.0, 0.0 ,self.z), 4, self.colour)
        
    def draw(self):
        if standalone:
            self.center.draw()


class HUDLadderRollIndicator(object):
    def __init__(self, camera, matsh, radius=0.3, line_thickness=2, line_colour=(1.0,1.0,1.0), max_angle=60, tick_angle=15, tick_len=0.025, alpha=0.8, standalone=False):
        self.radius = radius
        self.max_angle = max_angle
        self.tick_angle = tick_angle
        self.tick_len = tick_len
        self.line_thickness = line_thickness
        self.line_colour = line_colour
        self.alpha = alpha
        self.standalone = standalone

        if self.standalone:      
            self.normsh = pi3d.Shader("norm_colour")
            self.indicator = CPlanes.CPlanes(camera=camera, x=0, y=0, z=0)
            self.indicator.set_draw_details(self.normsh, [], 0, 0)
            self.generate(self.indicator)
            self.indicator.init()
            self.indicator.set_alpha(self.alpha)


    def generate(self, planes, grid_size=100):
        """
        *plane*: A CPlanes object to add the shape to 
        """
        grid = ScreenScale(grid_size, grid_size)
        points = []
        (x,rad) = grid.pos_to_pixel(self.radius, self.radius)
        (x,tlen) = grid.pos_to_pixel(self.tick_len, self.tick_len)
        
        ticks = int(self.max_angle / self.tick_angle)
        for tick in xrange(-ticks, ticks+1):
            angle1 = tick * self.tick_angle
            ypos1 = -rad * math.cos(math.radians(angle1))
            xpos1 = rad * math.sin(math.radians(angle1))

            angle2 = (tick + 1) * self.tick_angle
            ypos2 = -rad * math.cos(math.radians(angle2))
            xpos2 = rad * math.sin(math.radians(angle2))
            
            z=0

            if(tick < ticks):
                planes.add_line((xpos1,ypos1,z), (xpos2, ypos2,z), self.line_thickness, self.line_colour)
            
            angle1 += math.pi * 0.5
            typos = -tlen *  math.cos(math.radians(angle1)) + ypos1
            txpos =  tlen *  math.sin(math.radians(angle1)) + xpos1
            
            planes.add_line((xpos1,ypos1,z), (txpos, typos,z), self.line_thickness, self.line_colour)
                    

    def draw(self):
        if self.standalone:
            self.indicator.draw()
