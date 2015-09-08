from __future__ import absolute_import, division, print_function, unicode_literals

from pi3d.constants import *
from pi3d import Shape, Shader
from pi3d.shape import Plane as Plane
import CPlanes
#from pi3d import Plane

class Box2d(object):
    """ 3d model inherits from Shape"""
    def __init__(self,  camera=None, light=None, w=1.0, h=1.0, d=1.0,
               name="", x=0.0, y=0.0, z=0.0,
               line_colour=(1.0,1.0,1.0,1.0), fill_colour=(0,0,0,1.0), line_thickness = 1,
               shader=None, justify='C'):
        """uses standard constructor for Shape extra Keyword arguments:

          *w*
        width
          *h*
        height
          *d*
        depth
          
        The scale factors are the multiple of the texture to show along that
        dimension. For no distortion of the image the scale factors need to be
        proportional to the relative dimension.
        """
#       super(Cuboid, self).__init__(camera, light, name, x, y, z, rx, ry, rz,
#                                1.0, 1.0, 1.0, cx, cy, cz)

        if(shader == None):
            self.shader = None
        else:
            self.shader = shader
                        
        if justify=='L':
            xoffset = int(x - (w * 0.5))
        elif justify=='R':
            xoffset = int(x + (w * 0.5))
        else:
            xoffset = int(x)
            
        
        self.box = CPlanes.CPlanes(camera=camera, x=xoffset, y=y, z=0)
        
        self.box.add_filled_box(w, h, 0.0, 0.0, z, fill_colour, line_colour, line_thickness)
        
        self.box.set_draw_details(self.shader, [], 0, 0)
        self.box.init()

        
    def draw(self):
        box = getattr(self, "box", None) 
        if(box != None):
            box.draw()


