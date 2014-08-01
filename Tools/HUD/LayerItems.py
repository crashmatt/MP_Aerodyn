'''
Created on 18 Jul 2014

@author: matt
'''
import pi3d
import array
import numeric

class LayerItems(object):
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)

    def gen_items(self, phase=None):
        statuschange = False
        for item in self.items:
            if(phase == None):
                item.gen_item()
                if(item.changed):
                    statuschange = True
            elif(item.phase == phase):
                item.gen_item()
                if(item.changed):
                    statuschange = True                
        return statuschange
       
    def draw_items(self):
#        """ Draw all items in the list.  Used when any content of the layer has changed"""
        for item in self.items:
            item.draw_item()

            
        
        
class LayerItem(object):
#    """ A 2D item on an OffScreenTexture layer with information about how, where and when to draw it.
#        Is overridden by specific item type classes"""
    
    def __init__(self, camera=None, shader=None, x=0, y=0, phase=None):
#        """ *phase* controls when to update/generate a new image on the layer. Can be used to balance processor loading""""

        from pi3d.Display import Display
    
        self.x = x  #pos * Display.INSTANCE.height     #position offset in screen pixels
        self.y = y  #pos * Display.INSTANCE.width

        self.camera = camera
        self.shader = shader
        self.phase = phase
        
        self.changed = False    #flag to show if text has been generated but not redrawn yet


class LayerText(LayerItem):
    def __init__(self, font, text, camera, shader=None, x=0, y=0, size=1.0, phase=None, z=1, alpha=1):

        super(LayerText, self).__init__(camera, shader, x, y, phase)
                        
        self.font = font
        self.text = text
        self.size = size
        self.z = z
        self.alpha = alpha
        self.last_text = ""     #remember last generated text to prevent re-generation of unchanged text        
        
        
    def _gen_text(self):
        if self.text != self.last_text:
            self.text_str = pi3d.String(string=self.text, camera=self.camera, font=self.font, is_3d=False, x=self.x, y=self.y, z=self.z, size=self.size, justify='C')
            self.text_str.position(self.x, self.y, 5)
            self.text_str.set_material((0,0,0,0))
            self.text_str.set_alpha(self.alpha)
            self.text_str.set_shader(self.shader)
            self.last_text = self.text
            self.changed = True
        
    def draw_item(self):
        if self.text_str != None:
            self.text_str.draw()
            self.changed = False

    def gen_item(self):
        self._gen_text()


class LayerVarText(LayerText):
    
    def __init__(self, font, text, camera, dataobj=None, attr=None, shader=None, x=0, y=0, size=1.0, phase=None, z=1, alpha=1):
        self.attr = attr
        self.dataobj = dataobj
        self.textformat = text
        
        super(LayerVarText, self).__init__(font, text, camera, shader, x, y, size, phase, z, alpha)
        
        
    def gen_item(self):
        if(self.attr != None) and (self.dataobj != None):
            value = getattr(self.dataobj, self.attr, None)
        else:
            value = None
        
        if(value != None):
            self.text = self.textformat.format(value)
        else:
            self.text = " "
        self._gen_text()


class LayerStringList(LayerVarText):
    """ prerenders a list of strings for display"""
    
    def __init__(self, font, text_format, text_strings, camera, dataobj=None, attr=None, shader=None, x=0, y=0, size=1.0, phase=None, z=1, alpha=1, justify='C'):
        """ *text_Strings* array of strings """
        self.attr = attr
        self.dataobj = dataobj
        
        super(LayerStringList, self).__init__(font, text_format, camera, dataobj=dataobj, attr=attr, shader=shader, x=x, y=y, size=size, phase=phase, z=z, alpha=alpha)

        self.text_strings = []
        for txt in text_strings:
            formatted_text = self.textformat.format(txt)
            pi3dstr = pi3d.String(string=formatted_text, camera=self.camera, font=self.font, is_3d=False, x=self.x, y=self.y, z=self.z, size=self.size, justify=justify) 
#            pi3dstr = pi3d.String(string=formatted_text, camera=self.camera, font=self.font, is_3d=False, size=self.size, justify='C') 

            pi3dstr.set_material((0,0,0,0))
            pi3dstr.set_alpha(self.alpha)
            pi3dstr.set_shader(self.shader)
            self.text_strings.append((txt, pi3dstr))
        self.text = ""
        self.selected_string = None


    def gen_item(self):
        if(self.attr != None) and (self.dataobj != None):
            value = getattr(self.dataobj, self.attr, None)
        else:
            value = None
        
        if(value != None):
            self.text = value
        else:
            self.text = ""
        self._gen_text()
        
        
    def _gen_text(self):
        if self.text != self.last_text:
            for txt in self.text_strings:
                if(txt[0] == self.text):
                    self.selected_string = txt[1]
            self.last_text = self.text
            self.changed = True
    
    def draw_item(self):
        if(self.selected_string is not None):
            self.selected_string.draw()
        self.changed = False
        
class LayerNumeric(LayerVarText):
    def __init__(self, font, text, camera, dataobj=None, attr=None, shader=None, x=0, y=0, size=1.0, phase=None, digits=3, spacing=15, justify='R', z=1, alpha=1 ):
        super(LayerNumeric, self).__init__(font, text, camera, dataobj, attr, shader, x, y, size, phase, z, alpha)

        self.digits = digits
        self.spacing = spacing

        self.number = numeric.FastNumber(camera=self.camera, font=self.font, shader=self.shader, 
                                         digits=self.digits, x=self.x, y=self.y, size=self.size, 
                                         spacing=self.spacing, justify=justify, z=self.z, alpha=self.alpha)

    def _gen_text(self):
        self.number.set_number(self.text)
        
    def draw_item(self):
        self.number.draw()
        
        
class LayerShape(LayerItem):
    def __init__(self, drwshape, phase=None):
        super(LayerShape, self).__init__(self, phase=phase)

        self.drwshape = drwshape
        self.changed = True
    
    def gen_item(self):
        #Something useless just to override and do nothing
        if(self.drwshape == None):
            print("Item not defined")
    
    def draw_item(self):
        self.drwshape.draw()
        self.changed = False
                
class LayerDynamicShape(LayerItem):
    def __init__(self, drwshape, phase=None):
        super(LayerDynamicShape, self).__init__(self, phase=phase)

        self.drwshape = drwshape
        self.changed = True
    
    def gen_item(self):
        self.drwshape.gen_item()
    
    def draw_item(self):
        self.drwshape.draw()
        self.changed = False
        

class Layers(object):
    ''' PROBALY NOT VERY USEFUL - not enough control after generate output
    A collection of Layers and LayerItems which allow them to be generated and redrawn'''
    def __init__(self):
        ''' init self.layers as a tuple (Layer, LayerItems)'''
        self.layers=[]
        
    def add(self, layer, layer_items):
        ''' Add a layer and layer items'''
        self.layers.append((layer, layer_items))
        
    def generate(self, phase=None):
        for layer in self.layers:
            layer[1].gen_items(phase)
            
    def draw_layers(self):
        for layer in self.layers:
            layer[0].start_layer()
            layer[1].draw_items()
            layer[0].end_layer()
