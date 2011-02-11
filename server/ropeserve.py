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


    Also, this program features very messy code, don't hurt your head
    trying to decypher it.

    Copyright 2010-2011 Matti Eiden <snaipperi()gmail.com>
'''
''' 
NOTES


Protocol notes
\xff\xa0 Server  -> client: String of player names seperated by space
\xff\x00 Client <-> server: Client is not typing [string: player name]
\xff\x01 Client <-> server: Client is typing [string: player name]
\xff\x02 Client  -> server: Message [string:contents]
\xff\x02 Server <-  client: Message [string:owner] [float:timestamp] [string:contents]
\xff\x30 Client  -> server: Handshake [string:SUPERHANDSHAKE] [int:protocol]
\xff\x31 Client  -> server: Nickname  [string:nick]
\xff\x32 Client  -> server: Password  [string:sha256password]
\xff\x33 Client <-> server: Color     [string:colorid] [string:color]
\xff\x34 client  -> server: default-action [string:speak/offtopic/none]

Plaintext protocol?
lop = list of players
pit = player is typing
pnt = player not typing
msg = message
pwd = password
clr = color
nck = nick
hsk = handshake
dfa = default action

1 - offtopic
2 - talk
3 - emote
4 - describe

'''
# TODO: fix color highlight according to protocol
# TODO: password salt


''' thinking about modifications

world
- keeps track of messages
- maintains a message counter



- history format: text file?
- account format: pickle?
-- account should contain: password, avatars


