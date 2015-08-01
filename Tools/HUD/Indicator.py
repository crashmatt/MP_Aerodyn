'''
Created on 27 Jul 2014

@author: matt
'''

from Box2d import Box2d
import pi3d
from gettattra import *
from LayerItems import LayerItem

class Indicator(LayerItem):
    '''
    Indicator base class
    '''

    def __init__(self, dataobj, attr, x=0, y=0, phase=None, indmax=1, indmin=0, z=1, camera=None, shader=None ):
        '''
        Constructor
        *dataobj* is the object that the data pointer uses to show data
        *attr* is the attribute name in the object
        '''
        super(Indicator, self).__init__(camera=camera, shader=shader, x=x, y=y, phase=phase)
        
        self.dataobj = dataobj
        self.attr = attr
        
        self.indmax = indmax
        self.indmin = indmin
        self.z = z
        
        self.value = getattra(self.dataobj, self.attr, None)
        self.bezel=None
                
    def draw_bezel(self):
        self.bezel.draw()

        

class LinearIndicator(Indicator):
    def __init__(self, camera, flatsh, matsh, dataobj, attr, indmax=1, indmin=0, x=0, y=0, z=3, 
                 width=20, length=100, orientation="V",
                 line_colour=(255,255,255,255), fill_colour=(0,0,0,255), line_thickness = 1, 
                 needle_img="default_needle.jpg", phase=0, tick_spacing=0.5): #default_needle.img
        '''
        *width* width of the indicator
        *length* length of the indicator
        *orientation* 'V' for vertical 'H' for horizontal
        length and width is rotated with orientation
        '''
        super(LinearIndicator, self).__init__(dataobj, attr, x=x, y=y, phase=phase, indmax=indmax, indmin=indmin, z=z, camera=camera, shader=matsh )
        
        self.width = width
        self.length = length
        self.orientation = orientation
        self.line_colour = line_colour
        self.fill_colour = fill_colour
        self.line_thickness = line_thickness
        self.camera = camera
        self.matsh = matsh
        self.flatsh = flatsh
        self.x = x
        self.y = y
        self.z = z
        
        if(orientation=="H"):
            width = self.length
            height = self.width
            rot = 90
        else:
            width = self.width
            height = self.length
            rot = 0
            
        self.bezel = Box2d(camera=self.camera, w=width, h=height, d=1.0,
                         x=self.x, y=self.y, z=self.z,
                         line_colour=self.line_colour, fill_colour=self.fill_colour, 
                         line_thickness=self.line_thickness,  shader=matsh, justify='C')

        self.needle_texture = pi3d.Texture(needle_img)
        
        self.needle = pi3d.ImageSprite(camera=self.camera, texture=self.needle_texture, shader=flatsh, 
                                       w=self.needle_texture.ix, h=self.needle_texture.iy, 
                                       x=self.x, y=self.y, z=0.5, rz=rot, name="needle")
        
    def value_to_deltapos(self, value):
        """ travel limited position on the indicator"""
        indrange = float(self.indmax - self.indmin)
        deltapos = (( float(self.value - self.indmin) / indrange) * self.length) - (self.length * 0.5)

       #limit travel to meter endpoints
        if(deltapos > (self.length * 0.5)):
            deltapos = (self.length * 0.5)
        elif(deltapos < (self.length * -0.5)):
            deltapos = (self.length * -0.5)
        
        return deltapos

        
    def gen_item(self):
        self.value = getattra(self.dataobj, self.attr, None)
        indrange = float(self.indmax - self.indmin)
        deltapos = (( float(self.value - self.indmin) / indrange) * self.length) - (self.length * 0.5)

        #limit travel to meter endpoints
        if(deltapos > (self.length * 0.5)):
            deltapos = (self.length * 0.5)
        elif(deltapos < (self.length * -0.5)):
            deltapos = (self.length * -0.5)

        if(self.orientation == "H"):
            self.needle.positionX(self.x + deltapos)
        else:
            self.needle.positionY(self.y + deltapos)
        self.changed = True
        
        
    def draw(self):
        self.needle.draw()
        self.changed = False
        
        
        
class DirectionIndicator(Indicator):
    def __init__(self, camera, flatsh, matsh, dataobj, attr, x=0, y=0, z=3,
                 pointer_img="default_pointer.jpg", phase=0):
        
        super(DirectionIndicator, self).__init__(dataobj, attr, x=x, y=y, phase=phase, indmax=360, indmin=0, z=z, camera=camera, shader=matsh )

        self.pointer_texture =  pi3d.Texture(pointer_img)
        
        self.pointer = pi3d.ImageSprite(camera=self.camera, texture=self.pointer_texture, shader=flatsh, 
                                       w=self.pointer_texture.ix, h=self.pointer_texture.iy, 
                                       x=self.x, y=self.y, z=0.5, name="pointer")
        
    def gen_item(self):
        self.value = getattra(self.dataobj, self.attr, None)
        indrange = float(self.indmax - self.indmin)
        
        #limit travel to meter endpoints
#        if(deltapos > (self.length * 0.5)):
#            deltapos = (self.length * 0.5)
#        elif(deltapos < (self.length * -0.5)):
#            deltapos = (self.length * -0.5)

        self.pointer.rotateToZ(-self.value)
        self.changed = True
        
    def draw_item(self):
        self.draw()
        
    def draw(self):
        self.pointer.draw()
        self.changed = False
        