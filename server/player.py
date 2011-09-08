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
    Player class handles client input and a big
    part of the game logic (currently)
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
        self.recv = self.recvHandshake
        
        
    def __getstate__(self): 
        """ Players will never be pickled when world is saved as they contain references to networking """
        return None

    def recvIgnore(self, message):
        ''' This function simply ignores all received data '''
        pass
    
    def recvHandshake(self,message):
        ''' This function receives the handshake and gets angry at the client if its wrong '''
        message = message.strip()
        tok = message.split()
        
        if tok[0] == 'hsk' and len(tok) > 1:
            if tok[1] != self.core.version:
                self.send("Your version of ropeclient (%s) is not" +
                          " compatible with this server (%s)" % (tok[1],
                          self.core.version))
                self.recv = self.recvIgnore
            else:
                self.recv = self.recvMessage
        else:
            self.send("Hi, you're not supposed to be here, are you? :)")
            self.recv = self.recvIgnore
    
    def recvMessage(self, message):
        print "Recv", message
        message = message.strip()
        message = message.replace('$(','')
        tok = message.split()
        if tok[0] == 'msg':
            response = self.handler(tok[1:])
            print "Got resp",response
            print "Type",type(response)
            if type(response) is str or type(response) is unicode:
                self.send(response)
            self.typing = False
            self.world.updatePlayer(self)

        elif tok[0] == 'pnt':
            self.typing = False
            self.world.updatePlayer(self)

        elif tok[0] == 'pit':
            self.typing = True
            self.world.updatePlayer(self)
        

        
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
    

    ''' DEV: this function should possibly be removed '''    
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
                return "Your <f>password<reset>?"   
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
        self.name = self.account.name
        old = self.world.find(self.account.name,self.world.players)
        print "Looking for old",old
        if isinstance(old,Player):
            print "OLD HAS BEEN FOUND, DISCONNECTING"
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
        #self.send("Howabout $(clk2cmd:test;yellow;/testing;you click here)?")
        
    ''' New dev version gameHandler '''
    def gameHandler(self, tok):
        # style 0 is irc style, style 1 is mud style?
        if self.character and len(tok) > 0:
            if not self.account.style and tok[0][0] != '/': #IRC STYLE
                return self.handle_say(tok)
            elif not self.account.style:
                command = tok[0][1:]
            elif self.account.style:
                command = tok[0]
            if self.account.style and command[0] == '/': #Combatibility for /memorize command
                command = command[1:]
                
            command = "handle_%s"%command
            print "gameHandler: Searching for command",command
            print locals().keys()
            try:
                handle = getattr(self,command)
            except AttributeError:
                handle = False
            if handle:
                return handle(tok[1:]) # I assume we can drop the original trigger..
                
            elif tok[0][0] == '(':
                return self.handle_offtopic(tok)
            elif tok[0][0] == '#':
                return self.handle_describe(tok)
            elif self.handle_move(tok):
                return

    
    # Changing it so that a character is owned by whoever last was attached to it.            
    def characterSpawner(self,message):
        ''' This is a handler for character generation '''
        self.handlerstate += 1
        if isinstance(message,list):
            msg = " ".join(message)
            
        if self.handlerstate  == 1:
            return "Name of this character ?"

            
        elif self.handlerstate == 2:
            char = self.world.find(msg,self.world.characters)
            if not char:
                self.temp['name'] = msg
                return "Describe with a few words (max 5)"
            else:
                self.handlerstate -= 1
                return "Character name already exists!"
        elif self.handlerstate == 3:
            if len(message) > 5 or len(msg) < 3:
                self.handlerstate -= 1
                return "Try again.."
            self.temp['info'] = msg
            return "Long description? You may write it later too."
        elif self.handlerstate == 4:
            self.temp['description'] = msg
            newchar = world.Character(self.world,self.account.name,
                                      self.temp['name'],self.temp['info'],
                                      self.temp['description'],
                                      self.character.location)
            #newchar.move(self.character.location)
            self.handler = self.gameHandler
            return "Done"
    
    def locationCreator(self,tok):
        self.handlerstate += 1
        print "Locreator",tok
        print type(tok)
        msg = " ".join(tok)
        #if len(msg) < 1: return "Answer the damn question" 
        
        if self.handlerstate == 1:
            return "Name of the location?"
        elif self.handlerstate == 2:
            self.temp['name']= msg
            return "Description of the location?"
            
        elif self.handlerstate == 3:
            self.temp['description'] = msg
            return "Link exitname;returnname (Enter=No linking)"
            

        elif self.handlerstate == 4:
            if len(msg) == 0: 
                link = False
            else:
                link = msg.split(';')
                if len(link) != 2:
                    self.handlerstate -= 1
                    return "Invalid answer"
                
            
            newlocation = world.Location(self.world,self.temp['name'],self.temp['description'])
            if link:
                self.character.location.link(link[0],newlocation,link[1])
            self.world.locations.append(newlocation)
            self.handler = self.gameHandler
            return "Done"
    # ######################
    # Player related handles
    # ######################
    def handle_gm(self, tok):
        key = " ".join(tok)
        print "Testing",key
        if key == self.core.gmKey or self.gamemaster:
            self.gamemaster = not self.gamemaster
            self.db.save()
            if self.gamemaster:
                return "(GM status enabled"
            else:
                return "(GM status disabled"
        else:
            self.send("(Not authorized")
            


 
    def handle_chars(self, tok):
        print "Listing chars"
        ownedchars = self.world.findOwner(self.account.name,self.world.characters)
        buffer = []
        if ownedchars == None: 
            buffer.append("(You own no characters!")
        else:
            buffer = ["You own the following characters"]
            for char in ownedchars:
                name = char.name + " "*(10-len(char.name))
                if char == self.character:
                    buffer.append("<green>%s <talk>- %s"%(name,char.info))
                else:
                    buffer.append("<blue>%s <talk>- %s"%(name,char.info))
        
        if self.gamemaster:
            otherchars = set(self.world.characters)-set(ownedchars)
            if len(otherchars) > 0:
                buffer.append("- - - - - - - - - - - - - - - - - - - - - - - -")
                buffer.append("In addition, following other characters exist..")    
                for char in otherchars:
                    name = char.name + " "*(10-len(char.name))
                    buffer.append("<yellow>%s <talk> - %s"%(name,char.info))
        return "\n".join(buffer)
        
    def handle_introduce(self, tok):
        if len(tok) < 1: return "Introduce as who?"
        name = " ".join(tok)
        if len(name) < 2: return "Introduce as who?"
        self.character.introduce(name)
        
    def handle_memorize(self, tok): #TODO FIX
        if len(tok) < 2: 
            return "(<fail>Usage: memorize StaticID name"
        
        ident = tok[0]
        
        if ident not in self.world.idents.keys():
            return "(<fail>StaticID not found."
        
        character = self.world.idents[ident]
        if not isinstance(character,world.Character):
            return "(<fail>StaticID refered to a non-character"
            
        name   = " ".join(tok[1:])
        self.character.memory[character] = name
        return "(<ok>Memorized %s"%name
        
        
    def handle_color(self,tok):
        if len(tok) < 2:
            return "(Define the color"
        else:
            self.character.color = tok[1]
            return "(Color set to %s."%tok[1]
          
    def handle_attach(self,tok): 
        regex1 = "(.+?) to (.+)"
        msg = " ".join(tok)
        search = re.search(regex1,msg)
        if search:
            groups = search.groups()
            playerName = groups[0]
            characterName = groups[1]
            player    = self.world.find(playerName,self.world.players)
        else:
            player = [self]
            characterName = msg
        
        if not player:
            return "(<fail>Could not find player"
        else:
            player = player[0]
            
        character = self.world.find(characterName,self.world.characters)
        if not character:
            return "(<fail>Could not find character"
        else:
            character = character[0]
            
        if character.owner is not player.account.name and not self.gamemaster:
            return "(<fail>You may not attach to this character"
        
        if character.player:
            return "(<fail>Somebody is currently playing with this character. Detach them first?"
        
        player.character.detach()
        character.attach(player)
        
        if player is not self:
            return "(<ok>Attach succesful!"
        return
            
            
    def handle_style(self,tok):
        self.account.style = not self.account.style
        self.db.save()
        if self.account.style: return "You are now using MUD-style"
        else: return "You are now using IRC-style"
        
    def handle_detach(self,tok):
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
 
    def handle_locs(self, tok):
        print "Listing locations"
        buf = ["<green>Dynamic ID - Static  ID - Location name"]
        for loc in self.world.locations:
            ident = loc.id()
            dynid = ident[0] + ' '*(10-len(ident[0]))
            staid = ident[1] + ' '*(10-len(ident[1]))
            buf.append("<green>%s - %s <grey>- <spring green>%s"%(dynid,staid,loc.name))
        self.offtopic('\n'.join(buf))
    
    # #####################
    # World related handles
    # #####################
    def handle_look(self, tok):
        regex1 = '(?<=look ).+'
        match = re.search(regex1," ".join(tok))
        buffer = ['']
        
        if match:
            charname = match.group()
            char = self.world.findAny(charname,self.character.location.characters)
            if not char or not isinstance(char,world.Character): return "(<fail>There is no one with that id here (%s).."%charname
            buffer.append("Looking at %s.."%char.rename)
            buffer.append("%s"%char.description)
            return "\n".join(buffer)
            
        else:
            loc = self.character.location
            buffer.append("<purple>%s<reset>"%loc.name)
            buffer.append("<light sky blue>%s<reset>"%loc.description)
         
            chars = []
            for char in loc.characters:
                if char.invisible: continue
                elif char == self.character: continue
                else:
                    chars.append(char)
            
            print "Chars",len(chars)
            if len(chars) == 0:
                buffer.append("<turquoise>You are alone<reset>")
            elif len(chars) == 1:
                buffer.append("<turquoise>%s is here.<reset>"%chars[0].rename)
            else:
                buffer.append("<turquoise>%s and %s are here.<reset>"%(", ".join([char.rename for char in chars[:-1]]),chars[-1].rename))
            
            if len(loc.exits) == 0:
                buffer.append("<ok>There are no obvious exits..</cyan>")
            elif len(loc.exits) == 1:
                buffer.append("<ok>Only one exit: %s"%loc.exits.keys()[0])
            else:
                buffer.append("<ok>Exits: %s"%", ".join(loc.exits.keys()))
        
        #self.send("\n".join(buffer))
        return "\n".join(buffer)
          
    def handle_spawn(self, tok):
        ''' This command is used to spawn new characters '''
        if self.gamemaster:
            self.handler = self.characterSpawner
            self.handlerstate = 0
            self.temp = {}
            return self.handler(None)
        else:
            return "(Not authorized"
            
    def handle_create(self, tok):
        if self.gamemaster:
            self.handler = self.locationCreator
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return "(Not authorized"
    
    # #########################
    # Character related handles
    # #########################
    def handle_move(self,tok):
        if len(tok) > 0:
            print "Trying to move to",tok
            dir = tok[0].lower()
            for exit in self.character.location.exits.keys():
                if dir in exit.lower():
                    destination = self.character.location.exits[exit]
                    self.character.move(destination)
                    return True

            return False
        else:
            return False
            
    def handle_action(self,tok):
        if len(tok) > 1:
            message = " ".join(tok[1:])
            self.character.location.announce('''%s %s'''%(self.character.rename, message))
        
    def handle_describe(self,tok):
        if tok[0][0] == '#':
            tok[0] = tok[0][1:]
            message = " ".join(tok)
        else:
            message = " ".join(tok[1:])
        self.character.location.announce("""%s (%s)"""%(message, self.account.name))
        
    def handleShortDescription(self,tok):
        pass
        
    def handleLongDescription(self,tok):
        pass
        
    def handleGender(self,tok):
        pass

    
    
        
    def handle_offtopic(self, tok):
        if tok[-1][-1] == ')': 
            tok[-1] = tok[-1][:-1]
        if tok[0][0] == '(':
            tok[0] = tok[0][1:]
        message = "(%s: %s"%(self.getName()," ".join(tok))
        self.world.message(self.world.characters,message)
        
    def handle_say(self, tok):
        if not self.character.mute:
            if self.account.style:
                message = " ".join(tok[1:])
            else:
                message = " ".join(tok)
            
            if message[-2:] == ':)': 
                says = "smiles and says"
                message = message[:-2].strip()
            elif message[-2:].upper() == ':D':
                says = "laughingly says"
                message = message[:-2].strip()
            elif message[-2:] == ':(':
                says = "looks grim and says"
                message = message[:-2].strip()
            elif message[-1] == '!':
                says = "exclaims"
            else:
                says = 'says'
                # had color #8888ff
            self.character.location.announce('''%s %s, "%s"'''%(self.character.rename, says, message))
        else:
            #self.offtopic("You are mute! You can't talk")
            self.handle_offtopic(tok)
        
    def handle_shout(self, tok):
        pass
        
    def handle_teleport(self,tok):
        print "Trying to teleport.."
        regex1 = "(.+?) to (.+)"
        msg = " ".join(tok[1:])
        print "Command",msg
        search = re.search(regex1,msg)
        if search:
            print "SEARCH OK"
            groups = search.groups()
            charname = groups[0]
            targetname = groups[1]
            
            char = self.world.findAny(charname,self.world.characters)
            if not char: return ("Unable to find a character by identification: %s"%charname)
            target = self.world.findAny(targetname,self.world.locations)
            if not target: return ("Unable to find the target: %s"%targetname)
            
            char.move(target)
            return ("(<ok>Teleport succesful!")
        return "(<fail>Search failed"

    
    def handle_world(self,tok):
        if not self.gamemaster: return "(<fail>This command requires GM rights"
        if len(tok) < 1: return "(<fail>Usage: world name/save/load"
        if tok[0] == 'name' and len(tok) > 1: 
            self.world.name = " ".join(tok[1:])
            return "(<ok>World name set to %s."%(self.world.name)
        elif tok[0] == 'save':
            self.world.save()
            return "(<ok>World saved."
        elif tok[0] == 'load' and len(tok) > 2:
            if self.world.load(self.core," ".join(tok[1:])):
                return "(<ok>Load (%s) succesful."%self.world.name
            else:
                return "(<fail>Load failed."
                
            
    def handle_tell(self,tok):
        if len(tok) > 2:
            targetname = tok[1]
            message = " ".join(tok[2:])
            target = self.world.findAny(targetname,self.character.location.characters)
            if not target: return "(<fail>%s is not here.."%targetname
            self.world.message(target,'''%s whispers to you, "%s"'''%(self.character.rename, message))
            return '''You whisper to %s, "%s"'''%(target.rename,message)
        else:
            return "(<fail>Invalid arguments: /tell charname message"
    
    def handle_notify(self,tok):
        if len(tok) > 2 and self.gamemaster:
            targetname = tok[1]
            message = " ".join(tok[2:])
            target = self.world.findAny(targetname,self.character.location.characters)
            if not target: return "(<fail>%s is not here.."%targetname
            self.world.message(target,'''<notify>%s: %s'''%(self.account.name, message))
            return '''<notify>@%s: "%s"'''%(target.name,message)        
        else:
            return "(<fail>Invalid arguments: /tell charname message, or you're not GM"
            
    def handle_unlink(self,tok):
        if self.gamemaster:
            self.handler = self.linkRemover
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return "(Not authorized"
    def linkRemover(self,tok):
        self.handlerstate += 1
        print "linkremover",tok
        print type(tok)
        msg = " ".join(tok)
        #if len(msg) < 1: return "Answer the damn question" 
        
        if self.handlerstate == 1:
            return "Name of the link to remove?"
        elif self.handlerstate == 2:
            self.temp['linkto']= msg
            return "Remove return also?"
            
        elif self.handlerstate == 3:
            if len(msg) == 0:
                both = False
            else:
                both = True
                
            self.handler = self.gameHandler
            return self.character.location.unlink(self.temp['linkto'],both)
            
            
    def handle_link(self,tok):
        if self.gamemaster:
            self.handler = self.linkCreator
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return "(Not authorized"
    def linkCreator(self,tok):
        self.handlerstate += 1
        print "linkcreator",tok
        print type(tok)
        msg = " ".join(tok)
        #if len(msg) < 1: return "Answer the damn question" 
        
        if self.handlerstate == 1:
            return "Name of the link?"
        elif self.handlerstate == 2:
            self.temp['linkto']= msg
            return "Target location?"
            
        elif self.handlerstate == 3:
            self.temp['location'] = msg
            return "Return link (Enter=No linking)"
            

        elif self.handlerstate == 4:
            if len(msg) == 0: 
                backlink = False
            else:
                backlink = msg
                
            self.handler = self.gameHandler
            location = self.world.findAny(self.temp['location'],self.world.locations)
            if not location:
                return "(<fail>Unable to link - location not found"
            
            self.character.location.link(self.temp['linkto'],location,backlink)
            return "(<ok>Done"
