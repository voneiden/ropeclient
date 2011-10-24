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


    Copyright 2010-2011 Matti Eiden <snaipperi()gmail.com>

    This is now the 3rd complete -from scratch- version of the server.
    The original version was functional, but featured rather hacky code
    and was not really expandable. The second version was designed towards
    a plugin based approach, however it turned out to be rather painful
    to develop as utilizing object-oriented code became increasingly difficult.
    Now I'm after a 3rd version, this time sacrificing the plugin support
    for fast development but with a clean logic. Hopefully this turns out well.

    == Few words on the rope protocol ==

    The protocol between the client and server is pretty straightforward
    The packet starts with a 3-letter command. The most crucial ones are
    msg and pwd. The server to client msg packet looks like this

    msg timestamp owner payload

    And the client to server msg packet looks simply like this
    msg payload

    This time around I plan on implementing also standard telnet protocol.



'''

# Note to self
# 'message' should be better defined..

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.protocols.telnet import Telnet
from twisted.internet import defer


import time
import os
import sys
import player
import world
import cPickle

class Core(object):
    """ This class contains some core information.."""

    # I'm gonna improve the core to be a container for the
    # new multiworld thingy that I have on my mind.
    
    def __init__(self):
        self.version = "0.d.alpha"
        self.greeting = open('motd.txt', 'r').readlines()
        self.worlds = []
        self.loadAccounts()
        self.loadWorlds()
        
    def __getstate__(self):
        return None
        
    def loadAccounts(self):
        try:
            f = open('accounts.db', 'rb')
            self.accounts = cPickle.load(f)
            f.close()
            if type(self.accounts) != dict:
                print "Accounts have invalid type, clearing"
                self.accounts = {}
        except IOError:
            self.accounts = {}
    
    def saveAccounts(self):
        f = open('accounts.db','wb')
        cPickle.dump(self.accounts,f)
        f.close()
        
    def loadWorlds(self):
        pass #To be implemented
        
    def saveWorlds(self):
        pass #To be 

class RopePlayer(LineReceiver):

    def connectionMade(self):
        self.core = self.factory.core
        self.player = player.Player(self, self.core)
        self.sendMessage("".join(self.core.greeting))

    def lineReceived(self, line):
        line = line.decode('utf-8')
        line = line.strip()
        print "Testing new defer!"
        d = defer.Deferred()
        d.addCallback(self.player.recv)
        d.callback(line)
        #self.player.recv(line)

    def write(self, data, newline=True):
        if newline:
            data = ("%s\r\n" % data).encode('utf-8')
        self.transport.write(data)

    def connectionLost(self, reason):
        print "Connection lost"
        self.player.disconnect()

    def sendMessage(self, message):
        self.write('msg %f %s' % (time.time(),message))

    def disconnect(self):
        self.transport.loseConnection()


class TelnetPlayer(Telnet):

    def connectionMade(self):
        self.core = self.factory.core
        self.player = player.Player(self, self.core)
        for line in self.core.greeting:
            self.sendMessage(line)

    def telnet_User(self, recv):
        self.player.recv(recv)

    def sendMessage(self, message):
        payload = message + '\r\n'
        self.write(payload)


class RopeNetwork(Factory):

    def __init__(self, core):
        self.protocol = RopePlayer
        self.core = core

class TelnetNetwork(Factory):

    def __init__(self, core):
        self.protocol = TelnetPlayer
        self.core = core

class Account:
    def __init__(self,name,password):
        self.name = name
        self.password = password
        self.style = 0

if __name__ == '__main__':
    core = Core()
    reactor.listenTCP(49500, RopeNetwork(core))
    reactor.listenTCP(10023, TelnetNetwork(core))
    reactor.run()
