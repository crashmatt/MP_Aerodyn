'''
Created on 27 Jul 2015

@author: matt
'''

import math

class Cartesian(object):
    '''
    Class for Cartesian coordinate
    '''

    def __init__(self, x, y):
        '''
        Constructor
        '''
        self.x = x
        self.y = y
    

class Polar(object):
    '''
    Class for polar coordinate
    '''
    
    def __init__(self, distance=0.0, heading=0.0, geo_coord1=None, geo_coord2=None):
        '''
        Constructor
        '''
        if geo_coord1 is None or geo_coord2 is None:
            self.distance = distance
            self.angle = heading
        else:
            self.from_geo_coords(geo_coord1, geo_coord2)
        
    def to_coordinate(self):
        rad_angle = math.radians(self.heading)
        x = self.distance * math.sin(rad_angle)
        y = self.distance * math.sin(rad_angle)
        return Cartesian(x,y)
    
    def from_geo_coords(self, geo_coord1, geo_coord2):
        lon1 = math.radians(geo_coord1.lon)
        lat1 = math.radians(geo_coord1.lat)
        lon2 = math.radians(geo_coord2.lon)
        lat2 = math.radians(geo_coord2.lat)
        dLat = lat2 - lat1
        dLon = lon2 - lon1
        
        coslat1 = math.cos(lat1)
        coslat2 = math.cos(lat2)
        
        a = math.sin(0.5*dLat)**2 + math.sin(0.5*dLon)**2 * coslat1 * coslat2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
        self.distance = 6371 * 1000 * c
        
        # bearing calc from here: http://stackoverflow.com/questions/1971585/mapping-math-and-javascript
        # added sanity check for short distance
        if(self.distance > 1.0):
            self.angle = math.atan2(coslat1*math.sin(lat2)-math.sin(lat1)*coslat2*math.cos(dLon), math.sin(dLon)*coslat2) 
        else:
            self.angle = 0;


class GeoCoord(object):
    '''
    Class for Geographical Coordinates
    '''

    def __init__(self, lon, lat):
        '''
        Constructor
        '''
        self.lon = lon
        self.lat = lat


class TileCoord(object):
    '''
    Class for absolute map tile co-ordinates scaled in map tile size
    '''

    def __init__(self, tile_x, tile_y):
        '''
        Constructor
        '''
        self.tile_x = tile_x
        self.tile_y = tile_y

    def get_tile_number(self):
        '''
        Return the tile number which this tile co-ordinate is in
        '''
        return TileNumber(int(self.tile_x), int(self.tile_y))
    
    def get_relative_tile_coord(self, TileNumber):
        xrel = self.tile_x - TileNumber.tile_x
        yrel = self.tile_y - TileNumber.tile_y
        return RelTileCoord(xrel, yrel)
     
    def get_abs_pixel_pos(self, tilePixelSize):
        return MapPixelPos(self.tile_x*tilePixelSize, self.tile_y*tilePixelSize)
    
     
class RelTileCoord(object):
    '''
    Class for realtive map tile co-ordinates scaled in map tile size
    '''

    def __init__(self, tile_x, tile_y):
        '''
        Constructor
        '''
        self.tile_x = tile_x
        self.tile_y = tile_y
    
    def get_tile_pixel_pos(self, tilePixelSize):
        return TilePixelPos(tilePixelSize*self.tile_x, tilePixelSize*self.tile_y)

        

class TilePixelPos(object):
    '''
    Class for tile pixel position relative to the tile
    '''

    def __init__(self, pixel_x, pixel_y):
        '''
        Constructor
        '''
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
    
    
class MapPixelPos(object):
    '''
    Class for tile pixel position relative to the tile
    '''

    def __init__(self, pixel_x, pixel_y):
        '''
        Constructor
        '''
        self.map_pixel_x = pixel_x
        self.map_pixel_y = pixel_y
    

class TileNumber(object):
    '''
    Class for map tile numbering
    '''

    def __init__(self, tile_x, tile_y):
        '''
        Constructor
        '''
        self.tile_x = tile_x
        self.tile_y = tile_y
