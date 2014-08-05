import logging

#import server

class Handler(object):
    def __init__(self, player):
        self.player = player
        self.core = player.core
        
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
        
    def process_pwd(self, content):
        return False
        
    def process_nan(self, content):
        logging.error("Undefined cmd in message content")


class HandlerLogin(Handler):
    """
        state 0 msg - receiving username

    """
    def __init__(self, player):
        """

        @param player:
        @type player: server.WebPlayer
        @return:
        """
        Handler.__init__(self, player)
        self.state = 0
        self.name = None
        self.password = None
        self.ident = None

       
    def process_msg(self, message):
        logging.info(message)
        if len(message["value"]) == 0:
            return
            
        # State 0 - Received username
        if self.state == 0: 
            self.name = message["value"]

            # Test max length
            if len(self.name) > self.player.core.settings["max_login_name_length"]:
                self.player.send_message_fail("Login name is too long. Your name?")
                return

            # Test account has only characters
            if not self.name.isalpha():
                self.player.send_message_fail("Login name may not contain numbers or special characters. Your name?")
                return

            # Test if account exists
            ident = self.core.players.hget("names", self.name.lower())
            if ident:
                self.ident = ident
                self.player.send_message("Account found!")
                self.state = 1
                self.player.send_message("Password?")
                self.player.send_password()
                return
            else:
                self.player.send_message("Account not found! Create a new one? (y/n)")
                self.state = 10
                return

        elif self.state == 10:
            if message["value"][0].lower() == "y":
                self.state = 11
                self.player.send_message("Password?")
                self.player.send_password()
            else:
                self.state = 0
                self.player.send_message("Your name?")

        else:
            self.player.send_message("Something went wrong, restarting. Your name?")
            self.state = 0

    def process_pwd(self, pwd):
        if len(pwd["value"]) == 0:
            return

        if self.state == 1:
            player = self.core.players.fetch(self.ident)

            if pwd["value"] == player.get("password"):
                self.player.send_message("Password correct!")

                # Link connection and player interface together
                player.connection = self.player

                # This sets the WebPlayers player attribute to point to the player interface (awkward..)
                self.player.player = player

                # Create handler for player interface
                player.handler = HandlerWorld(player)

            else:
                self.player.send_message("Password incorrect!")



        elif self.state == 11:
            self.password = pwd["value"]
            logging.info("Got pwd: {}".format(self.password))
            self.player.send_message("Repeat password")
            self.player.send_password()
            self.state = 12

        elif self.state == 12:
            if self.password == pwd["value"]:
                self.core.players.new(self.name, self.password)
                self.player.send_message("Account created. You may now login. Your name?")
                self.state = 0
            else:
                self.player.send_message("Passwords mismatch. Try again. Your password?")
                self.player.send_password()
                self.state = 11

        else:
            self.player.send_message("Something went wrong, restarting. Your name?")
            self.state = 0
        
        
    def handler_login(self, header, message):
        '''
        THIS FUNCTION IS NOT USED ANYMORE
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
                
                self.connection.write('pwd\r\n') #TODO
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
        self.player.send_message("You are now in the world handler")

