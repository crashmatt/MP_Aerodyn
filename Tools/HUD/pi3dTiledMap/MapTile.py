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

        self.texture = OffScreenTexture(name=tilename,  w=self.tilePixels, h=self.tilePixels)
        self.sprite = FlipSprite(camera=map_camera, w=self.tilePixels, h=self.tilePixels, z=6.0, x=xpos, y=ypos, flip=True)

        self._regen_texture = None
        self._regen_index = -3
        
        
    def __del__(self):
        self.texture.delete_buffers()

        if self._regen_texture != None:
            self._regen_texture.delete_buffers()
            
    def get_items_age(self):
        if len(self.tile_items)  == 0:
            return 0.0
        return time.time() - self.tile_items[0][0]
            
    def regen_start(self):
        if self._regen_texture == None:
            tilename = 'maptile {:d},{:d}'.format(self.tile_no.tile_num_x , self.tile_no.tile_num_y)
            self._regen_texture = OffScreenTexture(name=tilename,  w=self.tilePixels, h=self.tilePixels)
            self._regen_index = -2
    
    def regen_end(self):
        if self._regen_texture != None:
            if self.texture != None:
                self.texture.delete_buffers()
                self.texture = None
                self.texture = self._regen_texture
                self._regen_texture = None
        self._regen_index = -1
    
    def redraw_start(self, clear=True):
        if self._regen_texture != None:
            self._regen_texture._start(clear)
    
    def redraw_end(self):
        if self._regen_texture != None:
            self._regen_texture._end()
        
    def get_regen_item_index(self):
        return self._regen_index
    
    def set_regen_index_to_start(self):
        self._regen_index = 0
        
    def set_regen_index(self, index):
        self._regen_index = index

    def regen_running(self):
        return self._regen_texture != None
        

    def draw(self):
        if self.sprite != None:
            self.sprite.draw(self.map_shader, [self.texture], camera = self.map_camera)
            self._drawDone = True
        if self._regen_texture != None and self._regen_index == -2:
            self.sprite.draw(self.map_shader, [self._regen_texture], camera = self.map_camera)
            self._regen_index = -1
        
    def is_draw_done(self):
        return self._drawDone
    
    def is_regen_draw_done(self):
        return self._regen_index >= 0
    
    def start(self, clear=True):
        self.texture._start(clear)
        # Only set update time if tile is not cleared
        if not clear:
            self.tile_update_time = time.time()
    
    def end(self):
        self.texture._end()
        
    def set_alpha(self, alpha):
        self.sprite.set_alpha(alpha)
        