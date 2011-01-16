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


from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
import hashlib, random, re


players = []
chartoplayer = {}

linebuffer  = []
NOECHO = '\xff\xfb\x01'
ECHO   = '\xff\xfc\x01'

CSI = '\033'
CSIregex = re.compile('\033<.*?>')
COLOR = {
    'reset':'000',
    'black':'001',
    'red':'002',
    'green':'003',
    'yellow':'004',
    'blue':'005',
    'magneta':'006',
    'cyan':'007',
    'white':'008',
    'gray':'009',
    'dim gray':'010'}


def colorize(color):
    return "%s<%s>"%(CSI,color)

def ansi(code):
    return CSI + code 



class ServeGame(LineReceiver):
    def connectionMade(self):
        self.handle = self.login
        self.state = 0
        self.color = ''
        self.typing = False
        self.gm     = False
        self.re_dice = re.compile("(?:\!\d*d\d*(?:\+|\-)*)(?:(?:(?:\d*d\d*)|\d*)(?:\+|\-)*)*",re.IGNORECASE)
        self.re_quote = re.compile('".*?"')
        self.re_off   = re.compile('\(.*?\)')
    def lineReceived(self, data):
        print("Line received!")
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
        tok = data.split(' ')
        self.typing = False
        if tok[0] == 'TYPING': self.typing = True
        elif tok[0] == 'NOT_TYPING': self.typing = False

        if self.state == 0:
            print ("Got data",data)
            if data != "SUPERHANDSHAKE": self.transport.loseConnection()
            self.state = 1
        else:
            tok = data.split(' ')
            if tok[0] == 'SETNICK':
                self.nick = tok[1]
                self.handle = self.game
                players.append(self)
                
                
                #pl = []
                #for player in players: pl.append(player.nick)
                #self.announce("D_PLAYERS %s"%(" ".join(pl))) 
                self.announce_players()
                for line in linebuffer[-100:]:
                    self.write(line)
                self.announce("(%s has joined the game!)"%self.nick)
            elif tok[0] == 'SETNAME':
                self.setname(" ".join(tok[1:]))
                
            elif tok[0] == 'SETCOLOR':
                try: self.color = colorize(" ".join(tok[1:]))
                except: self.color = colorize('gray'); self.write("Invalid color, defaulting to gray")
            
    def announce(self,data,style="default"):
        global linebuffer
        text = self.wrap(data,style=style)
        linebuffer.append( text)
        for player in players: player.write(text)
    def rf_dice(self,match):
        ''' Regex replace function for dice rolls '''
        roll = self.dicer(match.group())
        if roll: return roll
        else:    return match.group()
    def rf_quote(self,match):
        ''' Regex replace function for quotes '''
        return "%s%s%s"%(colorize('talk'),match.group(),colorize('reset'))
    def rf_off(self,match):
        ''' Regex replace function for quotes '''
        return "%s%s%s"%(colorize('offtopic'),match.group(),colorize('reset'))
    def rf_nam(self,match):
        return "%s%s%s"%(self.color,match.group(),colorize('reset'))
    def rf_color(self,match):
        return "\033%s"%match.group()
    def wrap(self,data,style):
        ''' this version supports full regex. probably the 4th time I rewrote it
        Initial color is WHITE. When you change color, please remember to RESET
        '''
        data = re.sub(self.re_dice,self.rf_dice,data)   #Search for dice combinatinos
        data = re.sub("<.*?>",self.rf_color,data)       #Search for color requests
        data = re.sub(self.re_quote,self.rf_quote,data) #Search for text in between quotes
        data = re.sub(self.re_off,self.rf_off,data)     #Search for offtopic 
        
        for player in players:
            data=re.sub(player.regex,player.rf_nam,data)#Search for player name highlights
        if   style == "default": data = "%s%s"%(colorize('white'),data)
        elif style == "describe": data = "%s%s"%(colorize('describe'),data)
        elif style == "action":   data = "%s%s"%(colorize('action'),data)

        ''' Building a color stack

            To be able to properly color everything,
            the final coloring must be done after
            the regex coloring. The final coloring
            looks for reset values, and then chooses
            the appropriate color to reset to from the
            color stack. It's pretty cool.
        '''
        colorstack = []
        for color in re.finditer(CSIregex,data):
            x = color.group()
            reset = '\033<reset>'
            if x == reset:
                try: 
                    colorstack.pop()
                    data=data.replace(reset,colorstack[-1],1)
                except: data=data.replace(reset,'\033<red>',1);print "Wrap(): Too many resets by %s?"%self.nick
            else: colorstack.append(x)

        return data
        
    
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
            if player.nick.lower() == who or who in player.name.lower(): player.write("%s(%s%s tells you: %s))"%(colorize('tell'),colorize('tell'),self.name,txt));told=1
            elif player.nick.lower() == self.nick.lower(): continue
            elif player.gm: player.write("%s(%s%s tells %s: %s)"%(colorize('yellow'),colorize('yellow'),self.name,who,txt))

        if told: self.write("%s(%sYou tell %s: %s)"%(colorize('tell'),colorize('tell'),who,txt))
        else: self.write("%s(%sNobody here with that name)"%(colorize('tell'),colorize('tell')))

    def game(self,data):
        if len(data) == 0: return
        data = data.decode('utf-8')
        tok = data.split(' ')
        if tok[0]   == 'TYPING': self.typing = True;self.announce_players()
        elif tok[0] == 'NOT_TYPING': self.typing = False;self.announce_players()
        elif tok[0] == '/name': self.setname(" ".join(tok[1:]))#self.name = ;self.regex = re.compile(self.name,re.IGNORECASE)
        elif tok[0] == '/gm': self.gm = (self.gm+1)%2;self.typing = False;self.announce_players()
        elif tok[0] == '/tell': self.tell(tok[1:]);self.typing = False;self.announce_players()
        else: 
            if data[0] == '*': self.announce('''%s %s'''%(self.name,data[1:]),style="action")
            elif data[0] == '!': 
                self.announce('''(%s: %s)'''%(self.name,data))
            elif data[0] == '#': self.announce('''(%s) %s'''%(self.name,data[1:]),style="describe")
            elif data[0] == '(': self.announce('''(%s: %s'''%(self.nick,data[1:]))
            else: self.announce('''%s says, "%s"'''%(self.name,data))
            self.typing = False
            self.announce_players()
    def announce_players(self):
        pl = []
        for player in players: 
            nick = player.nick
            if player.typing: nick = "*" + nick
            if player.gm:  nick = "[%s]"%nick
            pl.append(nick)
        ann = "D_PLAYERS %s"%(" ".join(pl))
        for player in players: player.write(ann)

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
        if not 0 < rolls <= 100: return False
        exploding = True
        exploded  = False
        total = 0
        rolls = range(rolls)
        for i in rolls:
            result = random.randint(1,sides)
            if result == sides and exploding: rolls.append(1); exploded = True
            total += result
        return (total,exploded)

