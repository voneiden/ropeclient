class Plugin:
    def __init__(self,core):
        print "Initializing plugin: harnmud"
        self.pluginName        = "Harnmud"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This harnmud plugin tries to implement some basic mud functionality"""
        
        self.core  = core
        
        import chargen
        
        self.core.plugins['plugins.harnmud.chargen'] = chargen.Plugin(self.core)
        
        
        self.core.event.add("loggedIn",self.loggedIn)
        self.core.event.add("connectionLost",self.connectionLost)
        self.players = []
        self.characters = {}
        
        
    def loggedIn(self,kwargs):
        ''' This function takes players who have logged in on an account '''
        print "plugins.harnmud: loggedIn"
        player = kwargs['player']
        self.sendMessage(player,"* To join the harnmud, type: /harnmud (%i players online)"%len(self.players))
        player.event.add("lineReceived",self.takeOver)
        player.event.add("takenOver",self.takenOver)
        player.typing = False
        player.name   = player.account
        
    def takeOver(self,kwargs):
        ''' This function is used for taking over a player after loggin in '''
        line   = kwargs['line']
        player = kwargs['player']
        print "core.harnmud.takeover",line
  
        if line == 'msg /harnmud':
            player.event.add("lineReceived",self.lineReceived)
            player.event.call("takenOver",{'player':player})
            
    def takenOver(self,kwargs):
        ''' This function means that the player was taken over.. well said he? '''
        print "plugins.harnmud.takeOver: Giving up player"
        player = kwargs['player']
        player.event.rem("takenOver",self.takenOver)
        player.event.rem("lineReceived",self.takeOver)
        
    def connectionLost(self,kwargs):
        player = kwargs['player']
        if player in self.players: self.remPlayer(player)
        print "plugins.harnmud: connection lost to",player.account
        
    def addPlayer(self,player):
        print "plugins.harnmud: addPlayer"
        self.players.append(player)
        self.sendMessage(self.players,"%s has joined the game!"%player.account)
        self.core.event.call("harnmudChargen",{'player':player,'lineReceived':self.lineReceived})
        
        
    def remPlayer(self,player):
        print "plugins.harnmud: remPlayer"
        self.players.remove(player)
        self.sendListOfPlayers()
        self.sendMessage(self.players,"%s has left the game!"%player.account)
        
    def lineReceived(self,kwargs):
        player = kwargs['player']
        line   = kwargs['line']
        tok    = kwargs['tok']
        pass
    def sendMessage(self,to,message):
        self.core.event.call("sendMessage",{'to':to,'message':message})