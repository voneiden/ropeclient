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

# TODO
# plugins.core.dispatcher

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver



class Core:
    def __init__(self):
        self.version = "2.0.alpha-1"
        self.event = Event()
        #self.plugins = {}
        
        ''' Import here the plugin packages you want to use '''
        self.plugins = {}
        import plugins.core.dispatcher
        import plugins.core.login
        import plugins.core.chatroom
        import plugins.core.dicer
        import plugins.harnmud
        
        self.plugins['plugins.core.dispatcher'] = plugins.core.dispatcher.Plugin(self),
        self.plugins['plugins.core.login'] = plugins.core.login.Plugin(self),
        self.plugins['plugins.core.chatroom'] = plugins.core.chatroom.Plugin(self),
        self.plugins['plugins.core.dicer'] = plugins.core.dicer.Plugin(self),
        self.plugins['plugins.harnmud'] = plugins.harnmud.Plugin(self)
        
        
        
        
class Event:
    def __init__(self):
        self.events = {}
        self.db     = {}
        
    def add(self,name,func):
        if name not in self.events: self.events[name] = []
        self.events[name].append(func)
        return True
    
    def rem(self,name,func):
        if name not in self.events: return False
        if func not in self.events[name]: return False
        self.events[name].remove(func)
        return True
    
    def call(self,name,kwargs):
        if name not in self.events: return False
        results = []
        for event in self.events[name][:]: #Fixed a possible bug with list being modified on the fly?
            print "event.call:",name,len(self.events[name])
            results.append(event(kwargs))
            
        # HACK: Should the server be able to return multiple event values?
        if len(results) == 1: return results[0]
            
        
class Player(LineReceiver):
    def connectionMade(self):
        self.core = self.factory.core
        self.event = Event()
        self.core.event.call("connectionMade",{'player':self})
    def lineReceived(self,line):
        line = line.decode('utf-8')
        line = line.strip()
        self.event.call("lineReceived",{'player':self,'line':line})
    

    #def message(self,
    def write(self,data,newline=True):
        if newline: data = ("%s\r\n"%data).encode('utf-8')
        self.transport.write(data)
    def connectionLost(self,reason):
        self.core.event.call('connectionLost',{'player':self})
        
        
    def disconnect(self): self.transport.loseConnection()
class Network(Factory):
    def __init__(self,core):
        self.protocol = Player
        self.core    = core
        
if __name__ == '__main__':
    core = Core()
    reactor.listenTCP(49500, Network(core))
    reactor.run()