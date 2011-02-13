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
edi = edit message [edi timestamp message]
pwd = password
clr = color
nck = nick
hsk = handshake
dfa = default action
1 - offtopic
2 - talk
3 - emote
4 - describe

RC TODO
- Hilight command


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
        
        if not messages: messages = {}
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
        
        
        
        
        self.locations['spawn'] = Location(self,'spawn','Spawn')
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
            print "World:connectPlayer: auto attach"
            player.account.avatars[0].attach(player)
        else:
            print "dunno what to do",len(player.account.avatars)
            for avatar in player.account.avatars:
                print avatar,avatar.name
                
    def disconnectPlayer(self,player):
        if player.avatar:
            player.avatar.detach()
            
        if player.account in self.players.keys():
            if self.players[player.account] == player:
                self.players[player.account].transport.loseConnection()
                del self.players[player.account]
                
        self.sendAnnounce('%s has left the game!'%(player.nick))
        self.sendPlayers()
            
    def sendPlayers(self):
        pl = []
        for player in self.players.values(): 
            nick = player.nick
            #if player.typing:   nick = "*" + nick
            if player.gm:       nick = "[%s]"%nick
            if not player.avatar:   nick = "(%s)"%nick
            pl.append(nick)
        ann = u"lop %s"%(" ".join(pl))
        for player in self.players.values(): player.write(ann)
        
    def sendAnnounce(self,message,save=False,owner="Server"):
        ''' Send a public message to all players. This is generally either an offtopic or server announcement'''
        print "World:sendAnnounce: announcing",message
        msg = self.makeMessage(owner,message)
        for player in self.players.values():
            for avatar in player.account.avatars:
                    avatar.actionHear(msg)
            if not player.avatar: player.sendMessage(self.messages[msg][1],self.messages[msg][0])
            
    

        
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
    
    def makeMessage(self,owner,content):
        timestamp = self.timestamp()
        content = self.messageWrap(content)
        self.messages[timestamp] = [owner,content]
        return timestamp
    
class Account:
    def __init__(self,world,name,pwd):
        self.world=world
        self.name    = name.lower()
        self.pwd     = pwd
        self.avatars = []
    
    def hasAvatar(self,avatarid):
        for avatar in self.avatars:
            if avatar.id == avatarid: return avatar
        return False
class Avatar:
    def __init__(self,world,name,account,location):
        self.world=world
        self.id   = name.lower()
        self.name = name
        self.player = None
        self.account = account
        self.oldmessages = []
        self.newmessages = []
        self.account.avatars.append(self)
        self.location = location
        self.location.addAvatar(self)
        self.world.avatars[self.id] = self
        
        
        
    def __getstate__(self):
        d = self.__dict__.copy() 
        d['player'] =None
        return d
        
    def actionHear(self,timestamp):
        ''' This is when the avatar hears something. Everything the avatar hears
         (or sees..) is recorded here. If the player is attached the messages get
        delivered instantly. Message format.. [Unread(1/0),'''
        if self.player:
            self.oldmessages.append(timestamp)
            msg = self.world.messages[timestamp]
            self.player.sendMessage(msg[1],msg[0],timestamp)
        else:
            self.newmessages.append(timestamp)
            
    def getNewMessages(self):
        if len(self.newmessages) >0:
            self.player.sendMessage("-- While you were away, your avatar noticed the following --")
            for timestamp in self.newmessages: # TODO: do something if world doesn't have the requested message
                msg = self.world.messages[timestamp]
                self.player.sendMessage(msg[1],msg[0],timestamp)
            self.player.sendMessage("-- End of new history --")
            self.oldmessages += self.newmessages
            self.newmessages = []
        
    def depart(self):
        if self.location:
            self.location.delAvatar(self)
            self.location = None
    def arrive(self,location):
        if not self.location:
            self.location = location
            self.location.addAvatar(self)
    
    def move(self,location):
        self.depart()
        self.arrive(location)
        
    
    def attach(self,player):
        if player.avatar:
            player.avatar.detach()
        player.avatar  = self
        self.player    = player
        player.sendMessage("You are now attached to %s"%self.name)
        self.getNewMessages()
        self.world.sendPlayers()
        
    def detach(self):
        if self.player:
            self.player.sendMessage("You have detached from the body of %s."%self.name)
            self.player.avatar = None
            self.player = None
        self.world.sendPlayers()
    
    def doAction(self,content,owner=False):
        if not owner and self.player: owner = self.player.account.name
        self.location.sendAnnounce(content,owner)
        
    
