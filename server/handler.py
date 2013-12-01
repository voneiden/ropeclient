class Handler(object):
    def __init__(self, player):
        self.player = player
        self.state  = 0
        
    def process_msg(self, content):
        return False
        
    def process_cmd(self, content):
        return False
        
    def process_edi(self, content):
        return False
        
    def process_pit(self, content):
        return False
        
    def process_pnt(self, content):
        return False
        

class HandlerLogin(Handler):
    def process_msg(self, content):
        pass
        
class HandlerWorld(Handler):
    def process_msg(self, content):
        pass
