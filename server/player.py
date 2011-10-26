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

# Todo avoid deleting of souls somehow.. :D

import server,re, world, time, random

class Player(object):
    '''
    Player class handles client input and a big
    part of the game logic (currently)
    '''

    def __init__(self, connection, core):
        self.connection = connection    # RopePlayer class
        self.core = core                # Core class
        self.world = None               # Current world, None = menu
        self.name = None                # 
        self.account = None             # ?
        self.typing = False              
        self.handler = self.loginHandler# Current function that handles all input
        self.character = None           # Current character
        self.gamemaster = False         # Is gamemaster
        self.handlerstate = 1           # A counter used by some handlers
        self.temp = {}                  # Temporary storage for handlers
        self.recv = self.recvHandshake  # Function that parses & feeds handler
        
        
    def __getstate__(self): 
        """ Players will never be pickled when world is 
            saved as they contain references to networking """
        return None

    def recvIgnore(self, message):
        ''' This function simply ignores all received data '''
        pass
    
    def recvHandshake(self,message):
        ''' This function receives the handshake and gets 
            angry at the client if its wrong '''
        message = message.strip()
        tok = message.split()
        
        if tok[0] == 'hsk' and len(tok) > 1:
            if tok[1] != self.core.version:
                buf = ["<fail>Your version of ropeclient ({clientversion}) is ",
                       "not compatible with this server ({version}). Please ",
                       "get the latest updates from http://www.github.com",
                       "/voneiden/ropecilent - thanks!"]
                self.send("".join(buf).format(clientversion=tok[1],
                                              version=self.core.version))
                self.recv = self.recvIgnore
            else:
                self.send("Version up to date!")
                self.send("".join(self.core.greeting))
                self.recv = self.recvMessage
        else:
            self.send("Hi, you're not supposed to be here, are you? :) Curren" +
                      "tly logins are only supported by the official client")
            self.recv = self.recvIgnore
    
    def recvMessage(self, message):
        print "Recv", message
        message = message.strip()
        
        # To avoid players being able to create their own variables.. remove $(
        message = message.replace('$(','')
        tok = message.split()
        if tok[0] == 'msg':
            
            response = self.handler(tok[1:])
            
            
            print "Got resp",response
            print "Type",type(response)
            if type(response) is str or type(response) is unicode:
                self.send(response)
            self.typing = False
            #self.world.updatePlayer(self)

        elif tok[0] == 'pnt':
            self.typing = False
            if self.world:
                self.world.updatePlayer(self)

        elif tok[0] == 'pit':
            self.typing = True
            if self.world:
                self.world.updatePlayer(self)
        

        
    def getName(self): # Obsolete?
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
            if self.temp['name'].lower() in self.core.accounts:
                self.handlerstate = 2
                self.account = self.core.accounts[self.temp['name'].lower()]
                
                self.connection.write('pwd\r\n')
                return "Your <f>password<reset>?"   
            else:
                if re.match("^[A-Za-z]+$", message[0]):
                    self.handlerstate = 10
                    return "Would you like to create a new account under the name '{name}' yes/no?".format(name=message[0])
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
                self.handlerstate = 13
                f = open('text/stylehelp.txt','r')
                buf = [f.read()]
                buf.append("Choose your style (can be changed later!): irc/mud")
                f.close()
                
                return "\n".join(buf)                
                
            else:
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return "Password mismatch, try again! Your password?"
                
        elif self.handlerstate == 13:
            if message[0].lower() == 'irc':
                self.temp['style'] = 'irc'
            elif message[0].lower() == 'mud':
                self.temp['style'] = 'mud'
            else:
                return "Please choose <white>irc<reset> or <white>mud<reset>!"
            
            print "New accont with",self.temp['name'],self.temp['password']
            
            self.account = server.Account(self.temp['name'],self.temp['password'],self.temp['style'])
            self.core.accounts[self.account.name] = self.account
            self.core.saveAccounts()
            return self.login()
    
    
    def disconnect(self):
        if self.character: self.character.detach()
        if self.world: pass #TODO: world disconnected
        if self.name in self.core.players:
            del self.core.players[self.name]
            
        self.send("Disconnecting you, bye bye. (Either you quit or " +
                  "you may have logged in elsewhere).")
        self.connection.transport.loseConnection()
        
    def login(self):
        # We need to check for old player connections and disconnect them.
        # TODO: Needs to be remade.
        #self.name = self.account.name
        #old = self.world.find(self.account.name,self.world.players)
        #print "Looking for old",old
        #if isinstance(old,Player):
        #    print "OLD HAS BEEN FOUND, DISCONNECTING"
        #    old.disconnect()
        if self.name in self.core.players:
            print "Disconnecting old player"
            self.core.players[self.name].disconnect()
            
        self.clearMain()
        self.handler = self.menuHandler
        return self.displayWorldMenu()
            
        #self.name = self.account.name 
        #character = self.db.findOwner(self.account.name,self.core.world.characters)
        #if character == None:
        #    newcharacter = world.Character(self.world,self.account.name,"Soul of %s"%(self.account.name))
        #    newcharacter.mute = True
        #    newcharacter.invisible = True
        #    newcharacter.soul = True
        #    
        #    newcharacter.attach(self)
        #elif isinstance(character,world.Character):
        #    character.attach(self)
        # Todo handle disconnects properly..
        #self.world.addPlayer(self)
        #self.handler = self.gameHandler
        #print "Sending clk"
        #self.send(self.handle_look([]))
        #self.connection.write("clk test;yellow;/testing;Click here to test a command!")
        #self.send("Howabout $(clk2cmd:test;yellow;/testing;you click here)?")
        
        
        
    def clearMain(self):
        self.connection.write("clr main")
        
    def clearOfftopic(self):
        self.connection.write("clr offtopic")
            
        
    def displayWorldMenu(self):
        buf = []
        buf.append("Welcome to the edge of the universe. " + 
                   "Where is your soul headed to?")
        buf.append("")
        
        iw = len(self.core.worlds)
        if iw == 0:
            buf.append("Nobody has created a world yet..")
        else:
            # This is a crazy generator. Not for the weak of mind :-D
            buf+=["{i}) {name}{pw}{players}".format(
             i=self.core.worlds.index(world)+1,
             name=world.name,
             pw=" [password]" if world.pw else "",
             players= " ({0} players online)".format(len(world.players)) 
             if len(world.players) > 1 else 
             " (1 player online)" 
             if len(world.players) else 
             " (No players online)") for world in self.core.worlds]
             
            #for i,world in enumerate(worlds):
            #    buf.append("{0}) {1}".format(i,world))
        buf.append('')
        choice = []
        for i in range(len(self.core.worlds)): choice.append(str(i+1))
        choice.append("create")
        buf.append("To create a new world, type <white>create<reset>. To join, type the number of the world.")
        buf.append("[{0}]".format(", ".join(choice)))
        return "\n".join(buf)
            
    def menuHandler(self, tok):
        pass
        
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
   
        
        if self.handlerstate == 1:
            return "(Location title:"
        elif self.handlerstate == 2 and len(msg) > 2:
            self.temp['name']= msg
            return "(Location description:"
            
        elif self.handlerstate == 3:
            self.temp['description'] = msg
            return "(Exit name (enter for no exit):"
        
        elif self.handlerstate == 4:
            if len(msg):
                self.temp['exit'] = msg
            else:
                self.temp['exit'] = False
            return "(Return exit name (enter for no return exit):"
            
            

        elif self.handlerstate == 5:
            if len(msg): 
                rexit = msg
            else:
                rexit = False
                 
            newlocation = world.Location(self.world,self.temp['name'],self.temp['description'])
            if self.temp['exit']:
                self.character.location.link(self.temp['exit'],newlocation)
            if rexit:
                newlocation.link(rexit,self.character.location)
                
            self.handler = self.gameHandler
            return "(<ok>Location created (dynid: %s | staid: %s)"%(newlocation.dynid(),newlocation.ident)
            
        else:
            return "<fail>Not enough information"
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
            
    def handle_del(self,tok):
        if not self.gamemaster:
            return "(<fail>Not authorized"
        character = " ".join(tok)
        if len(character) == 0:
            return "(<fail>Usage: del charid"
        character = self.world.findAny(character,self.world.characters)
        if not character:
            return "(<fail>Character not found"
        else:
            character = character[0]
        if character.player:
            character.player.send("(<fail>Your character has been terminated!")
            character.detach()
        self.world.remCharacter(character)
        return "(<ok>Done."
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
                info = char.info[:20] + " "*(20-len(char.info[:20]))
                ident = char.id()
                dynid = ident[0] + ' '*(10-len(ident[0]))
                staid = ident[1] + ' '*(10-len(ident[1]))
                if char == self.character:
                    buffer.append("<green>%s<talk>- %s - %s - %s"%(name,info,dynid,staid))
                else:
                    buffer.append("<blue>%s<talk>- %s - %s - %s"%(name,info,staid,staid))
        
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
            location = self.character.location
            buffer.append("<purple>%s<reset>"%location.name)
            buffer.append("<light sky blue>%s<reset>"%location.description)
         
            characters = []
            for character in location.characters:
                if character.invisible: continue
                elif character == self.character: continue
                else:
                    characters.append(chararcter)
            
            print "Chars",len(characters)
            if len(characters) == 0:
                buffer.append("<turquoise>You are alone<reset>")
            elif len(characters) == 1:
                buffer.append("<turquoise>%s is here.<reset>"%characters[0].rename)
            else:
                buffer.append("<turquoise>%s and %s are here.<reset>"%(", ".join([character.rename for character in characters[:-1]]),characters[-1].rename))
            
            if len(location.links) == 0:
                buffer.append("<ok>There are is no obvious way out from here..</cyan>")
            elif len(location.links) == 1:
                buffer.append("<ok>This is a dead end, only one way out: %s"%location.links[0].name)
            else:
                buffer.append("<ok>Exits: %s"%", ".join([link.name for link in location.links]))
        
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
            name = tok[0].lower()
            link = self.character.location.findLink(name=name)
            if link:
                self.character.move(link.destination)
                return True
            else:
                return False
            #for exit in self.character.location.exits.keys():
            #    if dir in exit.lower():
            #        destination = self.character.location.exits[exit]
            #        self.character.move(destination)
            #        return True

            #return False
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
        ''' TP function, allows chars to be moved to locations '''
        ''' ex1: tp 0 --- Teleport to location with dynid 0 '''
        ''' ex2: tp xxx to yyy --- Teleport character xxx to location with name/id yyy'''
        aregex = '^\d+$'   # tp 0
        bregex = '^(.+?) to (\d+)$'
        cregex = '^(.+?) to (.+)$'
        msg = " ".join(tok)
        if re.search(aregex,msg):
            character = self.character.ident
            location  = msg
            
        else:
            bsearch = re.search(bregex,msg)
            csearch = re.search(cregex,msg)
            if bsearch:
                groups = bsearch.groups()
                character = groups[0]
                location = groups[1]
            elif csearch:
                groups = csearch.groups()
                character = groups[0]
                location = groups[1]
            else:
                return "(<fail>Usage: teleport [locationid] OR teleport [charactername] to [locationid/locationname]"
        

        character = self.world.findAny(character,self.world.characters)
        location  = self.world.findAny(location,self.world.locations)
        
        if not character:
            return "(<fail>Character could not be resolved"
        if not location:
            return "(<fail>Location could not be resolved"
       
        character[0].move(location[0])
        if self.character != character[0]:
            if character[0].player:
                character[0].player.send("(<ok>You have been teleported")
        return "(<ok>Teleport succesful"
        

    def handle_tp(self,tok):
        return self.handle_teleport(tok)
    
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
