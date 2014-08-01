'''
Created on 23 Jul 2014

@author: matt
'''
import ConfigParser

class HUDConfig(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.filename = "HUD.cfg"
        self.layers = []
        
    def get_layers(self):
        return self.layers
    
    def store_hud_config(self):
        config = ConfigParser.ConfigParser()
        config.add_section("static_layer")
        
        with open('hud.cfg', 'wb') as configfile:
            config.write(configfile)    