class ServeGameFactory(Factory):
    #protocol = ServeGame
    def __init__(self,world):
        self.protocol = ServeGame
        self.world    = world
        Factory.__init__(self)

class World:
    def __init__(self):
        self.channels = {'spawn':[]}
        self.players  = {}
        
    def connect(self,player):
        nick = player.nick.lower()
        if self.players.has_key(nick):
            print "Dual connect, disconnecting the old player."
            self.players[nick].write("You have logged in elsewhere, disconnecting.")
            self.players[nick].transport.loseConnection()
        self.players[nick] = player
        print "Connect:",nick,self.players
        
    def disconnect(self,player):
        nick = player.nick.lower()
        if self.players.has_key(nick):
            del self.players[nick]
        print "Disconnect:",nick,self.players
    '''
    def join(self,avatar,channel):
        channel = channel.lower()
        avatar  = avatar.lower()
        
        if self.channels.has_key(channel):
            self.channels[channel.append(player)
        else:
            self.channels[channel] = [player]
        print "Join:",player
            
    def part(part,player,channel):
        channel = channel.lower()
        player = player.lower()
        if self.channels.has_key(channel):
            if player in self.channels[channel]:
                self.channels[channel].remove(player)
                return True
            else: return False
        else: return False
    '''
if __name__ == '__main__':
    world = World()
    reactor.listenTCP(49500, ServeGameFactory(world))
    reactor.run()
