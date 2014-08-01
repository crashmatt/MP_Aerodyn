'''
Created on 24 Jul 2014

@author: matt
'''

class ScreenScale(object):
    '''
    scale between screen position and pixel position
    
    screen position is +-0.5 with individual scales for x and y axis
    '''

    def __init__(self, xstep, ystep):
        '''
        Constructor
        *xstep* is the x grid size in screen position steps
        *ystep* is the y grid size in screen position steps
        '''
        from pi3d.Display import Display
        
        self.height = Display.INSTANCE.height
        self.width = Display.INSTANCE.width
        
        self.xgrid_step = xstep
        self.ygrid_step = ystep
        

    def pos_to_pixel(self, xpos=0, ypos=0):
        ''' returns a tuple x,y '''
        x=xpos * self.width
        y=ypos * self.height
        return x,y
    
    def pixel_to_pos(self, x=0, y=0):
        xpos = x / self.width
        ypos = y / self.height
        return xpos, ypos
        
    def get_grid_pos(self, grid_x=0, grid_y=0):
        x = grid_x * self.xgrid_step
        y = grid_y * self.ygrid_step
        return x,y
    
    def get_grid_pixel(self, grid_x=0, grid_y=0):
        x = grid_x * self.xgrid_step * self.width
        y = grid_y * self.ygrid_step * self.height
        return x,y
        
        