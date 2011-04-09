import time

class Plugin:
    def __init__(self,core):
        print "Initializing plugin: core.login"
        self.pluginName        = "core - dispatcher"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This plugin handles sending of packets"""
        
        self.core  = core
        
        self.core.event.add("sendMessage",self.sendMessage)
        
        self.timestamps = []
        
    def sendMessage(self,kwargs):
        if not kwargs.has_key('message') or not kwargs.has_key('to'):
            print "plugins.core.dispatcher: Unable to process an event."
            return
        
        if not kwargs.has_key('owner'): owner = 'server'
        else:  owner = kwargs['owner']
        
        message = kwargs['message']
        timestamp = self.generateTimestamp()
        
        to = kwargs['to']
        
        fullmessage = "msg %s %i %s"%(owner,timestamp,message)
        
        if type(to) == list:
            for t in to:
                t.write(fullmessage)
        else:
            to.write(fullmessage)
        
    def generateTimestamp(self):
        ''' this function generates an unique timestamp for a message'''
        timestamp = time.time()
        while timestamp in self.timestamps:
            timestamp += 0.00001
        self.timestamps.append(timestamp)
        return timestamp