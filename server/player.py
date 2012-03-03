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

import server,re, world, time, random, string, cgi
from collections import OrderedDict 

from cgi import escape 
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
                buf = ["<fail>ATTENTION - As of February 2011, the ropeclient ",
                       "Tk client is no longer supported. To use this server, ",
                       "Please login at <cyan>http://eiden.fi/ropeclient.html<fail> ",
                       "Thanks!"]
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
        content = message.replace('$(','')
        tok = content.split(" ")
        if tok[0] == 'msg' or tok[0] == 'cmd':
            response = self.handler(tok[0]," ".join(tok[1:]))

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
        
        elif tok[0] == 'edi':
            print "editok",tok
            self.handler(tok[0]," ".join(message.split(' ')[1:]))
                

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
            return u"<%s>%s<reset>"%(self.character.color,self.account.name)
        else:
            return self.account.name    
    
    def createHighlights(self,content):
        #print "****CREATING HILIGHTS*****"
        if not self.account:
            return content
            
        for regex,color in self.account.hilights.items():
            content = regex.sub(lambda match: "<{}>{}<reset>".format(color,match.group()),content)
        return content
        
    def createTalk(self,content):
        return re.sub('".+?"',lambda match: '"{talk}{text}<reset>"'.format(
                                                        talk=self.character.talk,
                                                        text=match.group()[1:-1]),
                                                        content)
                                                        
        
    def sendMessage(self, message): #TODO remove this function
        ''' This function will also do some parsing stuff! '''
        #if self.character: #TODO fix
        #    message = self.character.parse(message)
        
        #NOTE major problem with multi-part messages..8
        if isinstance(message,list):
            buf = []
            for part in message:
                timestamp = part[0]
                owner = part[1]
                content = self.replaceCharacterNames(part[2])
                content = self.createHighlights(content)
                if content[0] != '<': content = '<default>' + content
                if self.account and owner == self.account.name and "$(dice=" not in content:
                    owner = 1
                else:
                    owner = 0
                    
                buf.append((timestamp,owner,content))
            message = buf
            
        
        elif isinstance(message,tuple):
            timestamp = message[0]
            owner = message[1]
            content = self.replaceCharacterNames(message[2])
            content = self.createHighlights(content)
            if content[0] != '<': content = '<default>' + content
            if owner == self.account.name:
                owner = 1
            else:
                owner = 0
            message = (timestamp,owner,content)
            
        elif isinstance(message,str): # Send just text, ignore ownwer.
            message = unicode(message)
            message = self.replaceCharacterNames(message)
            message = self.createHighlights(message)
            if message[0] != '<': message = '<default>' + message
            
        elif isinstance(message,unicode):
            message = self.replaceCharacterNames(message)
            message = self.createHighlights(message)
            if message[0] != '<': message = '<default>' + message

        else:
            print "********* Fatal error in sendMessage at player********"
            return False    
        self.connection.sendMessage(message)
    
    def sendOfftopic(self,message):
        ''' message can be either a tuple (content,timestamp) or a list '''
        
        if isinstance(message,list):
            print "Sending %i offtopic lines (list)"%len(message)
            parsedMessages = []
            for content,timestamp in message:
                content = self.replaceCharacterNames(content)
                content = self.createHighlights(content)
                parsedMessages.append((content,timestamp))
            message = parsedMessages
            
        
        elif isinstance(message,tuple):
            print "Sending offtopic (tuple): ",message
            content = self.replaceCharacterNames(message[0])
            content = self.createHighlights(content)
            timestamp = message[1]
            message = (content,timestamp)
            
        
        elif isinstance(message,str):
            print "!! Sending offtopic (string) !!",message
            content = unicode(message)
            content = self.replaceCharacterNames(content)
            content = self.createHighlights(content)
            timestamp = 0
            message = (content,timestamp)
            
        elif isinstance(message,unicode):
            timestamp = 0
            content = self.replaceCharacterNames(message)
            content = self.createHighlights(content)
            message = (content,timestamp)
            
        self.connection.sendOfftopic(message)
        
        
    def handlerLogin(self,header, message):
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
                print u"New accont with",self.temp['name'],self.temp['password']
            
                self.account = server.Account(self.temp['name'],self.temp['password'])
                self.core.accounts.append(self.account)
                self.core.saveAccounts()
                self.name = self.account.name
                return self.login()
                
            else:
                self.handlerstate = 11
                self.connection.write('pwd\r\n')
                return u"Password mismatch, try again! Your password?"
        '''        
        elif self.handlerstate == 13:
            if message[0].lower() == 'irc':
                self.temp['style'] = 'irc'
            elif message[0].lower() == 'mud':
                self.temp['style'] = 'mud'
            else:
                return u"Please choose <white>irc<reset> or <white>mud<reset>!"
            
            print u"New accont with",self.temp['name'],self.temp['password']
            
            self.account = server.Account(self.temp['name'],self.temp['password'],self.temp['style'])
            self.core.accounts.append(self.account)
            self.core.saveAccounts()
            self.name = self.account.name
            return self.login()
        '''
    
    def disconnect(self):
        if self in self.core.players:
            self.core.players.remove(self)
        if self.character: self.character.detach()
        if self.world:
            self.world.remPlayer(self)
            
        if self.name in self.core.players:
            del self.core.players[self.name]
            
        self.sendMessage(u"<fail>Disconnecting you, bye bye. (Either you quit or " +
                  "you may have logged in elsewhere).")
        self.connection.transport.loseConnection()
        
    def login(self):
        # We need to check for old player connections and disconnect them.
        #if self.name in self.core.players:
        #    print "Disconnecting old player"
        #    self.core.players[self.name].connection.disconnect()
        # TODO: UPDATE
        
        #player = self.core.find(self.name,self.core.players)
        #Moved to world login..
            
        self.core.players.append(self)
        print "CHECKING COLORS",self.account.colors
        if 'background' in self.account.colors:
            print "Sending custom background color"
            self.connection.sendColor("background",self.account.colors['background'])
        if 'timestamp' in self.account.colors:
            print "Sending custom timestamp color"
            self.connection.sendColor("timestamp",self.account.colors['timestamp'])
        if 'input' in self.account.colors:
            self.connection.sendColor("input",self.account.colors['input'])
        
        self.connection.sendFont(self.account.font[0],self.account.font[1])
        
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
        buf.append(u"Welcome to the edge of the universe. " + 
                   u"Where is your soul headed to?")
        buf.append(u"")
        
        iw = len(self.core.worlds)
        if iw == 0:
            buf.append(u"Nobody has created a world yet..")
        else:
            # This is a crazy generator. Not for the weak of mind :-D
            buf+=[u"{i}) {name}<default>{pw}{players}".format(
             i=self.core.worlds.index(world)+1,
             name=world.name,
             pw=u" [password]" if world.pw else "",
             players= u" ({0} players online)".format(len(world.players)) 
             if len(world.players) > 1 else 
             u" (1 player online)" 
             if len(world.players) else 
             u" (No players online)") for world in self.core.worlds]
             
            #for i,world in enumerate(worlds):
            #    buf.append("{0}) {1}".format(i,world))
        buf.append(u'')
        choice = []
        for i in range(len(self.core.worlds)): choice.append(str(i+1))
        choice.append(u"create")
        choice.append(u"refresh")
        buf.append(u"To create a new world, type <white>create<reset>. To join, type the number of the world.")
        buf.append(u"[{0}]".format(", ".join(choice)))
        return u"\n".join(buf)
            
    def handlerWorldMenu(self, header,message):
        if header == 'cmd': return 
        tok = message.split()
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
                return u"<fail>Invalid password"
                
        if tok[0][0].lower() == 'c':
            if len([w for w in self.core.worlds if w.creator == self.name]) > 2:
                return u"<fail>You have created maximum number of worlds."
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
                return u"Invalid choice."
            if x < 1 or x > len(self.core.worlds):
                return u"Invalid choice."
            else:
                choice = self.core.worlds[x-1]
                if choice.pw:
                    self.connection.write('pwd\r\n')
                    self.handlerstate = 10
                    self.temp['choice'] = choice
                    return u"This world is password protected. You should have received a password from your game master. Type in the password now"
                    
                self.clearMain()
                self.world = choice
                player = self.core.find(self,self.name,self)
                if player:
                    player[0].connection.disconnect()
                choice.addPlayer(self)
                self.handler = self.handlerGame
                
                return u"Joined to world {0} - {1}".format(x,choice.name)
                
               
       
    def creatorWorld(self,header,*args): 
        tok = args
        print "Tok:",tok
        if self.handlerstate == 0:
            self.handlerstate = 1
            return u"Name of your new game world? Keep it below 60 chars."
        elif self.handlerstate == 1:
            s = " ".join(tok)
            if len(s) > 60: 
                return u"That name is too long, keep it shorter! Try again.."
            elif len(s) < 3:
                return u"That name is too short, make it longer. Try again.."
                
            # Make sure name is not a duplicate
            elif [w for w in self.core.worlds if w.name.lower() == s.lower()]:
                return u"That name already exists. Duplicate world names are not allowed.."
                
            elif not re.match("^[ \w-]+$",s,re.UNICODE):
                return u"This name contains invalid characters. Unicode alphanumerics and hyphen are OK"
                     
            self.temp['name'] = s
            self.handlerstate = 2
            return u"Set a password for joining? (yes/no)"
            
        elif self.handlerstate == 2:
            if len(tok[0]) == 0: return
            elif tok[0][0].lower() == 'y':
                self.handlerstate = 10
                self.connection.write('pwd\r\n')
                return u"Type password for joining the world"
            elif tok[0][0].lower() == 'n': 
                newworld = world.World(self.temp['name'],None,[self.name])
                self.core.worlds.append(newworld)
                self.handler = self.handlerWorldMenu
                return self.handler("msg",['refresh'])
                
        elif self.handlerstate == 10:
            self.handlerstate = 11
            self.temp['password'] = tok[0]
            self.connection.write('pwd\r\n')
            return u"Please retype"
            
        elif self.handlerstate == 11:
            if self.temp['password'] == tok[0]:
                newworld = world.World(self.temp['name'],self.temp['password'],[self.name])
                self.core.worlds.append(newworld)
                # TODO save
                self.handler = self.handlerWorldMenu
                return self.handler(['refresh'])
                
            else:
                self.handlerstate = 2
                return u"Mismatch. Set a password for joining? (yes/no)"
            
            
    ''' New dev version gameHandler '''
    def handlerGame(self, header,content):
        
        if header == 'msg':
            if len(content) == 0: 
                return
            
                
            if content[0] == '(':
                return self.handle_offtopic(content)
                
            elif content[0] == '#':
                return self.handle_describe(content)
            elif content[0] == '!':
                return self.handle_offtopic(content)
            elif content[0] == '%':
                return self.handle_action(content)
            else:
                return self.handle_say(content)
                
        elif header == 'cmd':
            # Fix the tokens
            args = content.split('\x1b')
            command = "handle_%s"%args[0]
            
            try:
                handle = getattr(self,command)
            except AttributeError:
                handle = False
            except UnicodeEncodeError: 
                # This happens if the player tries a command that contains scandics..
                handle = False
            if handle:
                return handle(*args[1:]) # I assume we can drop the original trigger..
        
        
        elif header == 'edi':
            print "HANDLING EDI:",content
            args = content.split()
            timestamp = float(args[0])
            content = " ".join(args[1:])
            print "p-content",content
            # Note, this should be connection specific decolor convert
            # But since webclient is the only client supported atm, doing it the simple way
            #content = content.replace('</font>','<reset>')
            #content = content.replace('<font color="','<')
            #content = content.replace('">','>')
            
            # TODO check the owner of the message!
            
            if timestamp not in self.character.world.messages:
                print "******* TIMESTAMP",timestamp,"NOT FOUND IN WORLD MESSAGES"
                return 
            
            # TODO find matching $(name strings and replace.
            message = self.character.world.messages[timestamp]
            print "Updating",message
            if message[0] != self.account.name:
                print "!*!*!*!* INVALID OWNER",message[0],self.account.name 
                return 
            
            # Replace the name holders
            snames = re.findall("\$\(name=.+?\)", message[1])
            for name in snames:
                print "content:",content
                print "Replacing name..",name
                content = content.replace("$(name)",name,1)
                
            
            if not len(content):
                return "(<fail>Deleting not supported yet."
            message = (message[0],content)
            print "To",message
            self.character.world.messages[timestamp] = message 
            self.character.world.sendEdit(timestamp,content)
            
        else:
            print "UNKNOWN HEADER"

    def replaceCharacterNames(self,message):
        ''' This functions solves name-memory '''
        nameregex = "\$\(name\=.+?\)"
        #print "Parsing.."
        for match in re.finditer(nameregex,message):
            name = self.getCharacterName(match)
            #print "Replacing..",match.group(),name
            message = message.replace(match.group(),"$(disp=%s)"%name,1)
        
        return message
    
    # Todo update these things to work with unique id's
    def getCharacterName(self,match): #unique should always be int..
        unique = int(match.group()[7:-1])
        character = [character for character in self.world.characters if character.unique == unique]
        if not character:
            return u"Joining.."
        #print "Checking my memory.."
        
        if not self.character:
            return character[0].name #TODO return actually character short description, just a quick hack
        return character[0].name
           

    def handle_players(self,*args):
        print "players",len(self.world.players)
        players = [player for player in self.core.players if player.world]
        players.sort(key=lambda player: player.world)
        buffer = ['Players online',20*'-']
        for player in players:
            buffer.append("{player.name:<10} - {player.world.name}".format(player=player))
            
        return u"\n".join(buffer)
        
    def handle_chars(self, *args):
        print "Listing chars"
        ownedchars = [character for character in self.world.characters if character.owner == self.name]
        
        buffer = []
        if not ownedchars: 
            buffer.append(u"(You own no characters!") #<- this kind of situation shouldn't even happen
        else:
            buffer = [u"(You own the following characters"]
            for character in ownedchars:
                buffer.append(u"<{color}>{index:<10} - {character.name}".format(
                    color="green" if character == self.character else "blue",
                    character=character,index=self.world.characters.index(character)))
        
        if self.gamemaster:
            otherchars = set(self.world.characters)-set(ownedchars)
            if len(otherchars) > 0:
                buffer.append(u"- - - - - - - - - - - - - - - - - - - - - - - -")
                buffer.append(u"In addition, following other characters exist..")  
                buffer.append(u"{:<10} - {:<15} - {}".format("Unique ID","Name","Owned by"))  
                for character in otherchars: #TODO add played by?
                    buffer.append(u"<yellow>{index:<10} - {character.name:<15} - {character.owner} ".format(
                        index=self.world.characters.index(character),character=character))
        return u"\n".join(buffer)
    '''    
    def handle_introduce(self, tok):
        if len(tok) < 1: return u"Introduce as who?"
        name = " ".join(tok)
        if len(name) < 2: return u"Introduce as who?"
        self.character.introduce(name)
    '''
    '''    
    def handle_memorize(self, tok): #TODO FIX
        if len(tok) < 2: 
            return u"(<fail>Usage: memorize StaticID name"
        
        ident = tok[0]
        
        if ident not in self.world.idents.keys():
            return u"(<fail>StaticID not found."
        
        character = self.world.idents[ident]
        if not isinstance(character,world.Character):
            return u"(<fail>StaticID refered to a non-character"
            
        name   = " ".join(tok[1:])
        self.character.memory[character] = name
        return u"(<ok>Memorized %s"%name
    '''    
    '''    
    def handle_color(self,tok):
        if len(tok) < 2:
            return u"(Define the color"
        else:
            self.character.color = tok[1]
            return u"(Color set to %s."%tok[1]
    '''      
    def handle_attach(self,*args): 
        if len(args) == 0:
            return "(<fail>This command needs arguments"
        elif len(args) == 1:
            targetName = re.compile(args[0],re.IGNORECASE)
            player = [self]
            character = [character for character in self.world.characters if re.match(targetName,character.name)]
        elif len(args) > 1:
            playerName = re.compile(args[0],re.IGNORECASE)
            targetName = re.compile(args[1],re.IGNORECASE)
            player = [player for player in self.world.players if re.match(playerName,player.name)]
            character = [character for character in self.world.characters if re.match(targetName,character.name)]
        
        if not player:
            return u"(<fail>Unable to find a player named '{0}'.".format(args[0])
        else:
            player = player[0]
            
        if not character:
            return u"(<fail>Unable to find a character '{0}'.".format(targetName.pattern)
        elif len(character) > 1:
            return ("<fail>Found multiple characters with the same name.. try using unique number.")
        else:
            character = character[0]
            
        if character.owner != player.account.name and not self.gamemaster:
            return u"(<fail>You may not attach to this character"
        
        if character.player:
            return u"(<fail>Somebody is currently playing with this character. Detach them first?"
        
        player.character.detach()
        character.attach(player)
        
        if player is not self:
            return u"(<ok>Attach succesful!"
        return
        
   

    def handle_detach(self,*args): #FIXME
        if self.character:
            if isinstance(self.character,world.Soul):
                return u"(<fail>You cannot detach from your soul!"
            else:
                location = self.character.location
                self.character.detach()
                world.Soul(self.world,self,location) # Soul attaches automatically!
                return u"(<ok>Detached!"
                
 
    def handle_locs(self, *args):
        print "Listing locations"
        buf = ["(<green>{:<10} - {}".format("Unique ID", "Location name")]
        for loc in self.world.locations:
            buf.append("<green>{:<10} - <spring green>{}".format(self.world.locations.index(loc),loc.name))
        return '\n'.join(buf)
    
    # #####################
    # World related handles
    # #####################
    def handle_look(self, *args):
        buffer = []
        if len(args) == 0:
            print "GENERAL LOOK"
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
            return u"\n".join(buffer)
        else:
            print "LOOK AT"
            charname = match.group()
            char = self.world.findAny(charname,self.character.location.characters)
            if not char or not isinstance(char,world.Character): return u"(<fail>There is no one with that id here (%s).."%charname
            buffer.append("Looking at %s.."%char.rename())
            buffer.append("%s"%char.description)
            return u"\n".join(buffer)

          
    def handle_spawn(self, *args):
        #0 Character name
        #1 Short description
        #2 Long description
        
        if self.gamemaster or not self.world.limitSpawn:
            if len(args) >= 3:
                name = args[0]
                shortd = args[1]
                longd = args[2]
                if len(name) > 40:
                    return u"(<fail>The character name is way too long!"
                if len(shortd) == 0:
                    shortd = name
                if len(shortd) > 40:
                    return u"(<fail>The short description is way too long! Max 40 letters."
                newchar = world.Character(self.world,self.name,
                                              name,shortd,
                                              longd,
                                              self.character.location)
                return u"Character created succesfully!"
                
        else:
            return u"(Not authorized"
            
            

            
    def handle_create(self, *args):
        # 0 Title
        # 1 Description
        # 2 Exit name
        # 3 Return exit name
        
        if self.gamemaster and len(args) >= 2:
            title = args[0]
            description = args[1]
            if len(title) == 0:
                return u"(<fail>Title cannot be left empty."
            if len(args) >= 3 and len(args[2]) > 0:
                exit = args[2]
            else:
                exit = False
            if len(args) >= 4 and len(args[3]) > 0:
                rexit = args[3]
            else:
                rexit = False
                
            newlocation = world.Location(self.world,title,description)
            if exit:
                self.character.location.link(exit,newlocation)
            if rexit:
                newlocation.link(rexit,self.character.location)
            return u"(<ok>Location created (unique: %i)"%(self.world.locations.index(newlocation))
        else:
            return u"(Not authorized"
    
    
    
    
    def handle_kill(self,*args):
        ''' Kills a character '''
        
        if not self.gamemaster:
            return u"(Not authorized"
        if len(args) < 1:
            return u"(Usage: kill [name/unique]"
        if len(args[0]) == 0: 
            return u"(Requires a name or id.."
        character = self.core.find(self,args[0],self.character)
        if not character:
            return u"(<fail>Character not found"
        elif len(character) > 1:
            return u"(<fail>Multiple characters found under that name!"
        else:
            character = character[0]
        if isinstance(character,world.Soul):
            return u"(Can't kill souls!"
        else:
            self.world.remCharacter(character)
            return u"(Character is history!"
            
    def handle_destroy(self,tok):    
        ''' Destroys a location '''
        
        if not self.gamemaster:
            return u"(Not authorized"
        if len(tok) != 1:
            return u"(Usage: destroy [unique]"
        unique = tok[0]
        try:
            unique = int(tok[0])
        except ValueError:
            return u"(Error: unique id required"
        location = [location for location in self.world.locations if location.unique == unique]
        if not location:
            return u"(Error: unique id not found"
        
        return u"(Location %s should be destroyed, but function not implemented yet"%location[0].name
        
            
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
        else:
            return False
            
    def handle_action(self,*args):
        if len(args) > 0 and not isinstance(self.character,world.Soul):
            message = args[0]
            if message[0] == '%':
                message = message[1:].strip()
            if len(message) == 0: 
                return 
                
            message = self.createTalk(message) 
            message = self.diceSub(message)
            self.character.location.sendMessage((self.account.name,u"%s %s"%(self.character.rename(), message)))
            
    def handle_me(self,*args):
        self.handle_action(*args)
        
    def handle_describe(self,*args):
        if len(args) >= 1:
            message = args[0]
            if not isinstance(self.character,world.Soul) or self.gamemaster:
                if message[0] == '#':
                    message = message[1:]
                    
                message = self.createTalk(message) 
                message = self.diceSub(message)
                self.character.location.sendMessage((self.account.name,u"%s (%s)"%(message, self.account.name)))
        
    def handle_getlog(self,*args):
        # 0 - email address
        # 1 - 1 main only, 2 offtopic only, 3 both
        # 2 - max age
        
        if len(args) < 3:
            return "(<fail>This command requires 3 arguments."
        email = args[0]
        mode = args[1]
        age = args[2]
        if not re.match('^.+?\@.+?\..+',email):
            return "(<fail>Bad email address"
        
        try:
            mode = int(mode)
            age = int(age)
        except:
            return "(<fail>Bad parameters, needs numbers"
        
        if not 0 < mode < 4:
            return "(<fail>Mode needs to be 1 (main chat), 2 (offtopic) or 3 (both)"
            
        maxage = time.time() - age * 60 * 60
        
        buffer = OrderedDict()
        # First we collect the appropriate messages.
        if mode == 2 or mode == 3:
            for (content,timestamp) in self.world.offtopicHistory:
                if timestamp < maxage:
                    continue
                else:
                    buffer[timestamp] = content
        if mode == 1 or mode == 3:
            for timestamp,message in self.world.messages.items():
                if timestamp < maxage:
                    continue
                else:
                    buffer[timestamp] = message[1]
                    
        print "Exporting"
        keys = buffer.keys()
        keys.sort()
        f = open('log.html','w')
        for key in keys:
            line = buffer[key]
            line = self.replaceCharacterNames(line)
            line = self.connection.colorConvert(line)
            line = re.sub("\$\(disp\=.+?\)", lambda match: match.group()[7:-1], line)
            line = line.encode('utf-8')
            f.write("%s<br>\n"%line)
        f.close()
        print "Export completed"
        print "Mailing"
        import subprocess
        subprocess.call("""cat log.html | mailx -s "Ropeclient log" %s"""%email,shell=True)
        print "Sent!"
        return "(<ok>Your log should arrive shortly. It's in HTML plaintext and encoded utf-8"
        
    
    def handle_setcolor(self,*args):
        """
        This command is used to set custom colors
        Special colors that the server should sync with the client..
        background and timestamp?
        """
        
        buffer = []
        if len(args) == 0:
            if len(self.account.colors) == 0:
                buffer.append("No color definitions set")
            else:
                buffer.append("Current color definitions")
                for c1,c2 in self.account.colors.items():
                    buffer.append("{c1} -> {c2}".format(c1=c1,c2=c2))
        elif len(args) == 1:
            c1 = args[0]
            if c1 in self.account.colors:
                del self.account.colors[c1]
                buffer.append("<ok>Removed color mapping for {0}".format(c1))
            else:
                buffer.append("<fail>Color not found")
        else:
            c1 = args[0]
            c2 = args[1]
            self.account.colors[c1] = c2
            buffer.append("<ok>Mapped: {c1} -> {c2}".format(c1=c1,c2=c2))
            
            if c1 == 'background' or c1 == 'timestamp' or c1 == 'input':
                self.connection.sendColor(c1,c2)
                
        return u"\n".join(buffer)
    
    def handle_sethilight(self,*args):
        print "Handle highlight",len(args)
        if len(args) == 0:
            if len(self.account.hilights) == 0:
                return "(You have no highlights"
            else:
                buf = ["Your current highlights",""]
                for regex,color in self.account.hilights.items():
                    buf.append("{:<3}) {:<10} -> {:<10}".format(self.account.hilights.keys().index(regex),escape(regex.pattern),color))
                return u"("+u"\r\n".join(buf)
        elif len(args) == 1:
            try: 
                r = int(args[0])
            except:
                return "(<fail>Please use an index number to define what you wish to remove."
            
            try:
                regex = self.account.hilights.keys()[r]
            except IndexError:
                return "(<fail>Index out of bounds"
            
            del self.account.hilights[regex]
            return "(<ok>Deleted."
        else:
            regex = args[0]
            color = args[1]
            self.account.hilights[re.compile(regex)] = color 
            return "(<ok>Highlight set!"
    def handle_settalk(self,*args):
        if len(args) < 1:
            return 
        color = args[0]
        allowed = set(string.ascii_lowercase + '#' + string.digits)
        if not set(color) <= allowed:
            return u"<fail>Invalid color"
            
        
        if self.character:
            self.character.talk = "<%s>"%(color)
        
    def handle_setfont(self,*args):
        if len(args) == 0: 
            return u"(<fail>Not enough args."
        font = args[0]
        if len(args) == 2:
            size = args[1]
        else:
            size = 8
        print "Setting font",font,"with size",size
        self.account.font = (font,size)
        self.connection.sendFont(font,size)
        
    def handle_offtopic(self, *args):
        message = args[0]
        if len(message) == 0: return
        #if message[-1] == ')': 
        #    message = message[:-1]
        
        if len(message) == 0: return
        if message[0] == '(':
            message = message[1:]
            
        if len(message) == 0: return
        
        message = u"{name}: {message}".format(name=self.name, message=message)
        
        message = self.diceSub(message)
        self.world.sendOfftopic(message)
        
    def handle_say(self, *args):
        message = args[0]
        
        if not self.character.mute and not isinstance(self.character,world.Soul):
            if len(message) == 0: return u"<fail>Say what?"
            
            print "Attempting to say",message
            
            
            # Some ideas are borrowed from
            # http://www.achaea.com/game/helpview/achaea/conversing
   
            pre  = ''
            says = ''
            post = ''
            
            emoteS = message[-2:].upper()
            if emoteS == ':)': 
                pre = "smiles and "
                message = message[:-2].strip()
            elif emoteS == ':]': 
                pre = "smiles broadly and "
                message = message[:-2].strip()
            elif emoteS == ':>': 
                pre = "smiles mischievously and "
                message = message[:-2].strip()
            elif emoteS == ';)': 
                pre = "smiles with a wink and "
                message = message[:-2].strip()
            elif emoteS == ':D':
                pre = "laughingly "
                message = message[:-2].strip()
            elif emoteS == ':(':
                post = " grimly"
                message = message[:-2].strip()
            elif emoteS == ':P':
                pre = "jokingly "
                message = message[:-2].strip() 
            elif emoteS == ':@':
                pre = "angrily "
                message = message[:-2].strip() 
            elif emoteS == ':S':
                pre = "looks confused and "
                message = message[:-2].strip() 
                
            if len(message) < 1:
                return u"(<fail>Nope. Don't say that."
                
            emoteS = message[-2:].upper()
            if emoteS == ':O':
                message = message[:-2].strip()
                says = "gasps"
                pre = ""
                post = ""
            elif emoteS == ':?':
                message = message[:-2].strip()
                says = "wonders"
                pre = ""
                post = ""
            elif emoteS == ':~':
                message = message[:-2].strip()
                says = "sings"
                pre = ""
                post = ""
            elif message[-2:] == '!!':
                says = "shouts"
                message = message[:-1]
                
            elif message[-1] == '!':
                says = "exclaims"
            elif message[-1] == '?':
                says = "asks"
            
            elif message[-1] == '.':
                says = 'says'
            else:
                says = 'says'
                message += '.'
            
            if message[0] not in string.uppercase:
                message = message[0].upper() + message[1:]
                
            message  = u'{name} {pre}{says}{post}, "{text}"'.format(
                                                       name=self.character.rename(),
                                                       pre=pre,
                                                       says=says,
                                                       post=post,
                                                       text=message)
            message = self.createTalk(message)   
            
            message = self.diceSub(message)                                         
            self.character.location.sendMessage((self.account.name,message))
            
        else:
            #self.offtopic("You are mute! You can't talk")
            self.handle_offtopic(message)
    
    '''    
    def handle_shout(self, tok):
        pass
    '''
    
    def handle_teleport(self,tok):
        ''' TP function, allows chars to be moved to locations '''
        ''' ex1: tp 0 --- Teleport to location with dynid 0 '''
        ''' ex2: tp xxx to yyy --- Teleport character xxx to location with name/id yyy'''
        if len(tok) == 1:
            try:
                print "got toks",tok
                unique = int(tok[0])
            except:
                return u"(<fail>Destination must be unique id"
            
            location  = [location for location in self.world.locations if location.unique == unique]
            character = [self.character]
        
        else:
            return ("<fail>Unable to parse request: tp {chr} [loc]")
        if len(location) != 1:
            return u"(<fail>Invalid destination)"
        if len(character) != 1:
            return u"(<fail>Invalid character)"
        

        character[0].move(location[0])
        if self.character != character[0]:
            if character[0].player:
                character[0].player.send("(<ok>You have been teleported")
        return u"(<ok>Teleport succesful"
        
    

    def handle_tp(self,*args):
        return self.handle_teleport(*args)
    
    def handle_world(self,*args): #FIXME
        tok = args
        if not self.gamemaster: return u"(<fail>This command requires GM rights."
        if len(tok) < 1: return u"(<fail>Usage: world rename/save/load"
        if tok[0] == 'name' and len(tok) > 1: 
            name = " ".join(tok[1:])
            if 3 > len(name) or len(name) > 60:
                return u"(<fail>World name should be no more than 60 characters"
            elif [world for world in self.core.worlds if world.name.lower() == name.lower()]:
                return u"(<fail>That name already exists. Duplicate world names are not allowed.."
                
            self.world.name = name
            
            return u"(<ok>World name set to %s."%(self.world.name)
        elif tok[0] == 'save':
            self.world.saveWorld()
            return u"(<ok>World saved."
            
        elif tok[0] == 'load':
            return u"(<fail>Loading is disabled!"
            
        elif tok[0] == 'limitspawn':
            self.world.limitSpawn = not self.world.limitSpawn
            if self.world.limitSpawn:
                return u"(<ok>Spawns are now limited to GM only."
            else:
                return u"(<ok>Spawns are now unlimited."
                
            #if self.world.load(self.core," ".join(tok[1:])):
            #    return u"(<ok>Load (%s) succesful."%self.world.name
            #else:
            #    return u"(<fail>Load failed."
                
            
    def handle_editlocation(self,*args):
        if not self.gamemaster: 
            return u"(<fail>This command requires GM rights."
        
        elif len(args) < 2:
            return u"(<fail>Usage: loc name/describe [text]"
        
        elif args[0] == 'name' and len(args)>=2:
            name = " ".join(args[1])
            if 3 > len(name) or len(name) > 60:
                return u"(<fail>Please limit your location name to 60 characters (min 3)"
            self.character.location.name = name
            return u"(<ok>Location renamed!"
        
        elif args[0] == 'd':
            desc = " ".join(args[1])
            if 3 > len(desc) or len(desc) > 5000:
                return u"(<fail>Please limit your title to 5000 characters (min 3)"
            self.character.location.description = desc
            return u"(<ok>Location renamed!"
            
    def handle_tell(self,*args):
        if len(args) >= 2:
            pattern = args[0]
            message = args[1]
            
            target = self.core.find(self,pattern,self.character)
            
            
            if not target: 
                return u"(<fail>%s is not here.."%targetName.pattern
            elif len(target) > 1:
                return u"(<fail>Multiple people found with that name.."
            else:
                target = target[0]
                
            self.world.sendMessage('''%s whispers to you, "%s"'''%(self.character.rename(), message),[target])
            return '''You whisper to %s, "%s"'''%(target.rename(),message)
        else:
            return u"(<fail>Invalid arguments: /tell charname message"
    
    def handle_notify(self,*args):
        if len(args) >= 2 and self.gamemaster:
            pattern = args[0]
            message = args[1]
            target = self.core.find(self,pattern,self)
            if not target: 
                target = self.core.find(self,pattern,self.character)
                if not target:
                    return u"(<fail>%s is not here.."%targetname
                else:
                    target = target[0]
            elif len(target) > 1:
                return u"(<fail>Multiple targets, be more specific"
            else:
                target = target[0]
                
            if isinstance(target,world.Character):
                self.world.sendMessage('''<notify>%s: %s'''%(self.account.name, message),[target])
            elif isinstance(target,Player):
                target.sendMessage('''<notify>%s: %s'''%(self.account.name, message))
                
            return '''<notify>@%s: "%s"'''%(target.name,message)        
        else:
            return u"(<fail>Invalid arguments: /tell charname message, or you're not GM"
            
    def handle_unlink(self,tok):
        if self.gamemaster:
            self.handler = self.removerLink
            self.handlerstate = 1
            self.temp = {}
            return self.handler([])
        else:
            return u"(Not authorized"
    def removerLink(self,tok):
        print "linkremover",tok
        print type(tok)
        msg = " ".join(tok)
        if msg.lower() == 'abort':
            self.handler = self.handlerGame
            return u"Aborted"
        if self.handlerstate == 1:
            self.handlerstate = 2
            return u"Name of the link to remove? (or type 'abort')"
            
        elif self.handlerstate == 2:
            self.temp['linkto']= msg
            self.handlerstate = 3
            return u"Remove return link also? (y/N)"
            
        elif self.handlerstate == 3:
            
            if len(msg) == 0:
                both = False
            elif msg[0].lower() == 'y':
                both = True
            else:
                both = False
                
            self.handler = self.gameHandler
            return self.character.location.unlink(self.temp['linkto'],both)
            
            
    def handle_link(self,tok):
        if self.gamemaster:
            self.handler = self.creatorLink
            self.handlerstate = 0
            self.temp = {}
            return self.handler([])
        else:
            return u"(Not authorized"
    
    def creatorLink(self,tok):
        #self.handlerstate += 1
        print "linkcreator",tok
        print type(tok)
        msg = " ".join(tok)
        if msg.lower() == 'abort':
            self.handler = self.handlerGame
            return u"Aborted"
        #if len(msg) < 1: return u"Answer the damn question" 
        
        if self.handlerstate == 0:
            self.handlerstate = 1
            return u"Name of the link? (or type 'abort')"
        elif self.handlerstate == 1:
        
            self.temp['name']= msg       
            self.handlerstate = 2
            return u"Target location (unique ID)?"
            
        elif self.handlerstate == 2:
            try:
                target = int(msg)
            except ValueError:
                return u"<fail>Unique ID required (or abort)"
                
            location = [location for location in self.world.locations if location.unique == target]
            #self.world.findAny(self.temp['location'],self.world.locations)
            if not location:
                return u"(<fail>Location not found, try again or abort"
           
            self.temp['target'] = location[0]
            self.handlerstate = 3
            return u"Return link (Enter=No linking)"
            

        elif self.handlerstate == 3:
            if len(msg) == 0: 
                backlink = False
            else:
                backlink = msg
                
            self.handler = self.handlerGame
           
            
            self.character.location.link(self.temp['name'],self.temp['target'])
            if backlink:
                self.temp['target'].link(backlink,self.character.location)
                
            return u"(<ok>Done"

    def handle_calldice(self,*args):
        if len(args) < 3:
            return u"(<fail>calldice requires 3 arguments: list of targets, roll expression and a query string"
        rawtargets = args[0]
        roll = args[1]
        query = args[2]
        
        targets = []
        rawtargets = rawtargets.split(',')
        for target in rawtargets:
            target = self.core.find(self,target.strip(),self.character)
            if len(target):
                targets.append(target[0])
        if not len(targets):
            return u"(<fail>calldice could not locate any targets"
            
            
        print "Targets",targets
        
        operators = re.search("[\<\>\=]+",roll)
        if operators:
            operators = operators.group()
            tok = roll.split(operators)
            dreq = tok[0].strip()
            dtar = tok[1].strip() 
            
            if not len(dreq) or not len(dtar):
                return u"(<fail>Invalid syntax"
            
            if dreq[0] == "1":
                dreq = dreq[1:]
                
            for target in targets:
                if target not in self.world.calledRolls.keys():
                    self.world.calledRolls[target] = (dreq,operators,dtar)
                    print "Target level set at",(dreq,operators,dtar)
                message = u"<offtopic>{self}: <notify>{name}, roll {dreq} ({query} - Target: {op}{tar})<reset><reset>".format(
                            self=self.name,
                            name=target.name,
                            dreq=dreq,
                            op=cgi.escape(operators),
                            tar=dtar,
                            query=query)
                self.world.sendOfftopic(message)
                
        else:            
            for target in targets:
                message = u"<offtopic>{self}: <notify>{name} roll {dreq} ({query})<reset><reset>".format(
                            self=self.name,
                            name=target.name,
                            dreq=roll,
                            query=query)
                self.world.sendOfftopic(message)
                
    def handle_cancelcall(self,*args):
        if len(args) < 1:
            return u"(<fail>Argument required"
        name = args[0].lower()
        match = [character for character in self.world.calledRolls if character.name.lower() == name]
        if len(match):
            for m in match:
                del self.world.calledRolls[m]
            return u"(<ok>%i called rolls removed."%len(match)
        return u"(<fail>No rolls found under that name."
        
    def diceSub(self,message):
        ''' This function performs a regex substitution for a string of text '''
        return re.sub(\![d0-9\+\-\*\/]+([\<\>\=]+[0-9]+),self.diceParse,message)
        
    def diceParse(self,match):
        diceregex = "[0-9]*d[0-9]+"
        equation = match.group()[1:]
        
        operators = re.search("[\<\>\=]+",equation)
        if operators:
            tok = equation.split(operators.group())
            equation = tok[0]
            operators = [operators.group(),tok[1]]
        else:
            operators = False
        
        resultequation = equation
        allrolls = []
        try:
            for dice in re.finditer(diceregex,equation):
                dice = dice.group()
                tok = dice.split('d')
                roll = self.diceRoll(tok[0],tok[1])
                resultequation = resultequation.replace(dice,str(roll[0]),1)
                allrolls.append(roll[1])
        except OverflowError:
            return "$(dice=[Overflow];N/A)"
        try: 
            total = eval(resultequation)
        except SyntaxError:
            return "$(dice=[Bad syntax];N/A)"
            
        # if self.character: #shouldn't be necessary to tes this
        if self.character in self.character.world.calledRolls.keys():
            calledroll = self.character.world.calledRolls[self.character]
            if calledroll[0] in equation:
                del self.character.world.calledRolls[self.character]
                # Just for testing, harnmaster specific behaviour..
                s1 = eval(str(total)+calledroll[1]+calledroll[2])
                op = self.core.escape(calledroll[1])
                tl = calledroll[2]
                
        elif operators:
            s1 = eval(str(total)+operators[0]+operators[1])
            op = self.core.escape(operators[0])
            tl = operators[1]
        else:
            s1 = None
            
        if s1 != None:
                if s1:
                    s1 = "success"
                else:
                    s1 = "failure"
                if not total%5:
                    s2 = "Critical"
                else:
                    s2 = "Marginal"
                return "${dice|[%s %s%s: %i - %s %s!]|%s}"%(equation,op,tl,total,s2,s1,str(allrolls))
                
        return "${dice|[%s: %i]|%s}"%(equation,total,str(allrolls))
            
            # Handle special rolls here?
                  
    def diceRoll(self,x,y):
        if x == '': x = 1
        x = int(x)
        y = int(y)
        if x > 20 or x < 1: 
            raise OverflowError
        if y > 100 or y < 1: 
            raise OverflowError
        
        total = 0
        rolls = []
        for i in xrange(x):
            r = random.randint(1,y)
            total += r
            rolls.append(r)
        return (total,rolls)
