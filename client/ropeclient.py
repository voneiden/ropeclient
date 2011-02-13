#!/usr/bin/python
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

from Tkinter import *
from ScrolledText import ScrolledText
import ConfigParser, logging, time, re, hashlib
from twisted.internet import tksupport, reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ReconnectingClientFactory

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='ropeclient.log')


class Window:
    def __init__(self):
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.title('Ropeclient')
        self.mainframe = Frame(self.root,background="black")
        self.mainframe.pack(fill=BOTH,expand=YES)
        self.mainframe2 = Frame(self.root)
        self.mainframe2.pack(fill=BOTH,expand=NO)

        self.textarea = ScrolledText(self.mainframe,width=80,height=20,
                                     wrap=WORD,
                                     state=DISABLED, background="black",foreground="white")
        self.textarea.pack(side=LEFT,fill=BOTH, expand = YES)
        self.textarea.bind(sequence="<FocusIn>", func=self.returnfocus)
        
        self.listbox = Listbox(self.mainframe,width=12,background="black",foreground="white")
        self.listbox.pack(side=LEFT,fill=BOTH,expand=NO)
        self.command = StringVar()
        self.entry = Entry(self.mainframe2,
                             textvariable=self.command,
                           background="black",foreground="white",
                             state=NORMAL, insertbackground="white")
        self.entry.pack(side=BOTTOM,anchor="w",fill=X, expand = NO)
        self.entry.bind(sequence="<Return>", func=self.process)
        self.entry.bind(sequence="<BackSpace>",func=self.backspace)
        self.entry.bind(sequence="<Key>", func=self.keypress)
        self.entry.bind("<MouseWheel>", self.mouse_wheel)
        self.entry.bind("<Button-4>",   self.mouse_wheel)
        self.entry.bind("<Button-5>",   self.mouse_wheel)
        self.entry.bind(sequence="<Up>", func=self.browseHistory)
        self.entry.bind(sequence="<Down>", func=self.browseHistory)
        self.entry.focus_set()

        self.CONFIG = True
        self.typing = False
 
        if not self.load_config(): 
            self.CONFIG = False

        self.colortags = []
        self.regexColor = re.compile('(?<=<).*?(?=>)')
        self.regexColorF= re.compile('<.*?>')
        
        self.playerlist = []
        
        self.password = False

        self.setTitle()
        
        self.lHistory = []
        self.cHistory = ''
        #for i in xrange(10): self.lHistory.append('')
        self.iHistory = 0
    
    def stop(self):
        self.root.destroy()
        reactor.stop()
        sys.exit(1)
    
    
    def addHistory(self,line):
        print "addHistory"
        self.lHistory.append(line)
        if len(self.lHistory) > 10: self.lHistory.pop(0)
        
    
    def browseHistory(self,event):
        print "keyupdown!!",event,event.keycode,event.char
        if self.iHistory == 0: 
            self.cHistory = self.command.get()
        if event.keycode == 38 or event.keycode == 111: 
            self.iHistory += 1
            self.iHistory %= 10
        elif event.keycode == 40 or event.keycode == 116:
            self.iHistory -= 1
            self.iHistory %= 10
        if self.iHistory > len(self.lHistory): self.iHistory = len(self.lHistory)
        print "iHistory",self.iHistory
        if self.iHistory == 0: self.command.set(self.cHistory)
        else:
            self.command.set(self.lHistory[-self.iHistory][1])
        
    def returnfocus(self,args):
        self.entry.focus_set()
        
    def mouse_wheel(self,event):
        print "Event num",event.num
        print "Event delta",event.delta
        if event.num == 5 or event.delta < 0:
            self.textarea.yview_scroll(event.delta,"pixels")
        elif event.num == 4 or event.delta > 0:
            self.textarea.yview_scroll(event.delta,"pixels")
        
    def load_config(self):
        ''' This function loads the config.txt  '''
        print "Loading config"
        parser = ConfigParser.SafeConfigParser()
        try: parser.readfp(open('config.txt','r'))
        except: self.display_line("Could not load config.txt");return False
        
        self.vars = {}
        config = {'general':['nick','host','default-action'],
                  'colors':['highlight','talk','action','offtopic','describe','tell']}
        for block,values in config.items():
            for option in values:
                try:
                    value = parser.get(block,option)
                    self.vars[option] = value
                except: self.display_line("config.txt error! Setting for block [%s] option %s is missing"%(block,option));return False
    
        self.nick = self.vars['nick']
        self.id   = self.nick.lower()
        self.host = self.vars['host']
        self.colors = {
                       'talk':self.vars['talk'],
                       'action':self.vars['action'],
                       'offtopic':self.vars['offtopic'],
                       'describe':self.vars['describe'],
                       'tell':self.vars['tell'],
                       'highlight':self.vars['highlight']}
        
        self.display_line("Your nick is: %s"%self.nick)
        self.display_line("Connecting to: %s"%self.host)
        return True
    
    def setTitle(self):
        pass
    
    def update_players(self):
        ''' Called when something changes in players '''
        self.listbox.delete(0, END)
        for player in self.playerlist:
            if player[1]: self.listbox.insert(END, "*%s"%player[0])
            else:         self.listbox.insert(END, "%s"%player[0])
            
    def playerTyping(self,id,status):
        for player in self.playerlist:
            if id in player[0]: player[1] = status
        self.update_players()
    
    def display_line(self,text,timestamp=None,owner=None):
        if not timestamp: timestamp = time.time()
        if self.textarea.yview()[1] == 1.0: scroll = True
        else: scroll = False
        if owner:
            tag   = timestamp
            self.textarea.tag_config(tag)
        
        self.textarea.config(state=NORMAL)
        asciitime = time.strftime('[%H:%M:%S]', time.localtime(float(timestamp)))
        #if owner: self.textarea.mark_set(start, END);self.textarea.mark_gravity(start,LEFT
        text = self.wrap(text)
        ts = ('grey',"%s "%(asciitime))
        text.insert(0,ts)
        if owner:
            print "TAGA",tag
            for piece in text:
                self.textarea.insert(END, piece[1],(piece[0],tag))
        else:
            for piece in text:
                self.textarea.insert(END, piece[1],piece[0])
        #if owner: self.textarea.mark_set(end, END);self.textarea.mark_gravity(end,LEFT)
        self.textarea.insert(END,'\n')
 
        
        
        print self.textarea.yview()
        if scroll: self.textarea.yview(END)
        '''
        if owner:
            print "Checking tag.."
            a,b= self.textarea.tag_ranges(tag)
            print dir(a)
            self.textarea.delete(a,b)
        '''  
        self.textarea.config(state=DISABLED)

    def edit_line(self,text,timestamp):
        print "Got edit",text #Edit needs to check if the mark exists!
        tag = "%s"%timestamp
        print "TAGE",tag
        self.textarea.config(state=NORMAL)
        asciitime = time.strftime('[%H:%M:%S]*', time.localtime(float(timestamp)))
        a,b= self.textarea.tag_ranges(tag) #<- this will fail TODO TODO TODOValueError
        self.textarea.delete(a,b)
        text = self.wrap(text)
        ts = ('grey',"%s "%(asciitime))
        text.insert(0,ts)
        text.reverse()
        for piece in text:
            self.textarea.insert(a, piece[1],(piece[0],tag))
        #text = self.wrap(text)
        #ts = ('grey',"%s "%(asciitime))
        #text.insert(0,ts)
        #for piece in text:
        #    self.textarea.insert(END, piece[1],piece[0])
        #self.textarea.insert(END,'\n')
        
 
        
        self.textarea.config(state=DISABLED)
        
    def wrap(self,text):
        buf = []
        for i,piece in enumerate(text.split('<')):
            if i == 0: buf.append(('white',piece));continue
            tok = piece.split('>')
            color = tok[0].lower()
            text  = ">".join(tok[1:])
        
            if color in self.colors: # Personalized colors
                color = self.colors[color]
                
            if color not in self.colortags:
                try: self.textarea.tag_config(color, foreground=color)
                except: self.textarea.tag_config(color,foreground="white")
            buf.append((color,text))
        return buf
    
    def process(self,args):
        self.typing = False
        data=unicode(self.command.get())
        if len(data) == 0: return
        self.command.set("")
        tok = data.split(' ')
        #if tok[0]== '/name': self.root.title("Ropeclient: %s"%" ".join(tok[1:]))
        try:
            if self.password:
                self.password = False
                self.entry.config(show='')
                data = "pwd %s"%(hashlib.sha256(data+'saltyropeclient').hexdigest())
                self.connection.write(data)
                
            elif self.iHistory and self.lHistory[-self.iHistory][0]: 
                print "EDI"
                self.connection.write(u"edi %s %s"%(self.lHistory[-self.iHistory][0],data))
                self.lHistory[-self.iHistory][1] = data
                self.iHistory = 0
            else:
                self.iHistory = 0
                self.addHistory([0,data])

                self.connection.write(u"msg %s"%(data))

        except:
            self.display_line("!!!!Something went wrong. I might crash!!!")
            print ("ERRORROREORE")
            raise

    def backspace(self,args):
        ''' This function captures the backspace and if there's
            only one character left in input it means the player
            removed everything, so send a not typing signal to server '''
        l = len(self.command.get())
        if l == 1 and self.typing:
            self.connection.write("pnt")
            self.typing = False
            
    def keypress(self,args):
        ''' Check if we've sent typing signal to server and if not, send it '''
        if args.keycode < 20: return
        elif not self.typing and len(self.command.get()) > 0: 
            self.connection.write("pit")
            self.typing = True
            
    def loop(self):
        self.root.mainloop()

