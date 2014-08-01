'''
Created on 4 Jul 2014

@author: matt
'''
import pi3d

#import sys.path(1, '/home/pi/pi3d/pi3d/pi3d.py')
#sys.path.insert(1, '/home/pi/pi3d/pi3d')


class FastNumber(object):

    #total digits including negatives and decimal points
    #spacing = pixels between digits
    def __init__(self,  font, camera=None, shader=None, x=0, y=0, size=0.5, digits=1, spacing=25, justify='R', z=1, alpha=1):
        self.digits = []
        self.camera = camera
        self.shader = shader
        self.alpha = alpha
        self.z = z
        if(justify=='R'):
            self.x = x + (spacing * 0.5)
        elif(justify == 'L'):
            self.x = x + (spacing * 0.5) - (spacing * digits)            
        elif(justify == 'C'):
            self.x = x + (spacing * 0.5) - (spacing * digits * 0.5)
        else:
            self.x = x
        
        self.y = y
        self.num_digits = digits
        self.value = 0
        self.spacing = spacing
        self.size = size
        self.font = font
        
        self.generate()
    
    def generate(self):
        xpos = self.x
        self.digits = []
        for i in xrange(0,self.num_digits):
            fdigit = FastDigit(font=self.font, camera=self.camera, shader=self.shader, x=xpos, y=self.y, 
                               size=self.size, z=self.z, alpha=self.alpha)
            self.digits.append(fdigit)
            xpos += self.spacing

    def set_number(self, text):
        pos = 0
        textlen = len(text)
        try:
            for i in xrange(0,self.num_digits-textlen):
                self.digits[pos].set_digit(" ")
                pos += 1
                
            pos =  self.num_digits-textlen
    #No check for excess text length       
    #        if(textlen > self.num_shown_digits):
            
            for numchar in text:
                digit = self.digits[pos]
                digit.set_digit(numchar)
                pos += 1
        except:
            print("did not fit text {:s} in length {:d}", text, self.num_digits)

    def draw(self):
        for digit in self.digits:
            digit.draw_digit()

class FastDigit(object):

    def __init__(self, font, camera=None, shader=None, x=0, y=0, z=1,size=1.0, default="0", alpha=1.0):
        self.shader = shader
        self.camera = camera
        self.size = size
        self.font = font
        self.x = x
        self.y = y
        self.z = z
        self.alpha = alpha
        self.digits = []
                
        self.generate_digits()
        self.num_shown_digits = 0;
        self.set_digit(default)
        
    def generate_digits(self):
        self.digits = []
        self.space = (" ", None)
        digit = pi3d.String(camera=self.camera, font=self.font, string=".", is_3d=False, z=self.z, size=self.size)
        digit.translate(self.x, self.y, self.z)
        digit.set_shader(self.shader)
        digit.set_alpha(self.alpha)
        self.dot = (".", digit)
        digit = pi3d.String(camera=self.camera, font=self.font, string=",", is_3d=False, z=self.z, size=self.size)
        digit.translate(self.x, self.y, self.z)
        digit.set_shader(self.shader)
        digit.set_alpha(self.alpha)
        self.comma = (",", digit)
        digit = pi3d.String(camera=self.camera, font=self.font, string="-", is_3d=False, z=self.z, size=self.size)
        digit.translate(self.x, self.y, self.z)
        digit.set_shader(self.shader)
        digit.set_alpha(self.alpha)
        self.neg = ("-", digit)
        digit = pi3d.String(camera=self.camera, font=self.font, string="+", is_3d=False, z=self.z, size=self.size)
        digit.translate(self.x, self.y, self.z)
        digit.set_shader(self.shader)
        digit.set_alpha(self.alpha)
        self.pos = ("+", digit)
        
        for i in xrange(0,10):
            tempstr = "%0d" % i
            digit = pi3d.String(camera=self.camera, font=self.font, string=tempstr, is_3d=False, z=self.z, size=self.size)
            digit.translate(self.x, self.y, self.z)
            digit.set_shader(self.shader)
            digit.set_alpha(self.alpha)
            self.digits.append((tempstr,digit))
        
        self.digit = self.space
        
    def draw_digit(self):
        if(self.digit[1] is not None):
#            self.digit[1].draw()
            self.digit[1].fast_draw()
            
    def set_digit(self,numchar):
        if(numchar != self.digit[0]):
            num = ord(numchar)
            if(num >= ord('0')) and (num <= ord('9')):
                self.digit = self.digits[int(numchar)]
            else:
                if(numchar == '-'):
                    self.digit = self.neg
                elif(numchar == '.'):
                    self.digit = self.dot
                elif(numchar == ','):
                    self.digit = self.comma
                elif(numchar == '+'):
                    self.digit = self.pos
                else:
                    self.digit = (" ", None)

