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

1 - offtopic
2 - talk
3 - emote
4 - describe

'''
# TODO: fix color highlight according to protocol
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
import hashlib, random, re, pickle, time

def pickleSave(object,filename):
    f = open(filename,'wb')
    pickle.dump(object,f)
    f.close()
    return True
def pickleLoad(filename):
    try:
        f = open(filename,'rb')
        x = pickle.load(f)
        f.close()
        return x
    except: return False

class Player(LineReceiver):
    def connectionMade(self):
        print "connectionMade"
        self.handle   = self.login
        self.state    = 0
        self.nick     = False
        self.id       = False
        self.pwd      = False
        self.colors   = {}
        self.avatar   = None
        self.color    = ''
        self.typing   = False
        self.gm       = False

        
        self.protocolVersion = "3"
        
        self.commands = {
        'say':self.gameSay,
        'emote':self.gameEmote,
        '/me':self.gameEmote,
        'tell':self.gameTell,
        'look':self.gameLook}
        
        
        self.triggers = {
        '.':self.gameSay,
        '*':self.gameEmote,
        '#':self.gameDescribe,
        '(':self.gameOfftopic}
        
        self.loginGreeting = """Welcome to ropeclient
                           _ _            _   
 _ __ ___  _ __   ___  ___| (_) ___ _ __ | |_ 
| '__/ _ \| '_ \ / _ \/ __| | |/ _ \ '_ \| __|
| | | (_) | |_) |  __/ (__| | |  __/ | | | |_ 
|_|  \___/| .__/ \___|\___|_|_|\___|_| |_|\__|
          |_|                                 
"""
        
        self.loginError = self.loginGreeting + """\n\nUnfortunately it seems your ropeclient is out of date.
        To connect to this server, please update your client from 
           http://eiden.fi/ropeclient
        OR http://eiden.fi/ropeclient/releases
        OR http://github.com/voneiden/ropeclient"""
        
        self.world = self.factory.world
        print "end connection made"
        
    def lineReceived(self, data):
        #print("Line received!")
        self.handle(data)
    
    def connectionLost(self,reason):
        if self in players:
            players.remove(self)
            print (self.nick,"disconnected")
            self.announce("(%s has disconnected!)"%self.nick)
            self.announce_players()
    
    def write(self,data,newline=True):
        data = data.encode('utf-8')
        if newline: self.transport.write(data+'\r\n')
        else: self.transport.write(data)


    def login(self,data):
        data = data.decode('utf-8')
        print "login"
        # Ignore typing announcements
        if len(data) >= 2:
            if data[:2]   == u'\xff\x00': return
            elif data[:2] == u'\xff\x01': return
        
        # Handshake state 
        # Ensure that the client is a ropeclient AND a proper version!'''
        if self.state == 0:
            if "SUPERHANDSHAKE" in data:
                if data[:2] == u'\xff\x30':
                    tok = data.split(' ')
                    if len(tok) == 2:
                        if tok[1] == self.protocolVersion: self.write(self.loginGreeting);self.state = 1
                        else:                              self.write(self.loginError);self.state = -1
                    else:                                  self.write(self.loginError);self.state = -1
                else:                                      self.write(self.loginError);self.state = -1
            else: self.transport.loseConnection() # Not a ropeclient!
        elif self.state == 1 and len(data) > 2:
            print "Handle data",data,ord(data[0]),ord(data[1])
            if   data[:2] == u'\xff\x31': self.nick = data[2:];self.id = self.nick.lower()
            elif data[:2] == u'\xff\x32': self.pwd  = data[2:]
            elif data[:2] == u'\xff\x33': 
                tok = data.split(' ')
                if len(tok) != 2: print "Corrupted color packet";return
                self.colors[tok[0][2:]] = tok[1]
            
            if self.nick and self.colors.has_key('highlight') and not self.pwd:
                if   self.world.passwords.has_key(self.id):  self.write(u'\xff\x32A password is required to access your account')
                else:                                        self.write(u'\xff\x32New player, please type your password (your password is encrypted client side, no worries)')
                    
            elif self.nick and self.colors.has_key('highlight') and self.pwd:
                if self.world.passwords.has_key(self.id):
                    if self.world.passwords[self.id] == self.pwd: 
                        self.world.connectPlayer(self)
                        self.handle = self.game
                    else: self.write("Invalid password");self.transport.loseConnection()
                else:
                    self.world.passwords[self.id] = self.pwd
                    self.world.savePasswords()
                    self.world.connectPlayer(self)
                    self.handle = self.game
            else:
                print self.nick,self.colors.has_key('highlight'),self.pwd
                

    def announce(self,data,style="default"):
        global linebuffer
        text = self.wrap(data,style=style)
        linebuffer.append( text)
        for player in players: player.write(text)




        
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
    def game(self,recv):
        # First we validate the data #
        if len(recv) < 2: return
        try: recv = recv.decode('utf-8')
        except: 
            print "Received non-unicode data from the client, ignoring."
            return
        
        # Second we read the packet type #
        packetid = recv[:2]
        if   packetid == u'\xff\x00': self.gameTyping(False);print "typing false"
        elif packetid == u'\xff\x01': self.gameTyping(True);print "typing true"
        elif packetid == u'\xff\x02': self.gameMessage(recv[2:])
        else: 
            print "Received unknown packet from",self.nick
            print "This:",recv
            
    def gameTyping(self,state):
        self.typing = state
        if self.typing: data = u'\xff\x01%s'%self.nick
        else:           data = u'\xff\x00%s'%self.nick
        for player in self.world.players.values():  player.write(data)
        
    def gameMessage(self,messageContent):
        '''
        messageParams   = recv.split(' ')
        messageOwner    = messageParams[0]
        messageType     = messageParams[1]
        messageTimestamp= messageParams[2]
        messageContent  = " ".join(messageParams[3:])
        '''
        print "Game message"
        if len(messageContent) < 1: print "Message too short";return
        messageParams = messageContent.split(' ')
        messageCommand = messageParams[0].lower()
        messageTrigger = messageCommand[0]
        
        if   self.commands.has_key(messageCommand): self.commands[messageCommand](messageContent[len(messageCommand):])
        elif self.triggers.has_key(messageTrigger): self.triggers[messageTrigger](meessageContent[1:])
        else:
            self.world.messageWorld('(%s: %s)'%(self.nick,messageContent),self.id)
        self.gameTyping(False)
        

    def sendMessage(self,messageOwner,messageTime,messageContent):
        print "Send ->",messageOwner,messageTime,messageContent
        self.write(u'\xff\x02%s %f %s'%(messageOwner,messageTime,messageContent))
        
    def gameSay(self,messageContent):
        messageParams = messageContent.split(' ')
        if messageParams.lower() == 'to' and len(messageParams) > 2:
            messageTo = messageParams[1]
            if players.has_key(messageTo.lower()):
                pass #TODO: Finish this 
    def gameEmote(self,messageContent):
        pass
    def gameTell(self,messageContent):
        pass
    def gameDescribe(self,messageContent):
        pass
    def gameLook(self,messageContent):
        pass
    def gameOfftopic(self,messageContent):
        pass
        """
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

    def dicer(self,data):
        dicex = re.compile('[\+-]?\d*d?\d+')
        total = 0
        output = []
        for obj in re.finditer(dicex,data):
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


class PlayerFactory(Factory):
    def __init__(self,world):
        self.protocol = Player
        self.world    = world

class World:
    def __init__(self):
        self.channels = {'spawn':[]}
        self.loadPasswords()
        self.players = {}
        self.history = []
        self.regexDice  = re.compile("(?:\!\d*d\d*(?:\+|\-)*)(?:(?:(?:\d*d\d*)|\d*)(?:\+|\-)*)*",re.IGNORECASE)
        self.regexQuote = re.compile('".*?"')
        self.regexOff   = re.compile('\(.*?\)')
        self.regexColor = re.compile('(?<=<).*?(?=>)')
        self.regexColorF= re.compile('<.*?>')
        
        
        
    def loadPasswords(self):
        passwords = pickleLoad('passwd')
        if passwords: self.passwords = passwords
        else:         self.passwords = {}
        
    def savePasswords(self): pickleSave(self.passwords,'passwd')
        
    def connectPlayer(self,player):
        if self.players.has_key(player.id):
            print "Dual connect, disconnecting the old player."
            self.players[player.id].write("You have logged in elsewhere, disconnecting.")
            self.players[player.id].transport.loseConnection()
        self.players[player.id] = player
        self.sendPlayerlist()
        self.sendHistory(player)
        self.messageWorld('%s has joined the game!'%(player.nick),'Server')
        print "Connect Player to World OK:",player.id,self.players
        
    def disconnectPlayer(self,player):
        if self.players.has_key(player.id):
            del self.players[nick]
        self.messageWorld('%s has quit the game!'%(player.nick),'Server')
        
    def sendPlayerlist(self):
        pl = []
        for player in self.players.values(): 
            nick = player.nick
            if player.typing:   nick = "*" + nick
            if player.gm:       nick = "[%s]"%nick
            if player.avatar:   nick = "%s (%s)"%(nick,"has_avatar")
            pl.append(nick)
        ann = u"\xff\xa0%s"%(" ".join(pl))
        for player in self.players.values(): player.write(ann)
    def sendHistory(self,player):
        for line in self.history:
            player.sendMessage("Server",line[0],line[1])
        
    def messageWorld(self,data,owner="Server",timestamp=False):
        if not timestamp: timestamp = time.time()
        self.history.append((time.time(),data))
        for player in self.players.values():
            player.sendMessage(owner,timestamp,data)
    
    def messageWrap(self,data,style='default'):
        ''' this version supports full regex. probably the 4th time I rewrote it
        Initial color is WHITE. When you change color, please remember to RESET
        '''
        data = re.sub(self.regexDice,self.wrapDice,data)   #Search for dice combinatinos
        data = re.sub(self.regexQuote,self.wrapQuote,data) #Search for text in between quotes
        data = re.sub(self.regexOff,self.wrapOff,data)     #Search for offtopic 
        
        for player in players:
            data=re.sub(player.regexHilite,player.wrapHilite,data)#Search for player name highlights
        if   style == "default":  pass #data = "%s%s"%('<white>',data)
        elif style == "describe": data = "%s%s"%('<describe>',data)
        elif style == "action":   data = "%s%s"%('<action>',data)
        else: data = "%s%s"%('<red>',data)
        
        ''' Building a color stack

            To be able to properly color everything,
            the final coloring must be done after
            the regex coloring. The final coloring
            looks for reset values, and then chooses
            the appropriate color to reset to from the
            color stack. It's pretty cool.
        '''
        colorstack = []
        for color in re.finditer(self.regexColorF,data):
            x = color.group()
            reset = '<reset>'
            if x == reset:
                try: 
                    colorstack.pop()
                    data=data.replace(reset,colorstack[-1],1)
                except: data=data.replace(reset,'<red>',1);print "Wrap(): Too many resets by %s?"%self.nick
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


if __name__ == '__main__':
    world = World()
    reactor.listenTCP(49500, PlayerFactory(world))
    reactor.run()
