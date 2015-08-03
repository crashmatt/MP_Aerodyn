'''
Created on 16 Jul 2015

@author: matt
'''

import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
from pi3d.shape.FlipSprite import FlipSprite
import time
from pi3dTiledMap import CoordSys


class MapTile(object):
    '''
    classdocs
    '''

    def __init__(self, map_camera, map_shader, tilePixels, tile_no):
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

        # Items draw on the tile that need to be tracked
        self.tile_items = []

        self.tile_no = tile_no
        
        tilename = 'maptile {:d},{:d}'.format(tile_no.tile_num_x , tile_no.tile_num_y)
        xpos = float(tile_no.tile_num_x*tilePixels)
        ypos = float(tile_no.tile_num_y*tilePixels)

        self.texture = OffScreenTexture(name="map_tile",  w=self.tilePixels, h=self.tilePixels)
        self.sprite = FlipSprite(camera=map_camera, w=self.tilePixels, h=self.tilePixels, z=6.0, x=xpos, y=ypos, flip=True)
        
    def __del__(self):
        self.texture.delete_buffers()
            
        
    def draw(self):
        self.sprite.draw(self.map_shader, [self.texture], camera = self.map_camera)
        self._drawDone = True
        
    def is_draw_done(self):
        return self._drawDone
    
    def start(self, clear=True):
        self.texture._start(clear)
        # Only set update time if tile is not cleared
        if not clear:
            self.tile_update_time = time.time()
    
    def end(self):
        self.texture._end()
        
    def set_alpha(self, alpha):
        self.sprite.set_alpha(alpha)
        