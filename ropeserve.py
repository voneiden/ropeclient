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

    Copyright 2010 Matti Eiden <snaipperi()gmail.com>
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

commands = {
'/re':'%s'%ansi(COLOR['red']),
'/gr':'%s'%ansi(COLOR['green']),
'/bl':'%s'%ansi(COLOR['blue']),
'/ye':'%s'%ansi(COLOR['yellow']),
'/cl':'CLEAR'}

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
                
                self.announce("(%s has joined the game!)"%self.nick)
                #pl = []
                #for player in players: pl.append(player.nick)
                #self.announce("D_PLAYERS %s"%(" ".join(pl))) 
                self.announce_players()
                for line in linebuffer[-100:]:
                    self.write(line)
            elif tok[0] == 'SETNAME':
                self.setname(" ".join(tok[1:]))
                
            elif tok[0] == 'SETCOLOR':
                try: self.color = colorize(" ".join(tok[1:]))
                except: self.color = colorize('gray'); self.write("Invalid color, defaulting to gray")
            
    def announce(self,data):
        global linebuffer
        text = self.wrap(data)
        linebuffer.append( text)
        for player in players: player.write(text)
    def rf_dice(self,match):
        ''' Regex replace function for dice rolls '''
        roll = self.dice(match.group())
        if roll:
            return "%s[%s: %s%s%s]%s"%(
                colorize('gray'),
                roll[0],
                colorize('green'),
                roll[1],
                colorize('reset'),
                colorize('reset'))
        else: return match.group()
    def rf_quote(self,match):
        ''' Regex replace function for quotes '''
        return "%s%s%s"%(colorize('cyan'),match.group(),colorize('reset'))
    def rf_off(self,match):
        ''' Regex replace function for quotes '''
        return "%s%s%s"%(colorize('gray'),match.group(),colorize('reset'))
    def rf_nam(self,match):
        return "%s%s%s"%(self.color,match.group(),colorize('reset'))
    def rf_color(self,match):
        return "\033%s"%match.group()
    def wrap(self,data):
        ''' this version supports full regex. probably the 4th time I rewrote it
        Initial color is WHITE. When you change color, please remember to RESET
        '''
        data = re.sub("<.*?>",self.rf_color,data)
        data = re.sub(self.re_dice,self.rf_dice,data)   #Search for dice combinatinos
        data = re.sub(self.re_quote,self.rf_quote,data) #Search for text in between quotes
        data = re.sub(self.re_off,self.rf_off,data)     #Search for offtopic 
        
        for player in players:
            data=re.sub(player.regex,player.rf_nam,data)#Search for player name highlights
        data = "%s%s"%(colorize('white'),data)


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
            #print "match:",x
            #print "reset:",reset
            if x == reset:
                #print "yess"
                colorstack.pop()
                data=data.replace(reset,colorstack[-1],1)
            else: colorstack.append(x)

        return data
        
    
    def setname(self,name):
        self.name = name
        first = self.name.split(' ')[0].lower()
        print "Setting name to:",first
        self.regex = re.compile("(?!^)%s"%first,re.IGNORECASE)
    def tell(self,tok):
        who = tok[0].lower()
        txt = " ".join(tok[1:])
        tells = []
        told = 0
        for player in players:
            if player.nick.lower() == who or who in player.name.lower(): player.write("%s(%s%s tells you: %s))"%(colorize('magenta'),colorize('magenta'),self.name,txt));told=1
            elif player.nick.lower() == self.nick.lower(): pass
            elif player.gm: player.write("%s(%s%s tells %s: %s)"%(colorize('yellow'),colorize('yellow'),self.name,who,txt))

        if told: self.write("%s(%sYou tell %s: %s)"%(colorize('magenta'),colorize('magenta'),who,txt))
        else: self.write("%s(%sNobody here with that name)"%(colorize('magenta'),colorize('magenta')))

    def game(self,data):
        if len(data) == 0: return
        data = data.decode('utf-8')
        tok = data.split(' ')
        if tok[0] == 'TYPING': self.typing = True;self.announce_players()
        elif tok[0] == 'NOT_TYPING': self.typing = False;self.announce_players()
        elif tok[0] == '/name': self.setname(" ".join(tok[1:]))#self.name = ;self.regex = re.compile(self.name,re.IGNORECASE)
        elif tok[0] == '/gm': self.gm = (self.gm+1)%2;self.typing = False;self.announce_players()
        elif tok[0] == '/tell': self.tell(tok[1:]);self.typing = False;self.announce_players()
        else: 
            if data[0] == '*': self.announce('''%s %s'''%(self.name,data[1:]))
            elif data[0] == '!': 
                self.announce('''(%s: %s)'''%(self.name,data))
            elif data[0] == '#': self.announce('''(%s) %s'''%(self.name,data[1:]))
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




        
    def dice(self,data):
        ''' This is an old dice function I wrote long time ago
            It takes dice data, sums and differences. It works
            very well, however it looks quite complex now. Again,
            could look neater if done with regex, but I'm happy
            the way it works now.
        '''
        x=data
        roll = [] # Dices we still need to roll [add/subtract, dice string]
        rolled = [] # Dices we have rolled: [add/subtract, dice string, result]

        y = x[1:].split('+') # Ignore the ! in the beginning, split the shit from + signs
        for tok in y:        # for every PLUS..
            z=tok.split('-') # Split the splitted shit from - signs
            for i,obj in enumerate(z):          # For every MINUS after a PLUS
                if len(obj) == 0: continue      # skip empty shit (for ex: !-d6 looks like [EMPTY,d6]
                if i == 0: roll.append([1,obj]) # if it's the first it's a PLUS
                else: roll.append([-1,obj])     # all the rest is MINUS
        while len(roll) > 0:       # While we have something to roll, do it.
            a,d = roll.pop(0)      # Pop the first out from the queue list
            if 'd' in d:           # If there is a "d", it's a dice (ex. 2d6)
                tok = d.split('d') # So lets split the shit (xdy)
                try: x=int(tok[0]) # Just in case it's soemthing like "d6", we assume x to be one (1d6)
                except: x = 1      # Yep.
                if 1 > x or x > 10: rolled.append([a,">%s<"%d,0]); continue # If the number of dices to roll is too big
                try: y = int(tok[1])                                        # Check that the y is a number
                except: rolled.append([a,"?%s?"%d,0]); continue             # if it's fucked up, screw that.
                if 2 > y or  y > 200: rolled.append([a,">%s<"%d,0]); continue # check that it's not a crazy value
                for i in xrange(x):                     # Do the dice rolling loop
                    r=random.randint(1,y)               # random!
                    if r == y: roll.append((a,'d%i'%y)) # it's exploding!
                    rolled.append([a,'d%i'%y,r])        # done rolling 
            else:                                                           # Guess it's not a dice (no "d")
                try:                                                        # Lets try
                    i = int(d)                                              # Maybe it's a number
                    rolled.append([a,d,i])                                  # No errors, cool!
                except: rolled.append([a,"error!%s!error"%d,0]); continue   # Nope, it's something weird.
        
        tot = 0                                             # Total result
        output = []                                         # Info string
        for obj in rolled:                                  # for everything in the rolled list
            if obj[0] == 1:                                 # if it's 1, it means it's ADD. else SUBTRACT
                tot += obj[2]                               # So add the result to total
                output.append("+[%s:%i]"%(obj[1],obj[2]))   # and write info to 
            else:                                           # its SUBTRAACT
                tot -= obj[2]                               # minus it
                output.append("-[%s:-%i]"%(obj[1],obj[2]))  # write it
        if tot == 0: return                                 # dont bother to send if there are no results   
        #msg.Chat.SendMessage("%s rolls: %i (%s)"%(msg.FromDisplayName,tot,"".join(output))) #combine and send it
        #return "[(%s) = %s]"%(str(tot), data[1:])#"".join(output))
        return data[1:],str(tot)

class ServeGameFactory(Factory):
    protocol = ServeGame
    def __init__(self, text=None):
        if text is None:
            text = """Sup bro. Please use a %stelnet/mud%s client that has black background. Using a command line is a good idea too."""%(colorize('red'),colorize('white'))
        self.text = text

if __name__ == '__main__':
    reactor.listenTCP(49500, ServeGameFactory())
    reactor.run()
