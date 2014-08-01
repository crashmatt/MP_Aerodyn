from __future__ import absolute_import, division, print_function, unicode_literals

from pi3d.constants import *
from pi3d import Shape
from pi3d.shape import Plane

class Box2d(object):
    """ 3d model inherits from Shape"""
    def __init__(self,  camera=None, light=None, w=1.0, h=1.0, d=1.0,
               name="", x=0.0, y=0.0, z=0.0,
               line_colour=(255,255,255,255), fill_colour=(0,0,0,255), line_thickness = 1,
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

        if(fill_colour[3] > 0):
            self.box = Plane.Plane(camera=camera, w=w, h=h, x=xoffset, y=y, z=z)
            self.box.set_material((fill_colour))
            self.box.set_draw_details(self.shader, [], 0, 0)
            self.box.set_alpha(fill_colour[3])

        self.boxtop = Plane.Plane(camera=camera, w=w+(line_thickness*2), h=line_thickness, x=xoffset, y=y+(h/2)+(line_thickness/2), z=z)
        self.boxtop.set_material((line_colour))
        self.boxtop.set_draw_details(self.shader, [], 0, 0)
        self.boxtop.set_alpha(line_colour[3])

        self.boxbottom = Plane.Plane(camera=camera, w=w+(line_thickness*2), h=line_thickness, x=xoffset, y=y-(h/2)-(line_thickness/2), z=z)
        self.boxbottom.set_material((line_colour))
        self.boxbottom.set_draw_details(self.shader, [], 0, 0)
        self.boxbottom.set_alpha(line_colour[3])

        self.boxleft = Plane.Plane(camera=camera, w=line_thickness, h=h+(line_thickness*2), x=xoffset-(w/2)-(line_thickness/2), y=y, z=z)
        self.boxleft.set_material((line_colour))
        self.boxleft.set_draw_details(self.shader, [], 0, 0)
        self.boxleft.set_alpha(line_colour[3])

        self.boxright = Plane.Plane(camera=camera, w=line_thickness, h=h+(line_thickness*2), x=xoffset+(w/2)+(line_thickness/2), y=y, z=z)
        self.boxright.set_material((line_colour))
        self.boxright.set_draw_details(self.shader, [], 0, 0)
        self.boxright.set_alpha(line_colour[3])
        
    def draw(self):
        box = getattr(self, "box", None) 
        if(box != None):
            box.draw()
        self.boxtop.draw()
        self.boxbottom.draw()
        self.boxleft.draw()
        self.boxright.draw()

