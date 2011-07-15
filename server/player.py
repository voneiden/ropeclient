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
        self.name = "Undefined!"
        self.password = None
        self.account = None
        self.typing = False
        self.handler = self.loginHandler
        self.character = None
        self.gamemaster = False
        self.handlerstate = 1
        self.temp = {}
        
        self.commands = {
            'chars':self.handleCharlist,
            'intro':self.handleIntroduce,
            'memorize':self.handleMemorize,
            'gm':self.handleGM,
            'spawn':self.handleSpawn,
            'look':self.handleLook,
            'style':self.handleStyle
            }
        
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
        '''
        State 1 - asking for name
        State 2 - asking for password
        State 10 - asking for new account verification
        State 11 - asking for new account password
        State 12 - asking one more time for password
        '''
        if self.handlerstate == 1:
            self.temp['name'] = message[0]
            find = self.db.find(message[0],self.db.accounts)
            if isinstance(find,db.Account):
                self.handlerstate = 2
                self.account = find
                self.connection.write('pwd\r\n')
                return "Your password?"   
            elif find == None:
                if re.match("^[A-Za-z]+$", message[0]):
                    self.handlerstate = 10
                    return "Would you like to create a new account under the name '%s' yes/no?"%message[0]
                else:
                    return "This account name contains invalid characters - Try again"
             
        
        elif self.handlerstate == 2:
            if message[0] == self.account.password:
                return self.login()
            else:
                self.connection.disconnect()
                
        elif self.handlerstate == 10:
            if message[0][0].lower() == 'y':
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return "What would your password be?"
            else:
                self.handlerstate = 1
                return "What is your name?"
                
        elif self.handlerstate == 11:
            self.temp['password'] = message[0]
            self.handlerstate = 12
            self.connection.write('pwd\r\n')
            return "Please retype"
            
        elif self.handlerstate == 12:
            if self.temp['password'] == message[0]:
                print "New accont with",self.temp['name'],self.temp['password']
                self.account = db.Account(self.temp['name'],self.temp['password'])
                self.db.accounts.append(self.account)
                self.db.save()
                self.login()
            else:
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return "Password mismatch, try again! Your password?"
    
    
    def disconnect(self):
        if self.character: self.character.detach()
        self.world.remPlayer(self)
        self.send("You are being logged out because you logged in elsewhere.")
        self.connection.transport.loseConnection()
        
    def login(self):
        # We need to check for old player connections and disconnect them.
        old = self.world.find(self.account.name,self.world.players)
        print "Looking for old",old
        if isinstance(old,Player):
            old.disconnect()
        
        self.name = self.account.name 
        character = self.db.findOwner(self.account.name,self.core.world.characters)
        if character == None:
            newcharacter = world.Character(self.world,self.account.name,"Soul of %s"%(self.account.name))
            newcharacter.mute = True
            newcharacter.attach(self)
        elif isinstance(character,world.Character):
            character.attach(self)
        # Todo handle disconnects properly..
        self.world.addPlayer(self)
        self.handler = self.gameHandler
        print "Sending clk"
        self.connection.write("clk test;yellow;/testing;Click here to test a command!")
        
    def gameHandler(self, tok):
        if self.character:
            for command in self.commands.keys():
                if self.account.style == 0:
                    if re.search("^/%s"%command,tok[0]):
                        return self.commands[command](tok)
                elif self.account.style == 1:
                    if re.search("^%s"%command,tok[0]):
                        return self.commands[command](tok)
                    
            if tok[0][0] == '(':
                return self.handleOfftopic(tok)
                
            elif not self.character.mute:        
                self.character.location.announce('''%s says, "%s"'''%(self.character.name, " ".join(message)))
            else:
                message = "%s: %s"%(self.account.name," ".join(tok))
                self.world.offtopic(message)
                
    def gmSpawner(self,message):
        ''' This is a handler for character generation '''
        self.handlerstate += 1
        if isinstance(message,list):
            msg = " ".join(message)
            
        if self.handlerstate  == 1:
            return "Owner of this character (Enter=you)"
        elif self.handlerstate == 2:
            if msg == '':
                self.temp['owner'] = self.account.name
            else:
                self.temp['owner'] = msg
                
            return "Name of the character?"
            
        elif self.handlerstate == 3:
            self.temp['name'] = msg
            return "Describe with a few words?"
        elif self.handlerstate == 4:
            self.temp['info'] = msg
            return "Describe a bit longer?"
        elif self.handlerstate == 5:
            self.temp['description'] = msg
            newchar = world.Character(self.world,self.account.name,self.temp['name'],self.temp['info'],self.temp['description'])
            newchar.move(self.character.location)
            self.handler = self.gameHandler
            return "Done"
            
            
    def handleLook(self, tok):
        loc = self.character.location
        buffer = [loc.name]
        buffer.append(loc.description)
        if len(loc.characters) == 1:
            buffer.append("You're alone")
        elif len(loc.characters) == 2:
            chars = loc.characters[:]
            chars.remove(self.character)
            buffer.append("%s is here."%chars[0].name)
        else:
            chars = loc.characters[:]
            chars.remove(self.character)
            buffer.append("%s are here."%(", ".join(chars)))
        self.send("\n".join(buffer))
        
    def handleSpawn(self, tok):
        self.handler = self.gmSpawner
        self.handlerstate = 0
        self.temp = {}
        return self.handler(None)
        
    def handleOfftopic(self, tok):
        if tok[-1][-1] == ')': 
            tok[-1] = tok[-1][:-1]
        message = "%s: %s"%(self.account.name," ".join(tok)[1:])
        self.world.offtopic(message)
        
    def handleSay(self, tok):
        pass
        
    def handleShout(self, tok):
        pass
        
    def handleCreate(self, tok):
        pass
        
    def handleGM(self, tok):
        self.gamemaster = not self.gamemaster
        
    def handleCharlist(self, tok):
        print "Listing chars"
        chars = self.world.findOwner(self.account.name,self.world.characters)
        if chars == None: 
            return "You possess no characters.."
        
        buffer = ["You can possess the following characters"]
        if not isinstance(chars,list): 
            chars = [chars]
        
        for char in chars:
            if char == self.character:
                buffer.append("** %s - %s **"%(char.name,char.info))
            else:
                buffer.append("%s - %s"%(char.name,char.info))
        self.offtopic('\n'.join(buffer))
        
    def handleIntroduce(self, tok):
        name = " ".join(message[1:])
        if len(name) < 2: return "Introduce as who?"
        pass
        
    def handleMemorize(self, tok):
        pass
        
    def handleStyle(self,tok):
        self.account.style = not self.account.style
        if self.account.style: return "You are now using MUD-style"
        else: return "You are now using IRC-style"
        self.db.save()
