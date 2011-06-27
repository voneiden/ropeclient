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


class Connection(LineReceiver):
    def __init__(self,window):
        self.window   = window

    def connectionMade(self):
        self.window.displayMain("Connected!")
        self.write("hsk 3.0.0")

    def lineReceived(self, data):
        data = data.decode('utf-8').strip()
        tok = data.split(' ')
        
        if tok[0] == 'msg':
            owner = tok[1]
            timestamp = tok[2]
            message = " ".join(tok[3:])
            self.window.displayMain(message)

    def write(self,data):
        data = data+'\r\n'
        data = data.encode('utf-8')
        print "Writing",data
        self.transport.write(data)

class connectionFactory(ReconnectingClientFactory):
    def __init__(self,window):
        self.window = window

    def startedConnecting(self, connector):
        self.window.displayMain("Connecting to server..")

    def buildProtocol(self, addr):
        print ('Connected.')
        print ('Resetting reconnection delay')

        self.resetDelay()
        connection = Connection(self.window)
        self.window.connection = connection
        return connection

    def clientConnectionLost(self, connector, reason):
        message = reason.getErrorMessage().split(':')[0]
        self.window.displayMain("Connection failed (%s)"%(message))
        self.window.connection = None
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        message = reason.getErrorMessage().split(':')[0]
        self.window.displayMain("Connection failed (%s)"%(message))
        self.window.connection = None
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
