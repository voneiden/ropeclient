class RopeModule:
    def __init__(self,parent):
        self.parent = parent
        self.players = {}
        
    def enable(self):
        self.parent.addHook('receiveMessage',self.receiveMessage)
        self.parent.addHook('requireModule',self.requireModule)
    def disable(self):
        self.parent.delHook('receiveMessage',self.receiveMessage)
        self.parent.delHook('requireModule',self.requireModule)
        
    def receiveMessage(self,data):
        player = data[0]
        if player in self.players.keys():
            text = data[1]
            tok = text.split(' ')
            hdr = tok[0].lower()
            
            if hdr == 'mod' and len(tok) > 2:
                status = tok[1]
                module = tok[2]
                if module in self.players[player]:
                    if status == 'enabled' and self.players[player][module] == 1:
                        self.display("Client enabled the module")
                    elif status == 'disabled' and self.players[player][module] == 0:
                        self.display("Client has disabled the module")
                    else:
                        self.display("Client has failed to comply module request. Forcing a disconnect.")
                        player.transport.loseConnection()
                        
                        
        
    def display(self,text):
        self.parent.callHook("output","core_module: %s"%text)
        
    def requireModule(self,data):
        print "Requiring module",data
        player = data[0]
        state = data[1]
        module = data[2]
        player.write("mod %s %s"%(state,module))
        if player in self.players:
            self.players[player][module] = 1
        else:
            self.players[player] = {module:1}
            
        