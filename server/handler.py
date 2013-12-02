import logging

class Handler(object):
    def __init__(self, player):
        self.player = player
        
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
        
    def process_nan(self, content):
        logging.error("Undefined cmd in message content")
        
class HandlerLogin(Handler):
    def __init__(self, player):
        Handler.__init__(self, player)
        self.state = 0
        self.name = None
       
    def process_msg(self, content):
    
        if len(content["txt"]) == 0:
            return
            
        if self.state == 1: # 1) Received username
            self.name = content["txt"]
            if len(self.name) > self.player.core.settings["max_login_name_length"]:
                return self.player.send_fail_msg("Login name is too long.")
                
                
        
        
  def handler_login(self, header, message):
        '''
        State 1 - asking for name
        State 2 - asking for password
        State 10 - asking for new account verification
        State 11 - asking for new account password
        State 12 - asking one more time for password
        '''
        if header == 'cmd': return
        if len(message) == 0: return 
        message = message.split()
        if self.handlerstate == 1:
            self.temp['name'] = message[0]
            account = [account for account in self.core.accounts if self.temp['name'].lower() == account.name.lower()]
            if account:
                self.handlerstate = 2
                self.account = account[0]
                
                self.connection.write('pwd\r\n')
                return u"Your <fail>password<reset>?"   
            else:
                if re.match("^[A-Za-z]+$", message[0]):
                    self.handlerstate = 10
                    return u"Would you like to create a new account under the name '{name}' yes/no?".format(name=message[0])
                else:
                    return u"This account name contains invalid characters - Try again"
             
        
        elif self.handlerstate == 2:
            if message[0] == self.account.password:
                self.name = self.account.name
                return self.login()
            else:
                self.connection.disconnect() #TODO
                
        elif self.handlerstate == 10:
            if len(message[0]) < 1: return
            if message[0][0].lower() == 'y':
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return u"What would your <red>password<reset> be?"
            else:
                self.handlerstate = 1
                return u"What is your name?"
                
        elif self.handlerstate == 11:
            self.temp['password'] = message[0]
            self.handlerstate = 12
            self.connection.write('pwd\r\n')
            return u"Please retype"
            
        elif self.handlerstate == 12:
            if self.temp['password'] == message[0]:
                #self.handlerstate = 13
                #f = open('text/stylehelp.txt','r')
                #buf = [f.read()]
                #buf.append(u"Choose your style (can be changed later!): irc/mud")
                #f.close()
                
                #return u"\n".join(buf)                
                logging.info( u"New account ({})".format(self.temp['name']))
            
                self.account = server.Account(self.temp['name'],self.temp['password'])
                self.core.accounts.append(self.account)
                self.core.saveAccounts()
                self.name = self.account.name
                return self.login()
                
            else:
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return u"Password mismatch, try again! Your password?"
class HandlerWorld(Handler):
    def process_msg(self, content):
        pass
