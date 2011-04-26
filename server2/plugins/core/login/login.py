class Plugin:
    def __init__(self,core):
        print "Initializing plugin: core.login"
        self.pluginName        = "core - login handler"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This plugin handles basic player authentication"""
        
        self.core  = core
        
        ''' This plugin uses the core event connectionMade and player event lineReceived '''
        
        self.core.event.add("connectionMade",self.connectionMade)
        
        self.motd = open('strings/motd.txt','r').read()
        
    def connectionMade(self,kwargs):
        print "plugins.core.login: Connection made"
        player = kwargs['player']
        
        player.version = False
        player.account = False
        player.pw      = False
        
        player.event.add("lineReceived",self.lineReceived)
        
    def lineReceived(self,kwargs):
        print "plugins.core.login: lineReceived - %s"%kwargs['line']
        player = kwargs['player']
        line   = kwargs['line']
        
        if not player.version:
            tok = line.split(' ')
            if tok[0] != 'hsk': player.disconnect();return
            elif len(tok) != 2: player.disconnect();return
            
            if tok[1] == 'SUPERHANDSHAKE':
                self.core.event.call("sendMessage",{'to':player,'message':"You are running a ropeclient with a very ancient protocol. To connect to this server, update."})
                return
            
            
            self.core.event.call("enablePlugin",{'to':player, 'plugin':'plugins.core.output'})
            self.core.event.call("enablePlugin",{'to':player, 'plugin':'plugins.core.entry'})
            #self.core.event.call("requireModule",{'to':player, 'module':'plugins.core.playerbox'})
            
            if tok[1] != self.core.version:
                self.core.event.call("sendMessage",{'to':player,'message':"Outdated version. You're running %s, server is running %s."%(tok[1],self.core.version)})
            else:
                self.core.event.call("sendMessage",{'to':player,'message':"Version up to date."})
                self.core.event.call("sendMessage",{'to':player,'message':self.motd})
                self.core.event.call("sendMessage",{'to':player,'message':"What is your name?"})
            player.version = tok[1]
                
        elif not player.account:
            self.core.event.call("sendMessage",{'to':player,'message':"Hello %s!"%line})

