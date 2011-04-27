import time

class Plugin:
    def __init__(self,core):
        print "Initializing plugin: core.chatroom"
        self.pluginName        = "core - dispatcher"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This plugin handles a simple chatroom"""
        
        self.core  = core
        
        self.core.event.add("loggedIn",self.loggedIn)
        self.core.event.add("connectionLost",self.connectionLost)
        
        self.players = {}
        
    def loggedIn(self,kwargs):
        player = kwargs['player']
        self.players[player.account] = player
        self.sendMessage(player,"You have logged in to chatroom!")
        
    def connectionLost(self,kwargs):
        pass
    
  
    def sendMessage(self,to,message):
        self.core.event.call("sendMessage",{'to':to,'message':message})
        