class Location:
    def __init__(self,world,name,title):
        self.world = world
        self.avatars = []
        self.name = name.lower()
        self.title = title
        
    def addAvatar(self,avatar):
        print "Location:addAvatar"
        if avatar not in self.avatars: self.avatars.append(avatar)
        self.sendAnnounce("%s has arrived."%(avatar.name))
    def delAvatar(self,avatar):
        if avatar in self.avatars: self.avatars.remove(avatar)
        self.sendAnnounce("%s has left."%(avatar.name))
    def sendAnnounce(self,content,owner="Server"):
        print "Location:sendAnnounce",content
        timestamp = self.world.makeMessage(owner,content)
        
        for avatar in self.avatars:
            avatar.actionHear(timestamp)
    



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
        'look':self.gameLook,
        'possess':self.avatarPossess,
        'depossess':self.avatarDepossess,
        'new':self.avatarNew,
        'del':self.avatarDel,
        'name':self.avatarName,
        'list':self.avatarList}
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
                
                
    def handleGame(self,recv):
        # First we validate the data #
        if len(recv) < 2: return
        #try: recv = recv.decode('utf-8')
        #except: 
        #    print "Player:handleGame: Received non-unicode data from the client, ignoring."
        #    return
        tok = recv.split(' ')
        
        # Second we read the packet type #
        packetid = tok[0]
        if   packetid == u'pnt':                  self.handleTyping(False);print "Player:handleGame: typing false"
        elif packetid == u'pit':                  self.handleTyping(True); print "Player:handleGame: typing true"
        elif packetid == u'msg' and len(tok) > 1: self.handleMessage(tok[1:])
        elif packetid == u'edi' and len(tok) > 1: self.handleEdit(tok[1:])
        else: 
            print "Player:handleGame: Received unknown packet from",self.nick
            print "Player:handleGame: This:",recv
            
    def handleTyping(self,state):
        self.typing = state
        if self.typing: data = u'pit %s'%self.nick
        else:           data = u'pnt %s'%self.nick
        for player in self.world.players.values():  player.write(data)
        
    def handleEdit(self,messageParams):
        print "Player:handleEdit"
        for player in self.world.players.values():
            player.write(u"edi %s"%(" ".join(messageParams)))
            
    def handleMessage(self,messageParams):
        print "Player:handleMessage"
        if len(messageParams) < 1: print "Player:handleMessage: Message too short";return
        #messageParams = messageContent.split(' ')
        messageContent = " ".join(messageParams)
        messageCommand = messageParams[0].lower()
        messageTrigger = messageCommand[0]
        print self.defaction
        
        if self.getname: # this can be expanded later
            if messageParams[0] in self.world.avatars: self.sendMessage("ID already in use");return
            avatar = Avatar(self.world,messageParams[0],self.account,self.world.locations['spawn'])
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
            The message is ---wrapped--- and processed here before sending '''
        if not timestamp: timestamp = self.world.timestamp()
        if not owner: owner='Server'
        print "Send ->",owner,timestamp,content
        self.write(u'msg %s %f %s'%(owner,timestamp,content))
        
    def gameSay(self,messageContent):
        messageParams = messageContent.split(' ') #TTODO FIX ERROR
        if not self.avatar:
            self.gameOfftopic("(%s: %s)"%(self.nick,messageContent))
            return
        else:
            self.avatar.location.sendAnnounce('''%s says, "%s"'''%(self.avatar.name,messageContent),self.account.name)
            
        #if messageParams[0].lower() == 'to' and len(messageParams) > 2:
        #    messageTo = messageParams[1]
        #    #if players.has_key(messageTo.lower()):
        #     #   pass #TODO: Finish this 
        #else: 
        #    pass #Check for avatar.. fail if you don't have an avatar
        
    def gameEmote(self,messageContent):
        if self.avatar:
            self.avatar.location.sendAnnounce("<action>%s %s"%(self.avatar.name,messageContent),self.account.name)
            
    def gameTell(self,messageContent):
        if self.avatar:
            tok = messageContent.split(' ')
            if len(tok) < 2: self.sendMessage("I don't quite get you");return
            target = tok[0].lower()
            message = " ".join(tok[1:])
            
            for avatar in self.world.avatars.values():
                print "if",target,avatar.id
                if target in avatar.id:
                    self.sendMessage('''<tell>You tell %s: %s'''%(avatar.name,message),self.account.name)
                    msg = self.world.makeMessage(self.account.name,'''<tell>%s tells you: %s'''%(self.avatar.name,message))
                    avatar.actionHear(msg)
                    return
            self.sendMessage('''There is no such person''')
            
    def gameDescribe(self,messageContent):
        if self.avatar:
            self.avatar.location.sendAnnounce("<describe>(%s) %s"%(self.avatar.name,messageContent),self.account.name)
    
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
        if messageContent[0] != '(': messageContent = '(%s: '%self.account.name + messageContent
        if messageContent[-1] != ')': messageContent = messageContent + ')'
        self.world.sendAnnounce(messageContent,True,self.account.name)
    

        
        
    def avatarPossess(self,content):
        ''' Posses avatar with tok[0] '''
        tok = content.split(' ')
        if not len(tok) == 1: self.sendMessage('''Use: possess (avatarid)''');return
        if len(tok[0]) < 1: self.sendMessage('''Use: possess (avatarid)''');return
        avatarID = tok[0].lower()
        avatar = self.account.hasAvatar(avatarID)
        if avatar:
            if self.avatar: self.avatar.detach()
            avatar.attach(self)    
        else: self.sendMessage('''You own no such avatar''')
        
    def avatarDepossess(self,content):
        if self.avatar: self.avatar.detach()
        else: self.sendMessage('''You're not possessing an avatar currently''')
        
    def avatarNew(self,content):
        tok = content.split(' ')
        print tok
        if not len(tok) == 1: self.sendMessage('''Use: new (avatarid)''');return
        if len(tok[0]) < 2: self.sendMessage('''Use: new (avatarid)''');return
        avatar = tok[0].lower()
        if avatar in self.world.avatars.keys(): self.sendMessage("Avatar ID already exists. Try some other ID")
        else:
            avatar = Avatar(self.world,avatar,self.account,self.world.locations['spawn'])
            self.sendMessage("Avatar created!")
        
    def avatarDel(self,content):
        tok = content.split(' ')
        if not len(tok) == 1: self.sendMessage('''Use: del (avatarid)''');return
        if len(tok[0]) < 1: self.sendMessage('''Use: del (avatarid)''');return
        avatarID = tok[0].lower()
        avatar = self.account.hasAvatar(avatarID)
        if avatar:
            avatar.detach()
            avatar.depart()
            self.account.avatars.remove(avatar)
            self.sendMessage("Avatar has been deleted")
        else: self.sendMessage("Avatar not found")
        
    def avatarName(self,content):
        tok = content.split(' ')
        if not len(tok) < 3: self.sendMessage('''Use: name (avatarid) (avatar name)''');return
        if len(tok[0]) < 2: self.sendMessage('''Use: name (avatarid) (avatar name)''');return
        avatarID = tok[0].lower()
        avatar = self.account.hasAvatar(avatarID)
        if avatar:
            oldname = avatar.name
            newname = " ".join(tok[1:])
            if len(newname)>20: newname = newname[:20]
            avatar.name = " ".join(tok[1:])
            self.world.sendAnnounce("%s is now known as %s."%(oldname,newname))
        else:self.sendMessage("Avatar not found")
        
    def avatarList(self,content): 
        buf = []
        for avatar in self.account.avatars:
            buf.append("%s --- %s"%(avatar.id,avatar.name))
        self.sendMessage("Your avatars:")
        for line in buf: self.sendMessage(line)
    

    def wrapHilite(self,match):
        return "%s%s<reset>"%(self.colors['highlight'],match.group())




class PlayerFactory(Factory):
    def __init__(self,game):
        self.protocol = Player
        self.world    = game.world


   
        

if __name__ == '__main__':
    game = Game()
    reactor.listenTCP(49500, PlayerFactory(game))
    reactor.run()
