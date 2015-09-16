""" Text rendered using a diy points class and special shader uv_spriterot.

This demo builds on the SpriteBalls demo but adds sprite image rotation, thanks
to Joel Murphy on stackoverflow. The information is used by the uv_spritemult
shader as follows

  vertices[0]   x position of centre of point relative to centre of screen in pixels
  vertices[1]   y position
  vertices[2]   z depth but fract(z) is used as a multiplier for point size
  normals[0]    rotation in radians
  normals[1]    alpha
  normals[2]    the size of the sprite square to use for texture sampling
                in this case each sprite has a patch 0.125x0.125 as there
                are 8x8 on the sheet. However normals[2] is set to 0.1 to
                leave a margin of 0.0125 around each sprite.
  tex_coords[0] distance of left side of sprite square from left side of
                texture in uv scale 0.0 to 1.0
  tex_coords[1] distance of top of sprite square from top of texture

The movement of the vertices is calculated using numpy which makes it very
fast but it is quite hard to understand as all the iteration is done
automatically.
"""
import numpy as np
from pi3d.Shape import Shape
from pi3d.shape.Points import Points
from pi3d.Texture import Texture
from pi3d.Shader import Shader
from pi3d.util.Font import Font
from encodings.rot_13 import rot13
from google.protobuf import text_format
from gettattra import *

class FastText(object):
    def __init__(self, font, camera, max_chars = 100):
        """ Arguments:
        *font*:
          A PointFont object.
        *fmax_chars*:
          maximum number of chars which determines the number of points in the buffer
        """
        self.max_chars = max_chars
        self.font = font

        self.shader = Shader("shaders/uv_spritemult")
        
        self.locations = np.zeros((max_chars, 3)) 
#        self.locations[:,0] = np.random.uniform(-300, 300, max_chars)
#        self.locations[:,1] = np.random.uniform(-200, 200, max_chars)
               
        self.locations[:,2] = 0.5

        self.normals = np.zeros((max_chars, 3))
        # :,0 for rotation
        # :,1 for alpha
        self.normals[:,1] = 0.0
        self.normals[:,2] = 0.057
        """  :,2 for sub-size i.e 64x64 images on 1024x1024 image each is 0.0625 
        there is margin on each side to avoidproblems with overlapping on rotations.
        """
        self.uv = np.zeros((max_chars, 2)) # u picnum.u v
#        self.uv[:,:] = 0.0 # all start off same. uv is top left corner of square
        
#        self.uv[:,0] = np.random.uniform(0, 15, max_chars) * 0.0625 # + 0.0625
#        self.uv[:,1] = np.random.uniform(0, 15, max_chars) * 0.0625 # + 0.0625

        self.text = None
        
        self.text_blocks = []
        
        self.text = Points(camera=camera, vertices=self.locations, normals=self.normals, tex_coords=self.uv,
                       point_size=64)   #font.height
        self.text.set_draw_details(self.shader, [self.font])
            

    def regen(self):
        ##### regenerate text from text blocks
        char_index = 0
        for block in self.text_blocks:
            if (char_index + block.char_count) < self.max_chars:
                xpos = block.x
                ypos = block.y
                str = block.get_string()
#                str = str.decode('utf-8')
                
                index = 0
                for char in str:
                    ind = index + char_index
                                        
                    glyph = self.font.glyph_table[char]
                    self.uv[ind][0] = glyph[0]
                    self.uv[ind][1] = glyph[1]
                    
                    self.locations[ind][0] = xpos
                    self.locations[ind][1] = block.y
                    self.locations[ind][2] = block.size
                    
                    self.normals[ind][1] = 1.0

                    xpos += glyph[2] * block.size
                    index += 1
                    
            char_index = char_index + block.char_count
                    
        self.text.buf[0].re_init(pts=self.locations, normals=self.normals, texcoords=self.uv) # reform opengles array_buffer
  
    def add_text_block(self, text_block):
        self.text_blocks.append(text_block)
        return len(self.text_blocks) - 1
    
    def set_text_block_position_xy(self, index, x, y):
        if index >= len(self.text_blocks):
            return
        block = self.text_blocks[index]
        block.x = x
        block.y = y
        
    def set_text_block_rotation(self, index, rot):
        if index >= len(self.text_blocks):
            return
        self.text_blocks[index].rot = rot

    def draw(self):
        self.text.draw()
 
class TextBlock(object):
    def __init__(self, x, y, z, rot, char_count, data_obj, attr, text_format="{:s}", size=0.25, spacing="C", space=1.1):
        """ Arguments:
        *x, y, z*:
          As usual
        *rot*:
          TODO: rotation in unknown units??? 
        *data_obj*:
          Data object to use in text format
        *attr*:
            Attribute in data object to use in text format
        *text_format*:
            Thetext format to use including any data formattings
        *size*:
            Size of the text 0 to 0.9999
        *spacing*:
             Type of character spacing. C=Constant, M=Multiplier, F=Fixed space
        """
        self.x = x 
        self.y = y 
        self.z = z 
        self.rot = rot 
        self.char_count = char_count
        self.data_obj = data_obj
        self.attr = attr
        self.text_format = text_format
        self.size = size
                 
    def get_string(self):
        if(self.attr != None) and (self.data_obj != None):
            value = getattra(self.data_obj, self.attr, None)
        else:
            value = None
        
        if(value != None):
            return self.text_format.format(value)

        return " "
        