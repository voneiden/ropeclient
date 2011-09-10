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
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ReconnectingClientFactory
import sha, time
import window
class Connection(LineReceiver):

    def __init__(self, window):
        self.window = window
        
    def connectionMade(self):
        self.window.display("Connected!")
        self.write("hsk 0.c.a")

    def lineReceived(self, data):
        data = data.decode('utf-8').strip()
        tok = data.split(' ')

        if tok[0] == 'msg':
            timestamp = float(tok[1])
            message = " ".join(tok[2:])
            self.window.display(message,timestamp)
        
        #elif tok[0] == 'oft':
        #    timestamp = float(tok[1])
        #    
        #    message   = "[%s] %s"%(time.strftime("%H:%M",time.localtime(timestamp))," ".join(tok[2:]))
        #    self.window.display(message,timestamp)
           
        elif tok[0] == 'pwd':
            self.window.entryboxHide = True
            self.window.entrybox.config(show='*')
        
        elif tok[0] == 'plu': 
            # Player list update
            lop = " ".join(tok[1:]).split(';')
            playerlist = {}
            for player in lop:
                ptok = player.split(':')
                playerlist[ptok[0]] = ptok[1:]
                
            self.window.playerlist = playerlist
            self.window.playerboxUpdate()
            
        elif tok[0] == 'ptu':
            ptu = " ".join(tok[1:]).split(':')
            self.window.playerlist[ptu[0]] = ptu[1:]
            self.window.playerboxUpdate()
            
        elif tok[0] == 'clk':
            print "Received clk"
            ptok = " ".join(tok[1:]).split(';')
            tag = ptok[0]
            color = ptok[1]
            command = ptok[2]
            text = ptok[3]
            print tag,color,command,text
            self.window.textboxMain.tag_config(tag,foreground=color)
            self.window.textboxMain.tag_bind(tag,"<Button-1>",lambda(event): self.window.entryboxSet(command))
            self.window.display(text,(tag,))
            print "Displayed"
           
        elif tok[0] == 'clr':
            if tok[1] == 'main':
                self.window.textboxMain.config(state=window.NORMAL)
                self.window.textboxMain.delete(1.0, window.END)
                self.window.textboxMain.config(state=window.DISABLED)
                
                self.window.offtopicMain.config(state=window.NORMAL)
                self.window.offtopicMain.delete(1.0,window.END)
                self.window.offtopicMain.config(state=window.DISABLED)
            else:
                print "Unknown tok",tok
        else: 
            print "Unknown packet",tok
    def write(self, data):
        data = data + '\r\n'
        data = data.encode('utf-8')
        print "Writing", data
        self.transport.write(data)

    def connectionLost(self,reason):
        self.window.playerbox.delete(0, window.END)
class connectionFactory(ReconnectingClientFactory):

    def __init__(self, window):
        self.window = window

    def startedConnecting(self, connector):
        self.window.display("Connecting to server..")

    def buildProtocol(self, addr):
        print ('Connected.')
        print ('Resetting reconnection delay')

        self.resetDelay()
        connection = Connection(self.window)
        self.window.connection = connection
        return connection

    def clientConnectionLost(self, connector, reason):
        message = reason.getErrorMessage().split(':')[0]
        self.window.display("Connection failed (%s)" % (message))
        self.window.connection = None
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        message = reason.getErrorMessage().split(':')[0]
        self.window.display("Connection failed (%s)" % (message))
        self.window.connection = None
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
