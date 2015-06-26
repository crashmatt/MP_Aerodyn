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
        
        self.degstep = 10
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
        self.camera2d = pi3d.Camera(is_3d = False)
        
        self.flatsh = shader    #pi3d.Shader("uv_flat")
        self.matsh = pi3d.Shader("mat_flat")

        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
 
        self.bar_count = int(math.ceil(self.maxDegrees / self.degstep))
        self.pixelsPerBar = self.screenstep * self.screen_height
        
        self.bar_pixel_height = int(Display.INSTANCE.height * 0.1)

        self.bars = []
        for i in xrange(-self.bar_count,self.bar_count+1):     #(-self.bar_count,self.bar_count):
            degstep = i * self.degstep
            bar = HUDladderBar(self.camera, self.shader, degstep, ypos=int(degstep*self.pixelsPerBar/self.degstep))

            self.bars.append(bar)

        self.inits_done = 0
        
        self.center = HUDLadderCenter(self.camera, self.matsh)
        self.roll_indicator = HUDLadderRollIndicator(self.camera, self.matsh, line_thickness=3)

    def _gen_ladder(self):
        """ Generate the ladder """
        for bar in self.bars:
            bar.draw_bar()
            bar.generate_bar(font=self.font, shaders=[self.flatsh, self.matsh])
        
    def gen_ladder(self):
        if self.inits_done < 1:
            self._gen_ladder()
            self.inits_done += 1
        
       
    def draw_ladder(self, roll, pitch, yaw):
        """ Draw the ladder. roll, pitch, yaw parameters in degrees"""
        if self.inits_done > 0:
            pos=0
            rot = 0
            ypos = pitch * self.pixelsPerBar / self.degstep
            pitchrange = self.degstep * 0.5 / self.screenstep
            lowpitch = pitch - pitchrange 
            highpitch = pitch + pitchrange
            
            self.camera2d.reset()
            self.camera2d.rotateZ(roll)
            self.camera2d.position((0,ypos,0))
            
            for bar in self.bars:
                if(bar.degree < highpitch) and (bar.degree > lowpitch):
                    screenpos = (bar.degree - pitch) * self.screenstep / self.degstep
                    if(screenpos < 0):
                        screenpos = -screenpos
                    if(screenpos < self.fadingpos_start):
                        fade = self.alpha
                    elif(screenpos > self.fadingpos_end):
                        fade = 0
                    else:
                        fade = self.alpha * (screenpos - self.fadingpos_end) / (self.fadingpos_start - self.fadingpos_end) 
                        
                    bar.draw_bar(self.camera2d, alpha=fade)
                    
    def draw_center(self):
        self.center.draw()
        
    def draw_roll_indicator(self):
        self.roll_indicator.draw()



class HUDladderBar(object):
    ''' Draws a single bar in the ladder'''
    def __init__(self, camera, shader, degree, ypos, scrnheight=0.1):
        self.degree = degree

        from pi3d.Display import Display
        
        self.pixel_height = int(scrnheight * Display.INSTANCE.height)
        self.pixel_width = Display.INSTANCE.width

        #For drawing the bar
        self.camera = camera
        self.shader = shader
                
        #This is an off screen texture onto which the bar is drawn
        self.bar = OffScreenTexture("bar", h=self.pixel_height)

        # need to do offscreentexture first so its size can be used for the following.
        self.xoffset = int((self.bar.ix - Display.INSTANCE.width) * 0.5)
        self.yoffset = int((self.bar.iy - Display.INSTANCE.height) * 0.5)

        # This is the sprite onto which the texture is drawn, positioned at the correct location on the ladder
        self.sprite = pi3d.FlipSprite(camera=camera, w=self.bar.ix, h=self.bar.iy, y=ypos, z=5, flip=True)

    # The following functions return values controlling the look and feel of the bar    

    def get_bar_colour(self):
        if(self.degree == 0):
            return (255,255,255,255)
        elif(self.degree > 0):
            return (0,255,0,255)
        else:
            return (255,0,0,255)
    
    def get_bar_width(self):
        if(self.degree == 0):
            return 0.45
        else:
            return 0.35
    
    def get_bar_thickness(self):
        if(self.degree == 0):
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

