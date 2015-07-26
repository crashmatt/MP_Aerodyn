'''
Created on 16 Jul 2015

@author: matt
'''

import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
from pi3d.shape.FlipSprite import FlipSprite
import time

class MapTile(object):
    '''
    classdocs
    '''


    def __init__(self, map_camera, map_shader, tilePixels, tile_x, tile_y):
        '''
        tilePixels = size of tile in pixels
        '''
        from pi3d.Display import Display
               
        self.tilePixels = tilePixels
        self._drawDone = False
        self.updateCount = 0
        
        self.map_camera = map_camera
        self.map_shader = map_shader
        
        self.tile_create_time = time.time()
        self.tile_update_time = self.tile_create_time
        
        tilename = 'maptile {:d},{:d}'.format(tile_x , tile_y)
#        tilename = "maptile [%d],[%d]", tile_x, tile_y
        xpos = float(tile_x*tilePixels)
        ypos = float(tile_y*tilePixels)

        self.texture = OffScreenTexture(name="map_tile",  w=self.tilePixels, h=self.tilePixels)
        self.sprite = FlipSprite(camera=map_camera, w=self.tilePixels, h=self.tilePixels, z=6.0, x=xpos, y=ypos, flip=True)
        
    def draw(self):
        self.sprite.draw(self.map_shader, [self.texture], camera = self.map_camera)
        self._drawDone = True
        
    def is_draw_done(self):
        return self._drawDone
        