'''






from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
import hashlib, random, re, pickle, time, os


class Game:
    def __init__(self):
        print "Intializing game"
        messages = self.pickleLoad('./messages.data')
        world    = self.pickleLoad('./world.data')
        
        if not messages: messages = Messages()
        if not world:    world = World()
    
        self.world = world
        self.messages = messages
        self.world.messages = messages
        self.world.players  = {}
        
        self.world.regexDice  = re.compile("(?:\!\d*d\d*(?:\+|\-)*)(?:(?:(?:\d*d\d*)|\d*)(?:\+|\-)*)*",re.IGNORECASE)
        self.world.regexQuote = re.compile('".*?"')
        self.world.regexOff   = re.compile('\(.*?\)')
        self.world.regexColor = re.compile('(?<=<).*?(?=>)')
        self.world.regexColorF= re.compile('<.*?>')
        self.world.regexDicex  = re.compile('[\+-]?\d*d?\d+')
        
        self.world.timestamps = []
        print "Game initialized"
    def pickleLoad(self,filename):
        try:
            f = open(filename,'rb')
            x = pickle.load(f)
            f.close()
            return x
        except: return False
    
class Messages(dict):
    def __init__(self):
        self.counter = 1
    def save(self):
        self.pickleSave(self,'messages.data')
    def pickleSave(self,object,filename):
        f = open(filename,'wb')
        pickle.dump(object,f)
        f.close()
        return True
    def addMessage(self,content):
        self.counter += 1
        self[self.counter] = content


class World:
    def __init__(self):
        self.messages = None
        self.accounts = {}
        self.locations= {}
        self.avatars  = {}
        self.players  = {}
        
        
        
        
        self.locations['spawn'] = Location('spawn','Spawn')
        print "World: init completed!"
        
    def pickleSave(self,object,filename):
        f = open(filename,'wb')
        pickle.dump(object,f)
        f.close()
        return True
 
    def saveAll(self):
        print "World:saveData: saving data"
        self.pickleSave(self,'./world.data')

    def __getstate__(self):
        d = self.__dict__.copy() 
        del d['messages']
        del d['players']
        return d
    
    def connectPlayer(self,player):
        if player.account in self.players.keys(): 
            self.players[player.account].transport.loseConnection()
        self.players[player.account] = player
        self.sendPlayers()
        self.sendAnnounce('%s has joined the game!'%(player.nick))
        if len(player.account.avatars) == 0:
            player.sendMessage("It seems that you haven't created any avatar yet. Please do so now by typing a first name or ID for your character")
            player.getname = True
        elif len(player.account.avatars) == 1:
            player.account.avatars[0].attach(player)
            
    def disconnectPlayer(self,player):
        if player.avatar:
            player.avatar.detach()
            
        if player.account in self.players.keys():
            if self.players[player.account] == player:
                self.players[player.account].transport.loseConnection()
                del self.players[player.account]
        
            
    def sendPlayers(self):
        pl = []
        for player in self.players.values(): 
            nick = player.nick
            if player.typing:   nick = "*" + nick
            if player.gm:       nick = "[%s]"%nick
            if player.avatar:   nick = "%s (%s)"%(nick,"has_avatar")
            pl.append(nick)
        ann = u"lop %s"%(" ".join(pl))
        for player in self.players.values(): player.write(ann)
        
    def sendAnnounce(self,message,save=False):
        ''' Send a public message to all players. This is generally either an offtopic or server announcement'''
        print "World:sendAnnounce: announcing",message
        if save: pass # TODO
        for player in self.players.values():
            player.sendMessage(message)
            
    

        
    def messageWrap(self,data,style='default'):
        data = re.sub(self.regexDice,self.wrapDice,data)   #Search for dice combinatinos
        data = re.sub(self.regexQuote,self.wrapQuote,data) #Search for text in between quotes
        data = re.sub(self.regexOff,self.wrapOff,data)     #Search for offtopic 
        
        for player in self.players.values():
            if player.regexHilite: 
                data=re.sub(player.regexHilite,player.wrapHilite,data)#Search for player name highlights
                
        if   style == "default":  data = "%s%s"%('<white>',data)
        elif style == "describe": data = "%s%s"%('<describe>',data)
        elif style == "action":   data = "%s%s"%('<action>',data)
        elif style == "offtopic": data = "%s%s"%('<offtopic>',data)
        else: data = "%s%s"%('<red>',data)
        
        # Colorstack is the heart of the whole thing.
        # I didn't figure any other way to do it nicely.
        # Ha ahaha.
        colorstack = []
        for color in re.finditer(self.regexColorF,data):
            x = color.group()
            reset = '<reset>'
            if x == reset:
                try: 
                    colorstack.pop()
                    data=data.replace(reset,colorstack[-1],1)
                except: data=data.replace(reset,'<red>',1);print "Wrap(): Too many resets at",data
            else: colorstack.append(x)

        return data
    
    def wrapDice(self,match):
        ''' Regex replace function for dice rolls '''
        roll = self.dicer(match.group())
        if roll: return roll
        else:    return match.group()
    def wrapQuote(self,match):
        ''' Regex replace function for quotes '''
        return "<talk>%s<reset>"%(match.group())
    def wrapOff(self,match):
        ''' Regex replace function for quotes '''
        return "<offtopic>%s<reset>"%(match.group())

    def dicer(self,data):
        total = 0
        output = []
        for obj in re.finditer(self.regexDicex,data):
            obj = obj.group()
            if   obj[0] == '+': add = True;  obj = obj[1:]
            elif obj[0] == '-': add = False; obj = obj[1:]
            else:               add = True;  obj = obj
            if 'd' not in obj:
                color = "<blue>"#colorize('blue')
                if add: output.append("<grey>+%s<reset>"%obj); total += int(obj)
                else:   output.append("<grey>-%s<reset>"%obj); total -= int(obj)
            else:
                tok = obj.split('d')
                result = self.roll(tok[0],tok[1])
                if not result: return "<grey>[<red>Dice value too high<reset>]<reset>"
                result,exploded = result
                if exploded: color = '<gold>'
                else:        color = '<SeaGreen>'
                if add: output.append("%s+%s<reset>"%(color,obj)); total += result
                else:   output.append("%s-%s<reset>"%(color,obj)); total -= result
        return "<grey>[%s: <green>%i<reset>]<reset>"%("".join(output),total)

    def roll(self,rolls,sides):
        if len(rolls) == 0: rolls = 1
        rolls = int(rolls)
        sides = int(sides)
        
        if not 0 < rolls <= 20: return False
        if not 1 < sides <= 100: return False
        exploding = True
        exploded  = False
        total = 0
        rolls = range(rolls)
        for i in rolls:
            result = random.randint(1,sides)
            if result == sides and exploding: rolls.append(1); exploded = True
            total += result
        return (total,exploded)

    def timestamp(self):
        ''' this function should generate a unique timestamp '''
        timestamp = time.time()
        while timestamp in self.timestamps:
            timestamp += 0.00001
        self.timestamps.append(timestamp)
        return timestamp
    
class Account:
    def __init__(self,world,name,pwd):
        self.world=world
        self.name    = name.lower()
        self.pwd     = pwd
        self.avatars = []
    
class Avatar:
    def __init__(self,name,account,location):
        self.id   = name.lower()
        self.name = name
        self.account = account
        self.account.avatars.append(self)
        self.location = location
        self.location.addAvatar(self)
        self.messages = []
        self.player = None
        
    def __getstate__(self):
        d = self.__dict__.copy() 
        del d['player']
        return d
        
    def tell(self,message):
        self.messages.append(message.i)
        
    def move(self,location):
        if self.location: self.sendAnnounce('%s has left.'%self.name)
        
    
    def attach(self,player):
        if player.avatar:
            player.avatar.detach()
        player.avatar  = self
        self.player    = player
        player.sendMessage("You are now attached to %s"%self.name)
        
    def detach(self):
        if self.player:
            self.player.sendMessage("You have detached from the body of %s."%self.name)
            self.player.avatar = None
            self.player = None
            
class Location:
    def __init__(self,world,name,title):
        self.world = world
        self.avatars = []
        self.name = name.lower()
        self.title = title
        
    def addAvatar(self,avatar):
        if avatar not in self.avatars: self.avatars.append(avatar)
        self.sendAnnounce("%s has arrived."%(avatar.name))
    def delAvatar(self,avatar):
        if avatar in self.avatars: self.avatars.remove(avatar)
        
    def sendAnnounce(self,content):
        for avatar in self.avatars:
            avatar.tell(content,self.world.timestamp
    



class Player(LineReceiver):
    def connectionMade(self):
        print "connectionMade"
        self.handle   = self.handleLogin
        self.state    = 0
        self.nick     = False
        self.account  = False
        self.pwd      = False
        self.defaction= None
        self.colors   = {}
        self.avatar      = None
        self.regexHilite = None
        self.color    = ''
        self.typing   = False
        self.gm       = False
        self.getname  = False
        
        self.protocolVersion = "3"
        
        self.commands = {
        'say':self.gameSay,
        'emote':self.gameEmote,
        'me':self.gameEmote,
        'tell':self.gameTell,
        'look':self.gameLook}
        #'avatar':self.gameAvatar}
        
        
        self.triggers = {
        '.':self.gameSay,
        '*':self.gameEmote,
        ':':self.gameEmote,
        '#':self.gameDescribe,
        '(':self.gameOfftopic}
        
        self.loginGreeting = open('strings/login_motd.txt','r').read()
        self.loginError = self.loginGreeting + open('strings/login_motd.txt','r').read()
        
        
        self.world = self.factory.world
        print "end connection made"
        
    def lineReceived(self, data):
        #print("Line received!")
        data = data.decode('utf-8')
        self.handle(data)
    
    def connectionLost(self,reason):
        self.world.disconnectPlayer(self)
    
    def write(self,data,newline=True):
        if newline: data = ("%s\r\n"%data).encode('utf-8')
        self.transport.write(data)
        
    def handleLogin(self,data):
        tok  = data.split( )
        hdr  = tok[0]
        print "Player:handleLogin"
        # Ignore typing announcements
        if hdr == 'pnt' or hdr == 'pit': return
        
        # Handshake state 
        # Ensure that the client is a ropeclient AND a proper version!'''
        if self.state == 0:
            if "SUPERHANDSHAKE" in data:
                print "handshake",data
                if hdr == u'hsk' and len(tok) == 3:
                    if tok[2] == self.protocolVersion: self.sendMessage(self.loginGreeting);self.state = 1
                    else:                              self.write(self.loginError);self.state = -1
                else:                                  self.write(self.loginError);self.state = -1
            else: self.transport.loseConnection() # Not a ropeclient! Lets drop them for now.
        
        elif self.state == 1 and len(data) > 2:
            print "Handle data",data,ord(data[0]),ord(data[1])
            if   hdr == 'nck' and len(tok) == 2: self.nick = tok[1];self.account = self.nick.lower()
            elif hdr == 'pwd' and len(tok) == 2: self.pwd  = tok[1]
            elif hdr == 'dfa' and len(tok) == 2: 
                defaction = tok[1]
                if   defaction == 'speak': self.defaction = "speak"
                elif defaction == 'offtopic': self.defaction = "offtopic"
                else:self.defaction = None
            elif hdr == 'clr' and len(tok) == 3: self.colors[tok[1]] = tok[2]
            
            if self.nick and self.colors.has_key('highlight') and not self.pwd:
                if   self.world.accounts.has_key(self.account):  self.write(u'pwd A password is required to access your account')
                else:                                        self.write(u'pwd New player, please type your password (your password is encrypted client side, no worries)')
                    
            elif self.nick and self.colors.has_key('highlight') and self.pwd:
                if self.world.accounts.has_key(self.account):
                    print self.world.accounts[self.account].pwd
                    print self.pwd
                    if self.world.accounts[self.account].pwd == self.pwd: 
                        self.account = self.world.accounts[self.account]
                        self.world.connectPlayer(self)
                        self.handle = self.handleGame
                    else: self.write("Invalid password");self.transport.loseConnection()
                else:
                    self.world.accounts[self.account] = Account(self.world,self.account,self.pwd)
                    # do a save
                    self.account = self.world.accounts[self.account]
                    self.world.saveAll()
                    self.world.connectPlayer(self)
                    self.handle = self.handleGame
            else:
                print self.nick,self.colors.has_key('highlight'),self.pwd
                
    '''
    def announce(self,data,style="default"):
        global linebuffer
        text = self.wrap(data,style=style)
        linebuffer.append( text)
        for player in players: player.write(text)
    '''

    

        
    '''
    def setname(self,name):
        self.name = name
        first = self.name.split(' ')[0].lower()
        print "Setting name to:",first
        self.regex = re.compile("(?<!^)(?<![(])%s"%first,re.IGNORECASE)
    def tell(self,tok):
        who = tok[0].lower()
        txt = " ".join(tok[1:])
        tells = []
        told = 0
        for player in players:
            if player.nick.lower() == who or who in player.name.lower(): player.write("%s(%s%s tells you: %s)"%(colorize('tell'),colorize('tell'),self.name,txt));told=1
            elif player.nick.lower() == self.nick.lower(): continue
            elif player.gm: player.write("%s(%s%s tells %s: %s)"%(colorize('yellow'),colorize('yellow'),self.name,who,txt))

        if told: self.write("%s(%sYou tell %s: %s)"%(colorize('tell'),colorize('tell'),who,txt))
        else: self.write("%s(%sNobody here with that name)"%(colorize('tell'),colorize('tell')))
    '''
    def handleGame(self,recv):
        # First we validate the data #
        if len(recv) < 2: return
        try: recv = recv.decode('utf-8')
        except: 
            print "Player:handleGame: Received non-unicode data from the client, ignoring."
            return
        tok = recv.split(' ')
        
        # Second we read the packet type #
        packetid = tok[0]
        if   packetid == u'pnt':                  self.handleTyping(False);print "Player:handleGame: typing false"
        elif packetid == u'pit':                  self.handleTyping(True); print "Player:handleGame: typing true"
        elif packetid == u'msg' and len(tok) > 1: self.handleMessage(tok[1:])
        else: 
            print "Player:handleGame: Received unknown packet from",self.nick
            print "Player:handleGame: This:",recv
            
    def handleTyping(self,state):
        self.typing = state
        if self.typing: data = u'pit %s'%self.nick
        else:           data = u'pnt %s'%self.nick
        for player in self.world.players.values():  player.write(data)
        
    def handleMessage(self,messageParams):
        print "Player:handleMessage"
        if len(messageParams) < 1: print "Player:handleMessage: Message too short";return
        #messageParams = messageContent.split(' ')
        messageContent = " ".join(messageParams)
        messageCommand = messageParams[0].lower()
        messageTrigger = messageCommand[0]
        print self.defaction
        
        if self.getname: # this can be expanded later
            avatar = Avatar(messageParams[0],self.account,self.world.locations['spawn'])
            self.account.avatars.append(avatar)
            avatar.attach(self)
            self.getname = False #Todo save world"
            return
        
        if self.defaction and len(messageCommand) > 1: messageCommand = messageCommand[1:]
        if self.commands.has_key(messageCommand): self.commands[messageCommand](messageContent[len(messageCommand)+1:])
        elif self.triggers.has_key(messageTrigger): self.triggers[messageTrigger](messageContent[1:])
        else:
            if self.defaction == 'talk':       self.gameSay(messageContent) #TODO: change gameSay to gameTalk?
            elif self.defaction == 'offtopic': self.gameOfftopic(messageContent)
            else:  self.sendMessage("Excuse me?")
        self.handleTyping(False)
        

    def sendMessage(self,content,owner=False,timestamp=False):
        ''' Sends the message to the client. 
            The message is wrapped and processed here before sending '''
        content = self.world.messageWrap(content)
        if not timestamp: timestamp = self.world.timestamp()
        if not owner: owner='Server'
        print "Send ->",timestamp,content
        self.write(u'msg %s %f %s'%(owner,timestamp,content))
        
    def gameSay(self,messageContent):
        messageParams = messageContent.split(' ') #TTODO FIX ERROR
        if not self.avatar:
            self.gameOfftopic("(%s: %s)"%(self.nick,messageContent))
            return
        if messageParams[0].lower() == 'to' and len(messageParams) > 2:
            messageTo = messageParams[1]
            #if players.has_key(messageTo.lower()):
             #   pass #TODO: Finish this 
        else: 
            pass #Check for avatar.. fail if you don't have an avatar
        
    def gameEmote(self,messageContent):
        pass
    def gameTell(self,messageContent):
        pass
    def gameDescribe(self,messageContent):
        pass
    
    def gameLook(self,messageContent):
        pass
    '''
        if len(messageContent) == 0:
            if self.avatar:
                location    = self.world.avatars[self.avatar]['location']
                title       = self.world.locations[location]['title']
                description = self.world.locations[location]['description']
                avatars     = self.world.locations[location]['avatars']
                self.sendMessage("Server",time.time(),"%s"%(title))
                self.sendMessage("Server",time.time(),"%s"%(description))
                self.sendMessage("Server",time.time(),"Here are: %s"%(", ".join(avatars)))
    '''
    def gameOfftopic(self,messageContent):
        # Todo, global and local offtopic?
        if messageContent[0] != '(': messageContent = '(' + messageContent
        if messageContent[-1] != ')': messageContent = messageContent + ')'
        self.world.sendAnnounce(messageContent,self.account,False,True)
    
    '''
    def gameAvatar(self,messageContent):
        tok       = messageContent.split(' ')
        hdr       = tok[0].lower()
        
        if len(messageContent) == 0:  msgBuffer = [self.world.displayAvatars(self,True),"Available commands: ADD, ENTER, LEAVE, DEL"]
        elif hdr == 'add':   msgBuffer = self.gameAvatarNew(tok[1:])
        elif hdr == 'enter': msgBuffer = self.gameAvatarEnter(tok[1:])
        elif hdr == 'leave': msgBuffer = self.gameAvatarLeave(tok[1:])
        elif hdr == 'del':   msgBuffer = self.gameAvatarDel(tok[1:])
        else:                msgBuffer = ["Unknown command"]
        print "BANG"
        self.sendMessage("Server",time.time(),"\n".join(msgBuffer))
          
    def gameAvatarNew(self,params):
        if len(params) == 0: return ["Not enough parameters. Please specify a unique ID for your avatar.",
                                     "Example: avatar add superwarrior"]
        avatarID = params[0].lower()
        addavatar= self.world.addAvatar(self,avatarID)
        if addavatar: return ["Avatar has been created succesfully. You can now use the command 'avatar enter %s' to possess your avatar."%avatarID]
        else:         return ["The ID you specified is already in use. Please try something else."]
    
    def gameAvatarEnter(self,params):
        if len(params) == 0: return ["Not enough parameters. Please specify a unique ID for your avatar.",
                                     "Example: avatar enter superwarrior"]
        avatarID = params[0].lower()
        if not self.world.avatars.has_key(avatarID):             return ["Avatar %s not found."%avatarID]
        if not self.world.avatars[avatarID]['owner'] == self.id: return ["You may not enter this soul."]
        self.avatar = avatarID
        avatar = self.world.avatars[avatarID]
        for line in avatar['history']: self.sendMessage(line[0],line[1],line[2])
        for line in avatar['flush']:   self.world.messageAvatar(avatar['id'],line[2],line[0],line[1])
        self.gameLook('')
        
        return ["You are now attached to %s."%avatarID]
    
    def gameAvatarLeave(self,params):
        return ["not implemented"]
    def gameAvatarDel(self,params):
        return ["not implemented"]
    '''

        
        
        

    """z
        if   messageHeader    == 'say': self.gameSay(" ".join(messageParams[1:]))
        elif messageHeader[0] == '.'  : self.gameSay(messageContent[1:])
        elif messageHeader    == '/me': self.gameEmote
             messageHeader    == 'emote': self.game
        
        data = data.replace('\n',' ')
        data = data.replace('\r', '')
        tok = data.split(' ')
        if len(data) == 2:
            if   data == u'\xff\x00': self.typing = False; self.announce_typing(); return
            elif data == u'\xff\x01': self.typing = True;  self.announce_typing(); return
        #if tok[0]   == 'TYPING': self.typing = True;self.announce_players()
        #elif tok[0] == 'NOT_TYPING': self.typing = False;self.announce_players()
        if tok[0] == '/name': self.setname(" ".join(tok[1:]))#self.name = ;self.regex = re.compile(self.name,re.IGNORECASE)
        elif tok[0] == '/gm': pass#self.gm = (self.gm+1)%2;self.typing = False;self.announce_players()
        elif tok[0] == '/tell': self.tell(tok[1:]);self.typing = False;self.announce_players()
        else: 
            if   data[0] == '*':      self.announce('''%s %s'''%(self.name,data[1:].strip()),style="action")
            elif data[0:3] == '/me':  self.announce('''%s %s'''%(self.name,data[3:].strip()),style="action")
            elif data[0] == '/': pass
            elif data[0] == '!': 
                self.announce('''(%s: %s)'''%(self.name,data))
            elif data[0] == '#': self.announce('''(%s) %s'''%(self.name,data[1:]),style="describe")
            elif data[0] == '(': 
                if data[-1] != ')': data += ')' # People tend to forget to add the last )
                self.announce('''(%s: %s'''%(self.nick,data[1:]))
            else: self.announce('''%s says, "%s"'''%(self.name,data))
            self.typing = False
            self.announce_players()
    """
    

    def wrapHilite(self,match):
        return "%s%s<reset>"%(self.colors['highlight'],match.group())




