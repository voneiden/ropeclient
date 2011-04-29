
import re, random

class Plugin:
    def __init__(self,core):
        print "Initializing plugin: core.dicer"
        self.pluginName        = "core - dicer"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This plugin handles dice calculations"""
        
        self.core  = core   
        
        self.regexRequest = re.compile("(?:\!\d*d\d*(?:\+|\-)*)(?:(?:(?:\d*d\d*)|\d*)(?:\+|\-)*)*",re.IGNORECASE)
        self.regexObject =  re.compile('[\+-]?\d*d?\d+')
        
        self.core.event.add("dicerSearch",self.search)
        
    
    def search(self,kwargs):
        ''' This function takes in kwargs argument and requries and searches for dice requests
        in it. It will return a dictionary consisting of match:result pairs, which can be 
        replaced by whoever requested it.'''
        print "plugins.core.dicer: search"
        data = kwargs['data']
        if kwargs.has_key('exploding'):
            exploding = kwargs['exploding']
        else: exploding = False
        
        requests = re.findall(self.regexRequest,data)
        results = {}
        
        for request in requests:
            components = self.parser(request)
            roll       = self.roll(components,exploding)
            results[request] = roll
        print "plugins.core.dicer: results",results
        return results
        
        
    def parser(self,request):
        ''' This function takes a request, and works out the components '''
        
        objects = []
        for object in re.finditer(self.regexObject,request):
            object = object.group()
            
            sign = object[0]
            
            if   sign == '-': objects.append((False,object))
            else:             objects.append((True,object))
            
        return objects
        
    
    def roll(self,components,exploding):
        ''' This function takes in a list of components and calculates
            the values of each components and also the total value etc.
            it returns a dictionary composing of {total(int),results(list)}. 
            The results is a tuple of roll,value,exploded '''
            
        total = 0
        results = []
        for component in components:
            sign,roll = component
            if 'd' in roll:
                x,y = roll.split('d')
                try: x = int(x)
                except: x = 1
                try: y = int(y)
                except: y = 2
                value,exploded = self.dice(x,y,exploding)
                if not sign: 
                    value = -value
                    roll = "-"+roll
                else: roll = "+"+roll
                results.append((roll,value,exploded))
                total += value
            else:
                value = int(roll)
                if not sign: 
                    value = -value
                    roll = "-"+roll
                else: roll = "+"+roll
                results.append((roll,value,False))
                total += value
                
        return {'total':total,'results':results}
            

    def dicer(self,data):
        total = 0
        output = []
        for obj in re.finditer(self.regexDicex,data):
            obj = obj.group()
            if   obj[0] == '+': add = True;  obj = obj[1:]
            elif obj[0] == '-': add = False; obj = obj[1:]
            else:               add = True;  obj = obj
            if 'd' not in obj:
                color = "<blue>"#colorize('blue')
                if add: output.append("<grey>+%s<reset>"%obj); total += int(obj)
                else:   output.append("<grey>-%s<reset>"%obj); total -= int(obj)
            else:
                tok = obj.split('d')
                result = self.roll(tok[0],tok[1])
                if not result: return "<grey>[<red>Invalid dice value<reset>]<reset>"
                result,exploded = result
                if exploded: color = '<gold>'
                else:        color = '<SeaGreen>'
                if add: output.append("%s+%s<reset>"%(color,obj)); total += result
                else:   output.append("%s-%s<reset>"%(color,obj)); total -= result
        return "<grey>[%s: <green>%i<reset>]<reset>"%("".join(output),total)

    def dice(self,rolls,sides,exploding):
    
        
        if not 0 < rolls <= 20: return False
        if not 1 < sides <= 100: return False

        exploded  = False
        total = 0
        rolls = range(rolls)
        for i in rolls:
            result = random.randint(1,sides)
            if result == sides and exploding: rolls.append(1); exploded = True
            total += result
        return (total,exploded)