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
# TODO input should be checked for invalid characters more often..

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
        self.name = None                # On login, accunt.name
        self.account = None             # Kind of unnecessary..
        self.typing = 0              
        self.handler = self.handlerLogin# Current function that handles all input
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
                self.sendMessage("".join(buf).format(clientversion=tok[1],
                                              version=self.core.version))
                self.recv = self.recvIgnore
            else:
                self.clearOfftopic()
                self.sendMessage("Version up to date!")
                self.sendMessage("".join(self.core.greeting))
                self.recv = self.recvMessage
        else:
            self.sendMessage("Hi, you're not supposed to be here, are you? :) Curren" +
                      "tly logins are only supported by the official client")
            self.recv = self.recvIgnore
    
    def recvMessage(self, message):
        '''
        This s the standard message receiver.
        It passes all msg packets forward to the handler
        '''
        
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
                if response[0] == '(':
                    self.sendOfftopic(response[1:])
                else:
                    self.sendMessage(response)
            self.typing = 0
            if self.world:
                self.world.updatePlayer(self)

        elif tok[0] == 'pnt':
            self.typing = 0
            if self.world:
                self.world.updatePlayer(self)

        elif tok[0] == 'pit':
            self.typing = 1
            if self.world:
                self.world.updatePlayer(self)
        

        
    def getName(self): # Obsolete?
        if self.character:
            return "<%s>%s<reset>"%(self.character.color,self.account.name)
        else:
            return self.account.name    
    
        
    def sendMessage(self, message): #TODO remove this function
        ''' This function will also do some parsing stuff! '''
        #if self.character: #TODO fix
        #    message = self.character.parse(message)
        self.connection.sendMessage(self.replaceCharacterNames(message))
    
    def sendOfftopic(self,message,timestamp=None):
        self.connection.sendOfftopic(self.replaceCharacterNames(message),timestamp)


        
    def handlerLogin(self, message):
        '''
        State 1 - asking for name
        State 2 - asking for password
        State 10 - asking for new account verification
        State 11 - asking for new account password
        State 12 - asking one more time for password
        '''
        if self.handlerstate == 1:
            self.temp['name'] = message[0]
            account = [account for account in self.core.accounts if self.temp['name'].lower() == account.name.lower()]
            if account:
                self.handlerstate = 2
                self.account = account[0]
                
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
                self.name = self.account.name
                return self.login()
            else:
                self.connection.disconnect() #TODO
                
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
            self.core.accounts.append(self.account)
            self.core.saveAccounts()
            self.name = self.account.name
            return self.login()
    
    
    def disconnect(self):
        if self.character: self.character.detach()
        if self.world:
            self.world.remPlayer(self)
            
        if self.name in self.core.players:
            del self.core.players[self.name]
            
        self.sendMessage("<fail>Disconnecting you, bye bye. (Either you quit or " +
                  "you may have logged in elsewhere).")
        self.connection.transport.loseConnection()
        
    def login(self):
        # We need to check for old player connections and disconnect them.
        if self.name in self.core.players:
            print "Disconnecting old player"
            self.core.players[self.name].connection.disconnect()
            
        
        self.handler = self.handlerWorldMenu
        return self.displayWorldMenu()
    
        #self.connection.write("clk test;yellow;/testing;Click here to test a command!")
        #self.send("Howabout $(clk2cmd:test;yellow;/testing;you click here)?")
        
        
        
    def clearMain(self):
        self.connection.write("clr main")
        
    def clearOfftopic(self):
        self.connection.write("clr offtopic")
            
        
    def displayWorldMenu(self):
        self.clearMain()
        buf = []
        buf.append("Welcome to the edge of the universe. " + 
                   "Where is your soul headed to?")
        buf.append("")
        
        iw = len(self.core.worlds)
        if iw == 0:
            buf.append("Nobody has created a world yet..")
        else:
            # This is a crazy generator. Not for the weak of mind :-D
            buf+=["{i}) {name}<default>{pw}{players}".format(
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
        choice.append("refresh")
        buf.append("To create a new world, type <white>create<reset>. To join, type the number of the world.")
        buf.append("[{0}]".format(", ".join(choice)))
        return "\n".join(buf)
            
    def handlerWorldMenu(self, tok):
        print "worldmenu",tok
        if len(tok) == 0: return
        elif len(tok[0]) == 0: 
            print "my god",tok
            return #This probably shouldn't happen? 
        if self.handlerstate == 10:
            if tok[0] == self.temp['choice'].pw:
                self.clearMain()
                self.world = self.temp['choice']
                self.temp['choice'].addPlayer(self)
                self.handler = self.handlerGame
                return
            else:
                self.handlerstate = 0
                return "<fail>Invalid password"
                
        if tok[0][0].lower() == 'c':
            if len([w for w in self.core.worlds if w.creator == self.name]) > 2:
                return "<fail>You have created maximum number of worlds."
            self.handler = self.creatorWorld
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        
        elif tok[0][0].lower() == 'r':
            return self.displayWorldMenu()
            
        else:
            try:
                x = int(tok[0])
            except ValueError:
                return "Invalid choice."
            if x < 1 or x > len(self.core.worlds):
                return "Invalid choice."
            else:
                choice = self.core.worlds[x-1]
                if choice.pw:
                    self.connection.write('pwd\r\n')
                    self.handlerstate = 10
                    self.temp['choice'] = choice
                    return "This world is password protected. You should have received a password from your game master. Type in the password now"
                    
                self.clearMain()
                self.world = choice
                choice.addPlayer(self)
                self.handler = self.handlerGame
                
                return "Joined to world {0} - {1}".format(x,choice.name)
                
               
       
    def creatorWorld(self,tok): 
        
        if self.handlerstate == 0:
            self.handlerstate = 1
            return "Name of your new game world? Keep it below 60 chars."
        elif self.handlerstate == 1:
            s = " ".join(tok)
            if len(s) > 60: 
                return "That name is too long, keep it shorter! Try again.."
            
            # Make sure name is not a duplicate
            elif [w for w in self.core.worlds if w.name.lower() == s.lower()]:
                return "That name already exists. Duplicate world names are not allowed.."
                
            elif not re.match("^[ \w-]+$",s,re.UNICODE):
                return "This name contains invalid characters. Unicode alphanumerics and hyphen are OK"
                     
            self.temp['name'] = s
            self.handlerstate = 2
            return "Set a password for joining? (yes/no)"
            
        elif self.handlerstate == 2:
            if len(tok[0]) == 0: return
            elif tok[0][0].lower() == 'y':
                self.handlerstate = 10
                self.connection.write('pwd\r\n')
                return "Type password for joining the world"
            elif tok[0][0].lower() == 'n': 
                newworld = world.World(self.temp['name'],None,[self.name])
                self.core.worlds.append(newworld)
                self.handler = self.handlerWorldMenu
                return self.handler(['refresh'])
                
        elif self.handlerstate == 10:
            self.handlerstate = 11
            self.temp['password'] = tok[0]
            self.connection.write('pwd\r\n')
            return "Please retype"
            
        elif self.handlerstate == 11:
            if self.temp['password'] == tok[0]:
                newworld = world.World(self.temp['name'],self.temp['password'],[self.name])
                self.core.worlds.append(newworld)
                # TODO save
                self.handler = self.handlerWorldMenu
                return self.handler(['refresh'])
                
            else:
                self.handlerstate = 2
                return "Mismatch. Set a password for joining? (yes/no)"
            
            
    ''' New dev version gameHandler '''
    def handlerGame(self, tok):
        print "Handlering"
        print "style is",self.account.style
        if len(tok) > 0:
            if self.account.style == 'irc' and tok[0][0] != '/': #IRC STYLE
                return self.handle_say(tok)
            elif self.account.style == 'irc':
                command = tok[0][1:]
            elif self.account.style == 'mud':
                command = tok[0]
            if self.account.style == 'mud' and command[0] == '/': #Combatibility for /memorize command
                command = command[1:] #TODO this could be part of elif
                
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


    def replaceCharacterNames(self,message):
        ''' This functions solves name-memory '''
        nameregex = "\$\(name\=.+?\)"
        print "Parsing.."
        for match in re.finditer(nameregex,message):
            name = self.getCharacterName(match)
            print "Replacing..",match.group(),name
            message = message.replace(match.group(),name,1)
        
        return message
    
    # Todo update these things to work with unique id's
    def getCharacterName(self,match): #unique should always be int..
        unique = int(match.group()[7:-1])
        character = [character for character in self.world.characters if character.unique == unique]
        if not character:
            return "AMAZINGBUG"
        print "Checking my memory.."
        
        if not self.character:
            return character[0].name #TODO return actually character short description, just a quick hack
        return character[0].name
           
        #else: #TODO needs fixing srsly
        #    print self.character.memory
        #    for key in self.character.memory.keys():
        #        print "Remembering",key,type(key)
        #    
        #    character = self.world.find(name,self.world.characters)
        #   
        #    if not character: 
        #        print "character not found"
        #        return name
        #    else:
        #        character = character[0] #TODO temp fix
        #    if character in self.memory.keys():
        #        return self.memory[character]
        #    elif character == self:
        #        return character.name
        #    else:
        #        return character.info
        
    # Changing it so that a character is owned by whoever last was attached to it.   
    def creatorCharacter(self,tok):
        ''' This is a handler for character generation '''
        msg = " ".join(tok)
        if msg.lower() == 'abort':
            self.handler = self.handlerGame
            return "Aborted"
            
        elif self.handlerstate  == 0:
            self.handlerstate = 1
            return "Character name [or 'abort']:"

            
        elif self.handlerstate == 1:
            matched = [character for character in self.world.characters if character.name == msg]
            if matched:
                self.sendMessage("<fail>Warning, a character with that name already exists!")
            elif len(msg) < 2:
                return("That's a too short name..! Try again:")
            self.temp['name'] = msg
            self.handlerstate = 2
            return "Short description [max 5 words OR blank to set same as name]:"
           
        elif self.handlerstate == 2:
            if len(tok) > 6:
                return "Too long, keep it brief.."
            if len(tok) == 0:
                self.temp['info'] = self.temp['name']
            else:
                self.temp['info'] = msg
            
            self.handlerstate = 3
            return "Long description?"
        
        elif self.handlerstate == 3:
            self.temp['description'] = msg
            newchar = world.Character(self.world,self.name,
                                      self.temp['name'],self.temp['info'],
                                      self.temp['description'],
                                      self.character.location)
            #newchar.move(self.character.location)
            self.handler = self.handlerGame
            return "Character created succesfully!"
    
    def creatorLocation(self,tok):
        print "Locreator",tok
        print type(tok)
        msg = " ".join(tok)
        if msg.lower() == 'abort':
            self.handler = self.handlerGame
            return "Aborted"
        
        if self.handlerstate == 0:
            self.handlerstate = 1
            return "(Location title:"
        elif self.handlerstate == 1 and len(msg) > 2:
            self.temp['name']= msg
            self.handlerstate = 2
            return "(Location description:"
            
        elif self.handlerstate == 2:
            self.temp['description'] = msg
            self.handlerstate = 3
            return "(Exit name (enter for no exit):"
        
        elif self.handlerstate == 3:
            if len(msg):
                self.temp['exit'] = msg
            else:
                self.temp['exit'] = False
            self.handlerstate = 4
            return "(Return exit name (enter for no return exit):"
            
            

        elif self.handlerstate == 4:
            if len(msg): 
                rexit = msg
            else:
                rexit = False
                 
            newlocation = world.Location(self.world,self.temp['name'],self.temp['description'])
            if self.temp['exit']:
                self.character.location.link(self.temp['exit'],newlocation)
            if rexit:
                newlocation.link(rexit,self.character.location)
                
            self.handler = self.handlerGame
            return "(<ok>Location created (unique: %i)"%(newlocation.unique)
            
        else:
            return "<fail>Not enough information"
    # ######################
    # Player related handles
    # ######################
    #def handle_gm(self, tok):
    #    key = " ".join(tok)
    #    print "Testing",key
    #    if key == self.core.gmKey or self.gamemaster:
    #        self.gamemaster = not self.gamemaster
    #        self.db.save()
    #        if self.gamemaster:
    #            return "(GM status enabled"
    #        else:
    #            return "(GM status disabled"
    #    else:
    #        self.send("(Not authorized")
    '''        
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
    '''
    def handle_chars(self, tok):
        print "Listing chars"
        ownedchars = [character for character in self.world.characters if character.owner == self.name]
        
        buffer = []
        if not ownedchars: 
            buffer.append("(You own no characters!") #<- this kind of situation shouldn't even happen
        else:
            buffer = ["(You own the following characters"]
            for character in ownedchars:
                buffer.append("<{color}>{character.unique:<10} - {character.name}".format(
                    color="green" if character == self.character else "blue",
                    character=character))
        
        if self.gamemaster:
            otherchars = set(self.world.characters)-set(ownedchars)
            if len(otherchars) > 0:
                buffer.append("- - - - - - - - - - - - - - - - - - - - - - - -")
                buffer.append("In addition, following other characters exist..")  
                buffer.append("{:<10} - {:<15} - {}".format("Unique ID","Name","Owned by"))  
                for character in ownedchars: #TODO add played by?
                    buffer.append("<yellow>{character.unique:<10} - {character.name:<15} - ".format(
                        character=character))
        return "\n".join(buffer)
    '''    
    def handle_introduce(self, tok):
        if len(tok) < 1: return "Introduce as who?"
        name = " ".join(tok)
        if len(name) < 2: return "Introduce as who?"
        self.character.introduce(name)
    '''
    '''    
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
    '''    
    '''    
    def handle_color(self,tok):
        if len(tok) < 2:
            return "(Define the color"
        else:
            self.character.color = tok[1]
            return "(Color set to %s."%tok[1]
    '''      
    def handle_attach(self,tok): 
        regex1 = "(.+?) to (.+)"
        msg = " ".join(tok)
        special = re.search(regex1,msg)
        if special:
            groups = search.groups()
            playerName = groups[0].lower()
            characterName = groups[1].lower()
            #player    = self.world.find(playerName,self.world.players)
            player = [player for player in self.world.players if player.name.lower() == playerName]
        else:
            player = [self]
            characterName = msg
        
        if not player:
            return "(<fail>Unable to find a player named '{0}'.".format(playerName)
        else:
            player = player[0]
            
        #TODO handle characters with the same name
        #TODO wildcards?
        
        character = [character for character in self.world.characters if character.name.lower() == characterName.lower()]
        if not character:
            return "(<fail>Unable to find a character named '{0}'.".format(characterName)
        elif len(character) > 1:
            return ("<fail>Found multiple characters with the same name..")
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
            
            
    def handle_style(self,tok): #FIXME
        self.account.style = "irc" if self.account.style == 'mud' else 'mud'
        self.core.saveAccounts()
        if self.account.style == 'mud': return "You are now using MUD-style"
        else: return "You are now using IRC-style"
        
    def handle_detach(self,tok): #FIXME
        if self.character:
            if isinstance(self.character,world.Soul):
                return "(<fail>You cannot detach from your soul!"
            else:
                #location = self.character.location
                self.character.detach()
                #world.Soul(self.world,self,location) # Soul attaches automatically!
                return "Done"
                
 
    def handle_locs(self, tok):
        print "Listing locations"
        buf = ["(<green>{:<10} - {}".format("Unique ID", "Location name")]
        for loc in self.world.locations:
            buf.append("<green>{:<10} - <spring green>{}".format(loc.unique,loc.name))
        return '\n'.join(buf)
    
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
            buffer.append("Looking at %s.."%char.rename())
            buffer.append("%s"%char.description)
            return "\n".join(buffer)
            
        else:
            location = self.character.location
            buffer.append("<purple>%s<reset>"%location.name)
            buffer.append("<light sky blue>%s<reset>"%location.description)
            
            characters = [character.rename() for character in location.characters if not 
                          isinstance(character,world.Soul) and character != self.character]
            print "Chars",len(characters),characters
            if len(characters) == 0:
                buffer.append("<turquoise>You are alone<reset>")
            elif len(characters) == 1:
                buffer.append("<turquoise>%s is here.<reset>"%characters[0])
            else:
                buffer.append("<turquoise>%s and %s are here.<reset>"%(", ".join([character for character in characters[:-1]]),characters[-1]))
            
            if len(location.links) == 0:
                buffer.append("<ok>There is no obvious way out from here..</cyan>")
            elif len(location.links) == 1:
                buffer.append("<ok>This is a dead end, only one way out: %s"%location.links[0].name)
            else:
                buffer.append("<ok>Exits: %s"%", ".join([link.name for link in location.links]))
        
        return "\n".join(buffer)
          
    def handle_spawn(self, tok):
        ''' This command is used to spawn new characters '''
        if self.gamemaster or not self.world.limitSpawn:
            self.handler = self.creatorCharacter
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return "(Not authorized"
            
    def handle_create(self, tok):
        if self.gamemaster:
            self.handler = self.creatorLocation
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return "(Not authorized"
    
    def handle_kill(self,tok):
        ''' Kills a character '''
        
        if not self.gamemaster:
            return "(Not authorized"
        if len(tok) != 1:
            return "(Usage: kill [name/unique]"
        
        character = self.world.find(" ".join(tok),self.world.characters)
        if not character:
            return "(Character not found"
        
        if isinstance(character,world.Soul):
            return "(Can't kill souls!"
        else:
            self.world.remCharacter(character)
            return "(Character's history!"
                
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
        if len(tok) > 0 and not isinstance(self.character,world.Soul):
            message = " ".join(tok)
            self.character.location.sendMessage('''%s %s'''%(self.character.rename(), message))
            
    def handle_me(self,tok):
        self.handle_action(tok)
        
    def handle_describe(self,tok):
        if len(tok) > 0:
            if not isinstance(self.character,world.Soul) or self.gamemaster:
                message = " ".join(tok)
                self.character.location.sendMessage("""%s (%s)"""%(message, self.account.name))
        
    
        
    def handle_offtopic(self, tok):
        if len(tok) == 0: return
        if tok[-1][-1] == ')': 
            tok[-1] = tok[-1][:-1]
        if tok[0][0] == '(':
            tok[0] = tok[0][1:]
        message = "{name}: {message}".format(name=self.name, message=" ".join(tok))
        self.world.sendOfftopic(message) #TODO we want seperate function for sending offtopic?
        
    def handle_say(self, tok):
        if not self.character.mute and not isinstance(self.character,world.Soul):
            #if self.account.style == 'mud':
            #    message = " ".join(tok[1:])
            #else:
            #    message = " ".join(tok)
            message = " ".join(tok)
            if len(message) == 0: return "<fail>Say what?"
            
            print "Attempting to say",message
            print tok
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
                # had color #8888ff #TODO rename()
            self.character.location.sendMessage('{name} {says}, "<talk>{text}<reset>"'.format(
                                                       name=self.character.name,
                                                       says=says,
                                                       text=message))
        else:
            #self.offtopic("You are mute! You can't talk")
            self.handle_offtopic(tok)
    
    '''    
    def handle_shout(self, tok):
        pass
    '''
    """   
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
        
    """
    '''
    def handle_tp(self,tok):
        return self.handle_teleport(tok)
    '''
    
    def handle_world(self,tok): #FIXME
        if not self.gamemaster: return "(<fail>This command requires GM rights."
        if len(tok) < 1: return "(<fail>Usage: world rename/save/load"
        if tok[0] == 'name' and len(tok) > 1: 
            name = " ".join(tok[1:])
            if 3 > len(name) or len(name) > 60:
                return "(<fail>World name should be no more than 60 characters"
            elif [world for world in self.core.worlds if world.name.lower() == name.lower()]:
                return "(<fail>That name already exists. Duplicate world names are not allowed.."
                
            self.world.name = name
            
            return "(<ok>World name set to %s."%(self.world.name)
        elif tok[0] == 'save':
            self.world.saveWorld()
            return "(<ok>World saved."
            
        elif tok[0] == 'load':
            return "(<fail>Loading is disabled!"
            
        elif tok[0] == 'limitspawn':
            self.world.limitSpawn = not self.world.limitSpawn
            if self.world.limitSpawn:
                return "(<ok>Spawns are now limited to GM only."
            else:
                return "(<ok>Spawns are now unlimited."
                
            #if self.world.load(self.core," ".join(tok[1:])):
            #    return "(<ok>Load (%s) succesful."%self.world.name
            #else:
            #    return "(<fail>Load failed."
                
            
    def handle_loc(self,tok):
        if not self.gamemaster: 
            return "(<fail>This command requires GM rights."
        
        elif len(tok) == 0:
            return "(<fail>Usage: loc name/describe [text]"
        
        elif tok[0] == 'name':
            name = " ".join(tok[1:])
            if 3 > len(name) or len(name) > 60:
                return "(<fail>Please limit your location name to 60 characters (min 3)"
            self.character.location.name = name
            return "(<ok>Location renamed!"
        
        elif tok[0][0] == 'd':
            desc = " ".join(tok[1:])
            if 3 > len(desc) or len(desc) > 5000:
                return "(<fail>Please limit your title to 5000 characters (min 3)"
            self.character.location.description = desc
            return "(<ok>Location renamed!"
            
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
            self.handler = self.creatorLink
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return "(Not authorized"
    def creatorLink(self,tok):
        #self.handlerstate += 1
        print "linkcreator",tok
        print type(tok)
        msg = " ".join(tok)
        if msg.lower() == 'abort':
            self.handler = self.handlerGame
            return "Aborted"
        #if len(msg) < 1: return "Answer the damn question" 
        
        if self.handlerstate == 0:
            self.handlerstate = 1
            return "Name of the link?"
        elif self.handlerstate == 1:
        
            self.temp['name']= msg       
            self.handlerstate = 2
            return "Target location (unique ID)?"
            
        elif self.handlerstate == 2:
            try:
                target = int(msg)
            except ValueError:
                return "<fail>Unique ID required (or abort)"
                
            location = [location for location in self.world.locations if location.unique == target]
            #self.world.findAny(self.temp['location'],self.world.locations)
            if not location:
                return "(<fail>Location not found, try again or abort"
           
            self.temp['target'] = location[0]
            self.handlerstate = 3
            return "Return link (Enter=No linking)"
            

        elif self.handlerstate == 3:
            if len(msg) == 0: 
                backlink = False
            else:
                backlink = msg
                
            self.handler = self.handlerGame
           
            
            self.character.location.link(self.temp['name'],self.temp['target'])
            if backlink:
                self.temp['target'].link(backlink,self.character.location)
                
            return "(<ok>Done"
