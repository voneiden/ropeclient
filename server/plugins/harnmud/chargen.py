class Plugin:
    def __init__(self,core):
        print "Initializing plugin: harnmud.chargen"
        self.pluginName        = "Harnmud Character Generation"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This harnmud plugin tries to implement some basic mud functionality"""
        
        self.core  = core
        
        self.core.event.add("harnmudChargen",self.chargen)
        self.players = []
        
        
    def chargen(self,kwargs):
        ''' The kwargs should contain coreEvent (lineReceived) and player '''
        print "plugins.harnmud.chargen: enabling chargen.."
        lr = kwargs['lineReceived']
        player    = kwargs['player']
        
        player.db['lineReceived'] = lr
        
        player.event.rem("lineReceived",lr)
        player.event.add("lineReceived",self.lineReceived)
        
    def stop(self,kwargs):
        print "plugins.harnmud.chargen: stopping chargen.."
        player = kwargs['player']
        
        player.event.rem("lineReceived",self.lineReceived)
        player.event.add("lineReceived",player.db['lineReceived'])
        
        del player.db['lineReceived']
        
        
        
        
    def lineReceived(self,kwargs):
        player = kwargs['player']
        line   = kwargs['line']
        tok    = kwargs['tok']
        
        self.sendMessage(player,"Chargen!")
        
        
    def sendMessage(self,to,message):
        self.core.event.call("sendMessage",{'to':to,'message':message})