class Client(LineReceiver):
    def __init__(self,window):
        self.window   = window
        #LineReceiver.__init__(self)

        
    def connectionMade(self):
        self.window.display_line("Connected!")
        self.write("hsk SUPERHANDSHAKE 3")
        self.write("nck %s"%(self.window.nick))
        self.write("dfa %s"%(self.window.vars['default-action']))
        self.write("clr highlight %s"%(self.window.colors['highlight']))
        
        
    def lineReceived(self, data):
        data = data.decode('utf-8')
        #print "lineReceived",data
        if len(data) < 2: return
        tok = data.split(' ')
        hdr = tok[0]
        
        # Playerlist packet
        if hdr == 'lop' and len(tok) > 1:
            players = tok[1:]
            self.window.playerlist = []
            for player in players:
                self.window.playerlist.append([player,False,False])
            self.window.update_players()
        
        # Typing packet
        elif hdr == 'pit' and len(tok) > 1:
            self.window.playerTyping(tok[1],True)
        
        # Not typing packet
        elif hdr == 'pnt':
            self.window.playerTyping(tok[1],False)
            
        # Password request packet
        elif hdr == u'pwd' and len(tok) > 1:
            self.window.password = True
            self.window.entry.config(show='*')
            self.window.display_line(" ".join(tok[1:]))
        
        # Color packet
        elif hdr == 'clr' and len(tok) > 2:
            self.window.colors[tok[1]] = tok[2]
            
        # Message packet
        elif hdr == 'msg' and len(tok) > 3:
            messageOwner  = tok[1]
            messageTime   = tok[2]
            messageContent= " ".join(tok[3:])
            #print "Msg",messageContent
            if messageOwner == "Server": self.window.display_line("[Server] %s"%(messageContent),messageTime)
            else: 
                if messageOwner == self.window.id: self.window.lHistory[-1] = [messageTime,messageContent]
                self.window.display_line("%s"%(messageContent),messageTime,messageOwner)
        
        elif hdr == 'edi' and len(tok) > 2:
            timestamp = tok[1]
            content   = " ".join(tok[2:])
            self.window.edit_line(content,timestamp)
        
        else:
            self.window.display_line("Corrupted packet %s"%data)
    
    def connectionLost(self,reason):
        pass

    def write(self,data):
        data = data+'\r\n'
        data = data.encode('utf-8')
        print "Writing",data
        self.transport.write(data)
        
class CFactory(ReconnectingClientFactory):
    def __init__(self,window):
        self.window = window
        #ReconnectingClientFactory.__init__(self)
        
    def startedConnecting(self, connector):
        print ('Started to connect.')

    def buildProtocol(self, addr):
        print ('Connected.')
        print ('Resetting reconnection delay')
        
        self.resetDelay()
        client = Client(self.window)
        self.window.connection = client
        return client

    def clientConnectionLost(self, connector, reason):
        self.window.display_line(' Lost connection. Reason:' + str(reason))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        self.window.display_line( 'Connection failed. Reason:' + str(reason))
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)


if __name__ == '__main__':
    print ("Loading..")
    window = Window()
    
    window.display_line("Installing tksupport")
    tksupport.install(window.root)
    if window.CONFIG:
        window.display_line("Connecting to server..")
        reactor.connectTCP(window.host, 49500, CFactory(window))
    else: window.display_line("Fix your config before you can continue connecting.")
    try: reactor.run()
    except:
        print( "ERROR ERROR ERROR")

