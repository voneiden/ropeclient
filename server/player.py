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
import re, db, world, time, random

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
            'spawn':self.handleCharacterSpawn,
            'look':self.handleLook,
            'style':self.handleStyle,
            'say':self.handleSay,
            'color':self.handleColor,
            'attach':self.handleAttach,
            'a':self.handleAttach,
            'detach':self.handleDetach,
            'd':self.handleDetach
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
        message = message.replace('$(','')
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

        
    def getName(self):
        if self.character:
            return "<%s>%s<reset>"%(self.character.color,self.account.name)
        else:
            return self.account.name    
    
        
    def send(self, message):
        ''' This function will also do some parsing stuff! '''
        if self.character:
            message = self.character.parse(message)
        self.connection.sendMessage(message)
        
    def offtopic(self, message):
        #self.connection.write('oft %f %s'%(time.time(),message))
        self.send("(%s"%message)
        
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
                return "Your <red>password<reset>?"   
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
            if len(message[0]) < 1: return
            if message[0][0].lower() == 'y':
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return "What would your <red>password<reset> be?"
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
            newcharacter.invisible = True
            newcharacter.soul = True
            
            newcharacter.attach(self)
        elif isinstance(character,world.Character):
            character.attach(self)
        # Todo handle disconnects properly..
        self.world.addPlayer(self)
        self.handler = self.gameHandler
        print "Sending clk"
        #self.connection.write("clk test;yellow;/testing;Click here to test a command!")
        self.send("Howabout $(clk2cmd:test;yellow;/testing;you click here)?")
        
    def gameHandler(self, tok):
        if self.character and len(tok) > 0:
            for command in self.commands.keys():
                if self.account.style == 1:
                    if re.search("^%s"%command,tok[0]):
                        return self.commands[command](tok)
                    if re.search("/^%s"%command,tok[0]): # For compatibility with click triggers.
                        return self.commands[command](tok)
                elif self.account.style == 0:
                    if re.search("^/%s"%command,tok[0]):
                        return self.commands[command](tok)
                
                    
            if tok[0][0] == '(':
                return self.handleOfftopic(tok)
            
            if self.account.style == 0: 
                return self.handleSay(tok)
                
    def characterSpawner(self,message):
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
            newchar = world.Character(self.world,self.account.name,
                                      self.temp['name'],self.temp['info'],
                                      self.temp['description'],
                                      self.character.location)
            #newchar.move(self.character.location)
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
            buffer.append("%s is here."%chars[0].rename)
        else:
            chars = loc.characters[:]
            chars.remove(self.character)
            buffer.append("%s are here."%(", ".join([char.rename for char in chars])))
        self.send("\n".join(buffer))
        
    def handleCharacterSpawn(self, tok):
        if self.gamemaster:
            self.handler = self.characterSpawner
            self.handlerstate = 0
            self.temp = {}
            return self.handler(None)
        else:
            return "(Not authorized"
        
    def handleOfftopic(self, tok):
        if tok[-1][-1] == ')': 
            tok[-1] = tok[-1][:-1]
        message = "(%s: %s"%(self.getName()," ".join(tok)[1:])
        self.world.message(self.world.characters,message)
        
    def handleSay(self, tok):
        if not self.character.mute:
            if self.account.style:
                message = " ".join(tok[1:])
            else:
                message = " ".join(tok)    
            self.character.location.announce('''%s says, "%s"'''%(self.character.name, message))
        else:
            self.offtopic("You are mute! You can't talk")
        
    def handleShout(self, tok):
        pass
        
    def handleCreate(self, tok):
        pass
        
    def handleGM(self, tok):
        if len(tok) < 2:
            key = ''
        else:
            key = tok[1]
            
        if key == self.core.gmKey or self.gamemaster:
            self.gamemaster = not self.gamemaster
            self.db.save()
            if self.gamemaster:
                return "(GM status enabled"
            else:
                return "(GM status disabled"
        else:
            self.send("(Not authorized")
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
        self.db.save()
        if self.account.style: return "You are now using MUD-style"
        else: return "You are now using IRC-style"
        
    def handleColor(self,tok):
        if len(tok) < 2:
            return "(Define the color"
        else:
            self.character.color = tok[1]
            return "(Color set to %s."%tok[1]
            
    def handleDetach(self,tok):
        if self.character:
            if self.character.soul:
                return "(You cannot detach from your soul!"
            else:
                location = self.character.location
                
                
                chars = self.world.findOwner(self.account.name,self.world.characters)
                for char in chars:
                    if char.soul:
                        self.character.detach()
                        char.attach(self)
                        self.character.move(location)
                        return "(Your soul has left the body"
                return "Oh god, we lost your soul. This is bad!!!!!"
                    
                        
                        
    # Todo don't allow to attach to already attached characters..
    # Todo attaching messages should be delivered to other players in question    
    def handleAttach(self,tok):
        # Param verification
        print "Handling attach:",tok
        if len(tok) < 2: return "(<red>Whom do you want to attach to?"
        targetname = " ".join(tok[1:])
        player = self
        if len(tok) > 3:
            if tok[2].lower() == 'to':
                if not self.gamemaster: return "(<red>You're not allowed to attach others"
                playername = tok[1]
                player = self.world.find(playername,self.world.players)
                targetname = " ".join(tok[3:])
                if not isinstance(player,Player):
                    return "(<red>The player you wanted to attach was not found"
        
        
        
        print "Trying to attach %s to %s"%(player.name,targetname)
        
        char = self.world.find(targetname,self.world.characters)
        if isinstance(char,world.Character):
            if char.owner == player.account.name or self.gamemaster:
                if char.soul:
                    return "(<red>You cannot attach to a soul"
                if char.player:
                    return ("<red>This character is already possessed by someone..")
                player.character.detach()
                char.attach(player)
                return 
            else:
                return "(<red>You cannot attach to something you do not own!"
        else:
            return "(<red>Couldn't find %s"%targetname
        

