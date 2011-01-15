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
import ConfigParser, logging, time, re
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
        self.entry.focus_set()

        self.CONFIG = True
        self.typing = False
        '''
        self.textarea.tag_config("red", foreground="red")
        self.textarea.tag_config("white", foreground="white")
        self.textarea.tag_config("cyan", foreground="cyan")
        self.textarea.tag_config("gray", foreground="gray")
        self.textarea.tag_config("red", foreground="red")
        self.textarea.tag_config("dim gray", foreground="dim gray")
        self.textarea.tag_config("yellow", foreground="yellow")
        self.textarea.tag_config("green", foreground="green")
        self.textarea.tag_config("blue", foreground="blue")
        self.textarea.tag_config("magneta", foreground="magenta")
        '''
        #for line in testbuf: self.display_line(line)
        if not self.load_config(): 
            self.CONFIG = False

        self.colortags = []
        self.colorre   = re.compile('\033<.*?>')
        
        print "OK"
    
    def stop(self):
        
        self.root.destroy()
        reactor.stop()
    def returnfocus(self,args):
        self.entry.focus_set()
        
        
    def load_config(self):
        ''' This function loads the config.txt  '''
        parser = ConfigParser.SafeConfigParser()
        try: parser.readfp(open('config.txt','r'))
        except: self.display_line("Could not load config.txt");return False
        
        
        try:    nick  = parser.get('general','nick')
        except: self.display_line("Error in loading your config! nick is not defined in section [general]");return False
        try:    name = parser.get('general','name')
        except: self.display_line("Error in loading your config! name is not defined in section [general]");return False
        try:    host = parser.get('general','host')
        except: self.display_line("Error in loading your config! host is not defined in section [general]");return False

        try:    highlight = parser.get('colors','highlight')
        except: self.display_line("Error in loading your config! highlight is not defined in section [colors]");return False
        try:    talk = parser.get('colors','talk')
        except: self.display_line("Error in loading your config! talk is not defined in section [colors]");return False
        try:    action = parser.get('colors','action')
        except: self.display_line("Error in loading your config! action is not defined in section [colors]");return False
        try:    offtopic = parser.get('colors','offtopic')
        except: self.display_line("Error in loading your config! offtopic is not defined in section [colors]");return False
        try:    describe = parser.get('colors','describe')
        except: self.display_line("Error in loading your config! describe is not defined in section [colors]");return False
        try:    tell = parser.get('colors','tell')
        except: self.display_line("Error in loading your config! tell is not defined in section [colors]");return False
        



        self.nick = nick
        self.name = name
        self.root.title("Ropeclient: %s"%self.name)
        self.host = host
        self.colors = {
                       'talk':talk,
                       'action':action,
                       'offtopic':offtopic,
                       'describe':describe,
                       'tell':tell}
        self.highlight = highlight
        
        self.display_line("Your nick is: %s"%self.nick)
        return True
    
    
    def update_players(self,players):
        ''' Called when something changes in players '''
        self.listbox.delete(0, END)
        for player in players:
            self.listbox.insert(END, player)
    
    def display_line(self,text):
        text = self.wrap(text)

        plain = []
        for piece in text: plain.append(piece[1])
        logging.info("".join(plain))


        # Timestamp
        ts = ('grey',time.strftime('[%H:%M:%S] '))
        text.insert(0,ts)



        self.textarea.config(state=NORMAL)
        for piece in text:
            self.textarea.insert(END, piece[1],piece[0])
        self.textarea.insert(END,'\n')
        self.textarea.config(state=DISABLED)
        self.textarea.yview(END)

        
    def wrap(self,text):
        buf = []
        for i,piece in enumerate(text.split('\033<')):
            

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
        self.command.set("")
        tok = data.split(' ')
        if tok[0]== '/name': self.root.title("Ropeclient: %s"%" ".join(tok[1:]))
        try:
            self.connection.write(data)
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
            self.connection.write(u"\xff\x00")
            self.typing = False
            
    def keypress(self,args):
        ''' Check if we've sent typing signal to server and if not, send it '''
        if args.keycode < 20: return
        elif not self.typing and len(self.command.get()) > 0: 
            self.connection.write(u"\xff\x01")
            self.typing = True
            
    def loop(self):
        self.root.mainloop()

class Client(LineReceiver):
    def __init__(self,window):
        self.window = window
        #LineReceiver.__init__(self)

        
    def connectionMade(self):
        self.window.display_line("Connected!")
        self.write("SUPERHANDSHAKE")
        self.write("SETNAME %s"%self.window.name)
        self.write("SETCOLOR %s"%self.window.highlight)
        self.write("SETNICK %s"%self.window.nick)
        
    def lineReceived(self, data):
        #self.window.display_line("Line received!")
        data = data.decode('utf-8')
        #tok = data.split(' ')
        #print tok
        if data[0:2] == u'\xff\xa0':
            players = data[2:].split(' ')
            self.window.update_players(players)
        else: self.window.display_line(data)
    
    def connectionLost(self,reason):
        pass

    def write(self,data):
        data = data+'\r\n'
        data = data.encode('utf-8')
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

