from __future__ import absolute_import, division, print_function, unicode_literals

import ctypes
import numpy as np
import itertools
import os.path
import sys
if sys.version_info[0] == 3:
  unichr = chr

try:
  from PIL import Image, ImageDraw, ImageFont
except:
  print('Unable to import libraries from PIL')

from pi3d.constants import *
from pi3d.Texture import Texture

MAX_SIZE = 1920

class PointFont(Texture):
  """
  A Font contains a TrueType font ready to be rendered in OpenGL.

  A font is just a mapping from codepoints (single Unicode characters) to glyphs
  (graphical representations of those characters).

  Font packs one whole font into a single Texture using PIL.ImageFont,
  then creates a table mapping codepoints to subrectangles of that Texture."""

  def __init__(self, font, color=(255,255,255,255), codepoints=None,
               add_codepoints=None, font_size=48, italic_adjustment=1.1, background_color=None):
    """Arguments:
    *font*:
      File path/name to a TrueType font file.

    *color*:
      Color in standard hex format #RRGGBB

    *font_size*:
      Point size for drawing the letters on the internal Texture

    *codepoints*:
      Iterable list of characters. All these formats will work:

        'ABCDEabcde '
        [65, 66, 67, 68, 69, 97, 98, 99, 100, 101, 145, 148, 172, 32]
        [c for c in range(65, 173)]

      Note that Font will ONLY use the codepoints in this list - if you
      forget to list a codepoint or character here, it won't be displayed.
      If you just want to add a few missing codepoints, you're probably better
      off using the *add_codepoints* parameter.

      If the string version is used then the program file might need to
      have the coding defined at the top:  # -*- coding: utf-8 -*-

      The default is *codepoints*=range(256).

    *add_codepoints*:
      If you are only wanting to add a few codepoints that are missing, you
      should use the *add_codepoints* parameter, which just adds codepoints or
      characters to the default list of codepoints (range(256). All the other
      comments for the *codepoints* parameter still apply.

    *image_size*:
      Width and height of the Texture that backs the image.
      If it doesn't fit then a larger size will be tried up to MAX_SIZE.
      The isses are: maximum image size supported by the gpu (2048x2048?)
      gpu memory usage and time to load by working up the size required
      in 256 pixel steps.

    *italic_adjustment*:
      Adjusts the bounding width to take italics into account.  The default
      value is 1.1; you can get a tighter bounding if you set this down
      closer to 1, but italics might get cut off at the right.
    """
    super(PointFont, self).__init__(font)
    self.font = font
    try:
      imgfont = ImageFont.truetype(font, font_size)
    except IOError:
      abspath = os.path.abspath(font)
      msg = "Couldn't find font file '%s'" % font
      if font != abspath:
        msg = "%s - absolute path is '%s'" % (msg, abspath)

      raise Exception(msg)

    pipew, pipeh = imgfont.getsize('|') # TODO this is a horrible hack
    #to cope with a bug in Pillow where ascender depends on char height!
    ascent, descent = imgfont.getmetrics()
    self.height = ascent + descent + 1  #+1 is correction to round up to 64. Why?
    
    image_size = self.height  * 16  # or 1024

    codepoints = (codepoints and list(codepoints)) or list(range(256))
    if add_codepoints:
      codepoints += list(add_codepoints)

    self.im = Image.new("RGBA", (image_size, image_size), background_color)
    self.alpha = True
    self.ix, self.iy = image_size, image_size

    self.glyph_table = {}

    draw = ImageDraw.Draw(self.im)

#    characters = []
    self.glyph_table = {}

    yindex = 0
    xindex = 0
      
    for i in itertools.chain([0], codepoints):
      try:
        ch = unichr(i)
      except TypeError:
        ch = i
    
      curX = xindex * self.height
      curY = yindex * self.height
      
      chwidth, ___ = imgfont.getsize(ch)
          
      draw.text((curX + ( (self.height - chwidth)  / 2), curY), ch, font=imgfont, fill=color)
      
      xpos = (curX + 2) / self.ix   # Correction for PIL font offset. Why? Who knows? Ahh well!
      ypos = curY / self.iy
      table_entry = [xpos, ypos, chwidth]
      
      self.glyph_table[ch] = table_entry

      xindex += 1
      if xindex >= 16:
        xindex = 0
        yindex += 1

    RGBs = 'RGBA' if self.alpha else 'RGB'
    #self.image = self.im.convert(RGBs).tostring('raw', RGBs)
    self.im = self.im.convert(RGBs)
    self.image = np.array(self.im)
    self._tex = ctypes.c_int()
    
     

  def _load_disk(self):
    """
    we need to stop the normal file loading by overriding this method
    """
