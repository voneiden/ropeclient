import time

class Plugin:
    def __init__(self,core):
        print "Initializing plugin: core.chatroom"
        self.pluginName        = "core - chatroom"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This plugin handles a simple chatroom"""
        
        self.core  = core
        
        self.core.event.add("loggedIn",self.loggedIn)
        self.core.event.add("connectionLost",self.connectionLost)
        self.players = []
        
    def loggedIn(self,kwargs):
        player = kwargs['player']
        self.sendMessage(player,"* To join the chatroom, type: /chatroom (%i players online)"%len(self.players))
        player.event.add("lineReceived",self.lineReceived)
        player.typing = False
        player.name   = player.account
        
    def connectionLost(self,kwargs):
        player = kwargs['player']
        if player in self.players: self.remPlayer(player)
        print "plugins.core.chatroom: connection lost to",player.account
    
  
    def sendMessage(self,to,message):
        self.core.event.call("sendMessage",{'to':to,'message':message})
    
    def lineReceived(self,kwargs):
        print "plugins.core.chatroom: lineReceived - %s"%kwargs['line']
        player = kwargs['player']
        line   = kwargs['line']
        tok = line.split(' ')
        if len(tok) == 1:
            if line   == 'pit': player.typing = True;self.sendTyping(player)
            elif line == 'pnt': player.typing = False;self.sendTyping(player)
        elif player not in self.players:
            if tok[1].lower() == '/chatroom':
                self.addPlayer(player)
        else:
            if tok[1].lower() == '/name' and len(tok) > 2:
                player.name = " ".join(tok[2:])
                # TODO: somehow notify the player of the character name..
            else:
                message = " ".join(tok[1:])
                self.core.event.call('dicerSearch',{'data':message})
                
                self.sendMessage(self.players,'''%s says, "%s"'''%(player.name,message))
                
        
        
    def addPlayer(self,player):
        print "plugins.core.chatroom: addPlayer"
        self.players.append(player)
        self.core.event.call("enablePlugin",{'to':player, 'plugin':'plugins.core.playerbox'})
        self.sendListOfPlayers()
        self.sendMessage(player,"Please set your character name using the command: /name")
        self.sendMessage(self.players,"%s has joined the game!"%player.account)
        
    def remPlayer(self,player):
        print "plugins.core.chatroom: renPlayer"
        self.players.remove(player)
        self.sendListOfPlayers()
        self.sendMessage(self.players,"%s has left the game!"%player.account)
        
    def sendListOfPlayers(self):
        players = []
        for player in self.players:
            players.append(player.account)
        buf = "lop %s"%(" ".join(players))
        
        for player in self.players:
            player.write(buf)
            
    def sendTyping(self,player):
        print "plugins.core.chatroom: sending typing update"
        if   player.typing: buf = "pit %s"%player.account
        else: buf = 'pnt %s'%player.account
        for player in self.players:
            player.write(buf)
            
    #def sendAnnounce(self,message):
    #    for player in self.players:
    #        sendMessage