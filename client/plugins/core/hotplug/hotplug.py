class Plugin:
    ''' This is the hotplug class for ropeclient, 
    It's meant to handle dynamic loading, enabling and disabling of other plugins.
    '''
    
    def __init__(self,core):
        self.core = core
        self.plugins = {}

    def enable(self):
        print "plugins.core.hotplug: enabled!"
        self.core.event.add("lineReceived",self.lineReceived)
        
    def disable(self):
        print "plugins.core.hotplug: disabled!"
        self.core.event.rem("lineReceived",self.lineReceived)

        
    def lineReceived(self,kwargs):
        if not kwargs.has_key('text') or not kwargs.has_key('tok'): return False
        tok = kwargs['tok']
        if tok[0] == 'mod':
            try:
                plugin = tok[1]
                state  = int(tok[2])
            except:
                print "plugins.core.hotplug: mod packet corrupted - %s"%str(tok)
                return False
            
            if state == 1: return self.enablePlugin(plugin)
            else: return self.disablePlugin(plugin)
    
    def enablePlugin(self,plugin):
        print "plugins.core.hotplug: enablePlugin()"
        if plugin not in self.plugins.keys():
            ''' Load the plugin module.. '''
            ''' TODO handle missing plugins! '''
            ''' BUG: will load the same plugin multiple times causing nasty stuff to happen '''
 
                
                
            self.plugins[plugin] = self.dynamicImport(plugin)
        else: 
            print "plugins.core.hotplug: enablePlugin - disabling old plugin"
            self.plugins[plugin].disable()
        self.plugins[plugin].enable()
            
    def disablePlugin(self,plugin):
        if plugin in self.plugins.keys():
            self.plugins[plugin].disable()
            
            
    def dynamicImport(self,name):
        print "plugins.core.hotplug:dynamicImport: %s"%name
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod.Plugin(self.core)
        
