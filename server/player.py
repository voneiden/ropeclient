#!/usr/bin/python2
# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


    Copyright 2010-2011 Matti Eiden <snaipperi()gmail.com>

'''
import re, db, world, time

class Player(object):
    '''
    Player is the standard class that handles basic client processing
    Player can be attached to various characters, or if unattached, it
    will be just a soul floating in space. Souls, unless GM's, may only
    send offtopic messages.
    '''

    def __init__(self, connection, core):
        self.connection = connection
        self.core = core
        self.world = self.core.world
        self.db = self.core.db
        self.name = 'Unknown'
        self.password = None
        self.account = None
        self.typing = False
        self.handler = self.loginHandler
        self.character = None
        self.gamemaster = False

    def __getstate__(self): 
        """ Players will never be pickled as they contain references to networking """
        return None

    def recvIgnore(self, message):
        pass

    def recv(self, message):
        self.typing = False
        self.world.updatePlayer(self)
        
        print "Recv", message
        message = message.strip()
        tok = message.split(' ')
        if tok[0] == 'msg':
            response = self.handler(tok[1:])
            print "Got resp",response
            print "Type",type(response)
            if type(response) is str or type(response) is unicode:
                self.send(response)

        elif tok[0] == 'pnt':
            self.typing = False
            self.world.updatePlayer(self)

        elif tok[0] == 'pit':
            self.typing = True
            self.world.updatePlayer(self)
        
        # Todo: maybe handshake should be mandatory before accepting any other comms..
        elif tok[0] == 'hsk':
            if tok[1] != self.core.version:
                self.send("Your version of ropeclient (%s) is not" +
                          " compatible with this server (%s)" % (tok[1],
                          self.core.version))
                self.recv = self.recvIgnore

        #self.send(None, message)

        
        
    
        
    def send(self, message):
        ''' This function will also do some parsing stuff! '''
        self.connection.sendMessage(message)
        
    def offtopic(self, message):
        self.connection.write('oft %f %s'%(time.time(),message))
        
    
        
    def loginHandler(self, message):
        """ Message is tokenized! """
        """ 
            self.username == 'Unknown' means the user is not authenticated at all
            self.username == (False,Name) means the user account does not exist
            self.username == (Password,Name) means the user has given a new password, verify and create account
        """
        if self.name == 'Unknown':
            if len(message) == 1:
                find = self.db.find(message[0],self.db.accounts)
                #print self.db.accounts
                #print self.db.accounts[0].name
                #print find
                if isinstance(find,db.Account):
                    self.name = find.name
                    self.account  = find
                    self.connection.write('pwd\r\n')
                    return "Your password?"

                elif re.match("^[A-Za-z]+$", message[0]):
                    self.name = (False,message[0])
                    return "The account you typed does not exist. Would you like to create a new account by the name '%s'?" % message[0]
                else:
                    return "This not ok"
            else:
                return "This not ok length"
        else:
            if type(self.name) == tuple and len(message[0]) > 0:
                if self.name[0] == False:
                    if message[0][0].lower() == 'y':
                        self.name = (True,self.name[1])
                        # Todo: request password type
                        self.connection.write('pwd\r\n')
                        return "Choose your password"
                    else:
                        self.name = 'Unknown'
                        return "Who are you then?"
                elif self.password == None:
                    print "Got pwd",message
                    self.password = message[0]
                    self.connection.write('pwd\r\n')
                    return "Please retype your password.."
           
                else:
                    if self.password == message[0]:
                        self.account = db.Account(self.name[1],self.password)
                        self.db.accounts.append(self.account)
                        self.name = self.account.name
                        self.db.save()
                        return self.login()
                    else:
                        self.password = None
                        self.connection.write('pwd\r\n')
                        return "Passwords mismatch, try again. Choose your password"
            else:
                if message[0] == self.account.password:
                    return self.login()
                    
                else:
                    self.connection.disconnect()
    def disconnect(self):
        if self.character: self.character.detach()
        self.world.remPlayer(self)
        self.send("You are being logged out because you logged in elsewhere.")
        self.connection.transport.loseConnection()
        
    def login(self):
        # We need to check for old player connections and disconnect them.
        old = self.world.find(self.name,self.world.players)
        print "Looking for old",old
        if isinstance(old,Player):
            old.disconnect()
    
        character = self.db.findOwner(self.name,self.core.world.characters)
        if character == None:
            newcharacter = world.Character(self.world,"Soul of %s"%(self.name),self.account.name)
            newcharacter.mute = True
            newcharacter.attach(self)
        elif isinstance(character,world.Character):
            character.attach(self)
        # Todo handle disconnects properly..
        self.world.addPlayer(self)
        self.handler = self.gameHandler
        print "Sending clk"
        self.connection.write("clk test;yellow;/testing;Click here to test a command!")
        
    def gameHandler(self, message):
        if self.character:
            if message[0][0] == '(':
                if message[-1][-1] == ')': 
                    message[-1] = message[-1][:-1]
                message = "%s: %s"%(self.name," ".join(message)[1:])
                self.world.offtopic(message)
            
            elif message[0] == '/chars':
                print "Listing chars"
                chars = self.world.findOwner(self.name,self.world.characters)
                if chars == None: 
                    self.offtopic("You possess no characters..")
                    return
                buffer = ["You can possess the following characters"]
                if not isinstance(chars,list): 
                    chars = [chars]
                for char in chars:
                    if char == self.character:
                        buffer.append("** %s - %s **"%(char.name,char.info))
                    else:
                        buffer.append("%s - %s"%(char.name,char.info))
                self.offtopic('\n'.join(buffer))
                
            elif message[0] == '/introduce':
                pass
            elif message[0] == '/memorize':
                pass
                
            elif not self.character.mute:        
                self.character.location.announce('''%s says, "%s"'''%(self.character.name, " ".join(message)))
            else:
                message = "%s: %s"%(self.name," ".join(message))
                self.world.offtopic(message)
