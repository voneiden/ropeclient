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
        self.write("hsk 2.0.alpha-1")

    def lineReceived(self, data):
        data = data.decode('utf-8').strip()
        tok = data.split(' ')

        self.window.displayMain(data)

    def write(self,data):
        data = data+'\r\n'
        data = data.encode('utf-8')
        print "Writing",data
        self.transport.write(data)

class connectionFactory(ReconnectingClientFactory):
    def __init__(self,window):
        self.window = window

    def startedConnecting(self, connector):
        print ('Started to connect.')

    def buildProtocol(self, addr):
        print ('Connected.')
        print ('Resetting reconnection delay')

        self.resetDelay()
        connection = Connection(self.window)
        self.window.connection = connection
        return connection

    def clientConnectionLost(self, connector, reason):
        print(' Lost connection. Reason:' + str(reason.getErrorMessage()))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print dir(reason)
        print( 'Connection failed. Reason:' + str(reason.getErrorMessage()))
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