#    def get_font_colour(self):
#        return (50, 200, 50, 1.0)
#        return (200, 0, 0, 1.0)


    def generate_bar(self, font, shaders=[None]):
        """ draw the bar onto the off screen texture.  Only done once.
        *shaders* is array of [flatsh, matsh]    """

        self.genshaders = shaders
        flatsh = self.genshaders[0]
        matsh = self.genshaders[1]

        self.font = font
        
        barcolour = self.get_bar_colour()
        bar_gap = self.get_bar_gap()
        fontsize = self.get_font_size()
        font_bar_gap = self.get_font_bar_gap()

        from pi3d.Display import Display
        bar_width = self.get_bar_width() * Display.INSTANCE.width
        
        self.bar._start()

        half_bar_width = self.get_bar_width() * Display.INSTANCE.width * 0.5
        gap_width = Display.INSTANCE.width * bar_gap
        bar_length = half_bar_width - gap_width
        
        bar_pattern = self.get_bar_pattern()
        dashes = bar_pattern[0]+1
        dash_separation = (bar_length / dashes)
        dash_length = dash_separation - (bar_length * bar_pattern[1] * 0.5)
        for i in xrange(0, dashes):
            dashoffset = (i * dash_separation) + (dash_length * 0.5)
            bar_shape = pi3d.Plane(camera=self.camera,  w=dash_length, h=self.get_bar_thickness())
            bar_shape.set_draw_details(matsh, [], 0, 0)
            bar_shape.set_material(barcolour)
            bar_shape.position( self.xoffset-dashoffset-(gap_width*0.5) ,  self.yoffset, 5) #
            bar_shape.draw()

            bar_shape.position( self.xoffset+dashoffset+(gap_width*0.5) ,  self.yoffset, 5) #
            bar_shape.draw()
        
        degText = "%01d" % self.degree
        degStr = pi3d.String(camera=self.camera, font=font, string=degText, size=fontsize, justify='R', is_3d=False)
        degStr.position(bar_width/2 + (font_bar_gap * self.pixel_width) + self.xoffset, self.yoffset,5)
        degStr.set_shader(flatsh)
        degStr.draw()
    
        degStr = pi3d.String(camera=self.camera, font=font, string=degText, size=fontsize, justify='C', is_3d=False)
        degStr.position((-bar_width/2) - (font_bar_gap * self.pixel_width) + self.xoffset,  self.yoffset,5)
        degStr.set_shader(flatsh)
        degStr.draw()
        
        self.bar._end()

    def draw_bar(self, camera=None, alpha=1):
        if camera == None:
            camera = self.camera

        self.sprite.set_alpha(alpha)
        self.sprite.draw(self.shader, [self.bar], camera = camera)



class HUDLadderCenter(object):
    def __init__(self, camera, matsh, colour=(255,255,255,255)):
        self.camera = camera
        self.matsh = matsh
        self.colour = colour
        
    def draw(self):
        bar_shape = pi3d.Plane(camera=self.camera,  w=3, h=20)
        bar_shape.set_draw_details(self.matsh, [], 0, 0)
        bar_shape.set_material(self.colour)
        bar_shape.position( 0,  10, 5)
        bar_shape.draw()

        bar_shape = pi3d.Plane(camera=self.camera,  w=120, h=3)
        bar_shape.set_draw_details(self.matsh, [], 0, 0)
        bar_shape.set_material(self.colour)
        bar_shape.position( 0,  0, 5)
        bar_shape.draw()


class HUDLadderRollIndicator(object):
    def __init__(self, camera, matsh, radius=0.3, line_thickness=2, line_colour=(255,255,255,255), max_angle=60, tick_angle=15, tick_len=0.025):
        self.camera = camera
        self.matsh = matsh
        self.radius = radius
        self.max_angle = max_angle
        self.tick_angle = tick_angle
        self.tick_len = tick_len
        self.line_thickness = line_thickness
        self.line_colour = line_colour
        
    def draw(self):
        grid = ScreenScale(100,100)
        points = []
        (x,rad) = grid.pos_to_pixel(self.radius, self.radius)
        (x,tlen) = grid.pos_to_pixel(self.tick_len, self.tick_len)
        
        ticks = int(self.max_angle / self.tick_angle)
        for tick in xrange(-ticks, ticks+1):
            angle = tick * self.tick_angle
            ypos = -rad * math.cos(math.radians(angle))
            xpos = rad * math.sin(math.radians(angle))
            points.append((xpos, ypos))
            
            angle += math.pi * 0.5
            typos = -tlen *  math.cos(math.radians(angle)) + ypos
            txpos =  tlen *  math.sin(math.radians(angle)) + xpos
            
            tmark = Line2d(self.camera, self.matsh, ((xpos,ypos), (txpos, typos)), self.line_thickness)
            tmark.draw()
            
        lines = Line2d(self.camera, self.matsh, points, self.line_thickness)
        lines.draw()        
            
