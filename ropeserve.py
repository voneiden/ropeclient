from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
import hashlib, random


players = []
chartoplayer = {}

linebuffer  = []
NOECHO = '\xff\xfb\x01'
ECHO   = '\xff\xfc\x01'

CSI = '\033['

COLOR = {
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
        #self.write(self.factory.text)
        #self.write("Login: ")
        #self.transport.loseConnection()
        self.typing = False
        self.gm     = False
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
                chartoplayer[self.name] = self
                self.announce("(%s has joined the game!)"%self.nick)
                #pl = []
                #for player in players: pl.append(player.nick)
                #self.announce("D_PLAYERS %s"%(" ".join(pl))) 
                self.announce_players()
                for line in linebuffer[-100:]:
                    self.write(line)
            elif tok[0] == 'SETNAME':
                self.name = " ".join(tok[1:])
            elif tok[0] == 'SETCOLOR':
                try: self.color = CSI + COLOR[" ".join(tok[1:])]
                except: self.color = CSI + COLOR['gray']; self.write("Invalid color, defaulting to gray")
            
    def announce(self,data):
        global linebuffer
        text = self.wrap(data)
        linebuffer.append( text)
        for player in players: player.write(text)
    def wrap(self,data):
        ''' Miten ois v2 mika lukee koko paskan kirjain kirjaimelta -> varien sailytys onnistuis '''
        # First talking
        quote = False
        offtopic = False
        dice  = False
        cmode = False
        output = ''
        dbuf = ''
        cbuf = ''
        color = [ansi(COLOR['white'])]
        print data
      
        for char in data:

            if char == '!' and not dice:
                dbuf = '!'
                dice = 1
                continue

            elif dice == 1:
                if char.isdigit():
                    dbuf += char
                    dice = 2
                    continue
                elif char == 'd':
                    dbuf += char
                    dice = 3
                    continue
                else:
                    output += dbuf
                    dbuf = ''
                    dice = False
                    
                
            elif dice == 2:
                if char.isdigit():
                    dbuf += char
                    continue
                elif char == 'd':
                    dbuf += char
                    dice = 3
                    continue
                else:
                    roll = self.dice(dbuf)
                    if roll:
                        color.append(ansi(COLOR['gray']))
                        output += color[-1] + '[' + roll[0] + ': '
                        color.append(ansi(COLOR['green']))
                        output += color[-1] + roll[1]
                        color.pop()
                        output += color[-1] + ']'
                        color.pop()
                        output += color[-1]
                    else:
                        output += dbuf
                    dbuf = ''
                    dice = False
                    continue

            elif dice == 3:
                if char.isdigit():
                    dbuf += char
                    continue
                elif char == '+' or char == '-':
                    dbuf += char
                    dice = 1
                    continue
                else:
                    dice = False
                    roll = self.dice(dbuf)
                    if roll:
                        color.append(ansi(COLOR['gray']))
                        output += color[-1] + '[' + roll[0] + ': '
                        color.append(ansi(COLOR['green']))
                        output += color[-1] + roll[1]
                        color.pop()
                        output += color[-1] + ']'
                        color.pop()
                        output += color[-1]
                    else:
                        output += dbuf

                    dbuf = ''


            if char == '/' and not cmode:
                cmode = 1
                cbuf += char
                continue
            elif cmode == 1:
                cmode = 2
                cbuf += char
                continue
            elif cmode == 2:
                cmode = False
                cbuf += char
                try: 
                    c = commands[cbuf]
                    if c == 'CLEAR':
                        color.pop()
                        output += color[-1]
                    else:
                        output += c
                        color.append(c)
                except: output += cbuf
                cbuf = ''
                continue

            if char == '"' and not quote:
                quote = True
                color.append(ansi(COLOR['cyan']))
                output +=  color[-1]+ '"'
                continue
            elif char == '"' and quote:
                quote = False
                color.pop()
                output += '"' + color[-1]
                continue

            elif char == '(' and not offtopic:
                offtopic = True
                color.append(ansi(COLOR['gray']))
                output += color[-1] + "("
                continue
            elif char == ')' and offtopic:
                offtopic = False
                color.pop()
                output += ")" + color[-1]
                continue
            
                
            else: output += char
            #output += ' '
        #output += dbuf
        if len(dbuf) > 0: 
            roll=self.dice(dbuf)
            if roll: 
                        color.append(ansi(COLOR['gray']))
                        output += color[-1] + '[' + roll[0] + ': '
                        color.append(ansi(COLOR['green']))
                        output += color[-1] + roll[1]
                        color.pop()
                        output += color[-1] + ']'
                        color.pop()
                        output += color[-1]
            else: output += dbuf
        if len(cbuf) > 0: output += cbuf
        print output
        return output
                
    def tell(self,tok):
        who = tok[0].lower()
        txt = " ".join(tok[1:])
        tells = []
        told = 0
        for player in players:
            if player.nick.lower() == who or who in player.name.lower(): player.write("%s(%s%s tells you: %s))"%(ansi(COLOR['magneta']),ansi(COLOR['magneta']),self.name,txt));told=1
            elif player.nick.lower() == self.nick.lower(): pass
            elif player.gm: player.write("%s(%s%s tells %s: %s)"%(ansi(COLOR['yellow']),ansi(COLOR['yellow']),self.name,who,txt))

        if told: self.write("%s(%sYou tell %s: %s)"%(ansi(COLOR['magneta']),ansi(COLOR['magneta']),who,txt))
        else: self.write("%s(%sNobody here with that name)"%(ansi(COLOR['magneta']),ansi(COLOR['magneta'])))

    def game(self,data):
        if len(data) == 0: return
        data = data.decode('utf-8')
        tok = data.split(' ')
        if tok[0] == 'TYPING': self.typing = True;self.announce_players()
        elif tok[0] == 'NOT_TYPING': self.typing = False;self.announce_players()
        elif tok[0] == '/name': self.name = " ".join(tok[1:])
        elif tok[0] == '/gm': self.gm = (self.gm+1)%2;self.typing = False;self.announce_players()
        elif tok[0] == '/tell': self.tell(tok[1:])
        else: 
            if data[0] == '*': self.announce('''%s %s'''%(self.name,data[1:]))
            elif data[0] == '!': 
                #roll = self.dice(data)
                #if roll: self.announce('''(%s: %s)'''%(self.name,roll))
                #else: 
                self.announce('''(%s: %s)'''%(self.name,data))
            elif data[0] == '#': self.announce('''(%s) %s'''%(self.name,data[1:]))
            elif data[0] == '(': self.announce('''(%s: %s'''%(self.name,data[1:]))
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
        self.announce("D_PLAYERS %s"%(" ".join(pl)))
    def dice(self,data):
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
            text = """Sup bro. Please use a %stelnet/mud%s client that has back background. Using a command line is a good idea too."""%(ansi(COLOR['red']),ansi(COLOR['white']))
        self.text = text

if __name__ == '__main__':
    reactor.listenTCP(49500, ServeGameFactory())
    reactor.run()