class PlayerFactory(Factory):
    def __init__(self,game):
        self.protocol = Player
        self.world    = game.world

class World2:
    def __init__(self):
        self.channels = {'spawn':[]}
        self.loadPasswords()
        self.loadAvatars()
        self.loadLocations()
        self.players = {}
        self.history = []
        
        
        
    def loadPasswords(self):
        passwords = pickleLoad('passwd')
        if passwords: self.passwords = passwords
        else:         self.passwords = {}
        
    def savePasswords(self): pickleSave(self.passwords,'passwd')
    
    def loadAvatars(self):
        avatars = pickleLoad('avatars')
        if avatars: self.avatars = avatars
        else:          self.avatars = {}
    def saveAvatars(self): pickleSave(self.avatars,'avatars')
    
    def loadLocations(self):
        locations = pickleLoad('locations')
        if locations: self.locations = locations
        else:          self.locations = {}
    def saveLocations(self): pickleSave(self.locations,'locations') 
    
    def connectPlayer(self,player):
        if self.players.has_key(player.id):
            print "Dual connect, disconnecting the old player."
            self.players[player.id].write("You have logged in elsewhere, disconnecting.")
            self.players[player.id].transport.loseConnection()
        self.players[player.id] = player
        self.sendPlayerlist()
        self.sendHistory(player)
        self.messageWorld('%s has joined the game!'%(player.nick),'Server')
        self.displayAvatars(player)
        print "Connect Player to World OK:",player.id,self.players
        
    def disconnectPlayer(self,player):
        if self.players.has_key(player.id):
            del self.players[player.id]
            self.sendPlayerlist()
            self.messageWorld('%s has quit the game!'%(player.nick),'Server')

    def displayAvatars(self,player,doReturn=False):
        avatars = []
        for avatar in self.avatars.values():
            if avatar['owner'] == player.id: avatars.append(avatar)
        if len(avatars) == 0: buf = ["<red>You have no avatars. To create a new avatar, use the AVATAR command for more information."]
        else: 
            buf = ["-- Your avatars -- "]
            for avatar in avatars: buf.append(avatar['name'])
        if doReturn: return u"\n".join(buf)
        else: player.sendMessage("Server",time.time(),u"\n".join(buf))
        
        
    def sendPlayerlist(self):
        pl = []
        for player in self.players.values(): 
            nick = player.nick
            if player.typing:   nick = "*" + nick
            if player.gm:       nick = "[%s]"%nick
            if player.avatar:   nick = "%s (%s)"%(nick,"has_avatar")
            pl.append(nick)
        ann = u"lop %s"%(" ".join(pl))
        for player in self.players.values(): player.write(ann)
    def sendHistory(self,player):
        for line in self.history:
            player.sendMessage("Server",line[0],line[1])
        
    def messageWorld(self,data,owner="Server",timestamp=False):
        if not timestamp: timestamp = time.time()
        data  = self.messageWrap(data,'offtopic')
        self.history.append((time.time(),data))
        for player in self.players.values():
            player.sendMessage(owner,timestamp,data)
            
    def messageLocation(self,locationID,messageContent,messageOwner='Server',messageTimestamp=False):
        print "messageLocation -->",locationID
        if not messageTimestamp: messageTimestamp = time.time()
        if not self.locations.has_key(locationID): return False
        location = self.locations[locationID]
        
        for avatar in location['avatars']: self.messageAvatar(avatar,messageContent,messageOwner,messageTimestamp)
        
    def messageAvatar(self,avatarID,messageContent,messageOwner='Server',messageTimestamp=False):
        print "messageAvatar -->",avatarID
        print "debug, list of players:",self.players
        
        if not messageTimestamp: messageTimestamp = time.time()
        if not self.avatars.has_key(avatarID): return False
        avatar = self.avatars[avatarID]
        
        if self.players.has_key(avatar['owner']) and self.players[avatar['owner']].avatar == avatar['id']:
            player = self.players[avatar['owner']]
            player.sendMessage(messageOwner,messageTimestamp,messageContent)
            avatar['history'].append((messageOwner,messageTimestamp,messageContent))
        else:
            avatar['flush'].append((messageOwner,messageTimestamp,messageContent))
            
        
    def addAvatar(self,player,avatarID):
        print "addAvatar",avatarID
        if self.avatars.has_key(avatarID): print "addAvatar: invalid avatar ID";return False
        else:
            self.avatars[avatarID] = {
                                'owner':player.id,
                                'id':avatarID,
                                'name':avatarID,
                                'location':'spawn',
                                'history':[],
                                'flush':[],
                                'description':"No description"}
            self.moveAvatar(avatarID,'spawn')
            return True
    def moveAvatar(self,avatarID,location):
        # This function moves an avatar to a new location
        # First we check that the target location exists, and 
        # if it doesn't, we create it.
        
        print "moveAvatar()"
        location = location.lower()
        if not self.avatars.has_key(avatarID): print "moveAvatar: invalid avatar id",avatarID,self.avatars;return False
        avatar = self.avatars[avatarID]
        if not self.locations.has_key(location):
            self.locations[location] = {'id':'location',
                                        'avatars':[],
                                        'title':'No title',
                                        'description':'No description'}
        
        # We remove the character from the old location
        old_location = avatar['location']
        if self.locations.has_key(old_location):
            if avatarID in self.locations[old_location]['avatars']:
                self.locations[old_location]['avatars'].remove(avatarID)
        
        # And add the character to a new location
        avatar['location'] = location
        self.locations[location]['avatars'].append(avatarID)
        
        self.messageLocation(location,'%s has arrived from %s.'%(avatar['name'],self.locations[old_location]['title']))
        
        
   
        

if __name__ == '__main__':
    game = Game()
    reactor.listenTCP(49500, PlayerFactory(game))
    reactor.run()