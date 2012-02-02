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

from txws import WebSocketFactory


import time
import os
import sys
import player
import world
import cPickle
import re


class Core(object):
    """ This class contains some core information.."""

    # I'm gonna improve the core to be a container for the
    # new multiworld thingy that I have on my mind.
    
    def __init__(self):
        self.version = "0.d.rc1"
        self.greeting = open('motd.txt', 'r').readlines()
        self.worlds = [world.World("Official sandbox",None,['voneiden'])]
        self.loadAccounts()
        self.loadWorlds()
        self.players = []
        
    def __getstate__(self):
        return None
        
    def loadAccounts(self):
        try:
            f = open('accounts.db', 'rb')
            self.accounts = cPickle.load(f)
            f.close()
            if type(self.accounts) != list:
                print "CORE: Accounts have invalid type, clearing"
                self.accounts = []
        except IOError:
            self.accounts = []
            
        for account in self.accounts:
            if not hasattr(account,"colors"):
                print "Fixing missing account color table"
                account.colors = {}
            if not hasattr(account,"font"):
                print "Fixing missing font data"
                account.font = ("Monospace",8)
    
    def saveAccounts(self):
        f = open('accounts.db','wb')
        cPickle.dump(self.accounts,f)
        f.close()
        
    def loadWorlds(self):
        for path,subfolders,files in os.walk('./worlds'):
            for fname in files:
                if fname[-6:] == '.world':
                    f = open("{0}/{1}".format(path,fname),'rb')
                    world = cPickle.load(f)
                    f.close()
                    world.setup(self)
                    
        
    def saveWorlds(self):
        print "CORE: Save the worlds from destruction!"
        for world in core.worlds:
            world.saveWorld()
    '''      
    def find(self,objID,objList):
        """ 
            Search objList for name or unique matching objID
        """
        try:
            unique = int(objID)
            
        except ValueError:
            obj = [obj for obj in objList if obj.name.lower() == objID.lower()]
            if not obj:
                return False
            else:
                return obj
        else:
            obj = [obj for obj in objList if obj.unique == unique]
            if not obj:
                return False
            else:
                return obj
        '''
    def find(self,source,pattern,instance):
        # source = player object
        # Pattern = pattern to be found
        # Instance = Type of instances to be searched
        
        # First case is testing for ID number.
        try:
            ref = int(pattern)
        except ValueError:
            ref = -1
        
        else:
            if isinstance(instance,world.Character):
                l = source.world.characters
            elif isinstance(instance,player.Player):
                l = source.world.Players
            try:
                return [l[ref]]
            except:
                return False
    
        # Second case is testing for local name match, applies only to characters
        pattern = re.compile(pattern+'$',re.IGNORECASE)
        
        if isinstance(instance,world.Character):
            l = source.character.location.characters
            
            match = [character for character in l if re.match(pattern,character.name)]
            if len(match) > 0:
                return match
                
        # Third case is testing for global name match, applies to rest
        if isinstance(instance,world.Character):
            l = source.world.characters
        elif isinstance(instance,player.Player):
          
            l = source.world.players
        else:
            l = []
        match = [object for object in l if re.match(pattern,object.name)]
        return match
        
            
        
class RopePlayer(LineReceiver):

    def connectionMade(self):
        self.core = self.factory.core
        self.player = player.Player(self, self.core)
        
        self.pingTimer = False
        self.pingTime = False
        self.doPing()
        
    def doPing(self,*args):
        self.pingTimer = False
        if self.pingTime != False: # This means last request was not replied
            print "ping not replied, disconnecting"
            self.disconnect()
        else:
            self.pingTime = time.time()
            self.write("png")
            self.pingTimer = reactor.callLater(10,self.doPing)
            print "Ping asked"

    def lineReceived(self, line):
        line = line.decode('utf-8')
        line = line.strip()
        if line == "png":
            
            print "Ping received, latency",time.time()-self.pingTime
            self.pingTime = False
            return
            
        print "Testing new defer!",line
        d = defer.Deferred()
        d.addCallback(self.player.recv)
        d.addErrback(self.failure)
        d.callback(line)
        #self.player.recv(line)

    def write(self, data, newline=True):
        data = self.colorConvert(data)
        if newline:
            data = ("%s\r\n" % data).encode('utf-8')
        self.transport.write(data)

    def colorConvert(self,data):
        # Ensure that color is always reseted to default (</font>)
        
        stack = []
        fallback = "gray"
        regex = '\<.*?\>'
        print "Pre-parse:",data
        for match in re.finditer(regex,data):
            match = match.group()
            color = match[1:-1]
            if self.player.account and color in self.player.account.colors:
                color = self.player.account.colors[color]
            elif color == 'fail':
                color = 'red'
            elif color == 'ok':
                color = 'green'
            elif color == 'default':
                color = '#aaaaff'
            elif color == 'offtopic':
                color = '#aaaaff'
            elif color == 'talk':
                color = '#8888ff'
            elif color == 'notify':
                color = 'orange'
            
            if color == 'reset':
                try:
                    color = stack.pop()
                    #recolor = stack[-1]
                    #color = 0
                except:
                    color = '#aaaaff'
                    stack.append(color)     
            else:
                stack.append(color)
                
            #if color:
            data = data.replace(match,"<%s>"%color,1)
            #else:
            #    data = data.replace(match,'</font>',1)
        #data = data + '</font>'*len(stack)
        print "Finished:",data
        return data

    def connectionLost(self, reason):
        print "Connection lost"
        self.disconnect()

    def sendMessage(self, message):
        self.write('msg %f %s' % (time.time(),message))

    def sendOfftopic(self,message,timestamp):
        if not timestamp: timestamp = time.time()
        self.write(u"oft {timestamp} <offtopic>{message}".format(timestamp=timestamp,message=message))
    
    def sendColor(self,c1,c2):
        self.write(u"col {c1} {c2}".format(c1=c1,c2=c2))
        
    def disconnect(self):
        if self.pingTimer:
            self.pingTimer.cancel()
            self.pingTimer = False
            
        if self.player: self.player.disconnect()
        else:
            self.transport.loseConnection()


    def failure(self,failure):
        ''' Failure handles any exceptions '''
        dtb = failure.getTraceback(detail='verbose')
        tb = failure.getTraceback(detail='brief')
        print "!"*30
        print failure.getErrorMessage()
        print "?"*30
        print tb
        print "!"*30
        logid = str(int(time.time())) + "-" + str(self.player.name)
        f=open('failures/{logid}.txt'.format(logid=logid),'w')
        f.write(dtb)
        f.close()
        
        self.sendMessage("<fail>[ERROR] Something you did caused an exception" +
                         " on the server. This is probably a bug. The problem" +
                         " has been logged with id {logid}.".format(logid=logid)+
                         " You may help to solve the problem by filing an issue"+
                         " at www.github.com/voneiden/ropeclient - Please mention"+
                         " this log id and what you were writing/doing when the"+
                         " error happened. Thank you!")
        

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

class WebPlayer(Protocol):
    def connectionMade(self):
        #TODO: require version from weblclient too
        print "Web connection made"
        self.core = self.factory.core
        self.player = player.Player(self, self.core)
        self.sendFont("Monospace")
        self.sendMessage("".join(self.core.greeting))
        self.player.recv = self.player.recvMessage
        self.pingTimer = False
        self.pingTime = False
        self.doPing()
    
    def doPing(self,*args):
        self.pingTimer = False
        if self.pingTime != False: # This means last request was not replied
            print "ping not replied, disconnecting"
            self.disconnect()
        else:
            self.pingTime = time.time()
            self.write("png")
            self.pingTimer = reactor.callLater(10,self.doPing)
            print "Ping asked"
            
    def disconnect(self):
        #if self.pingTimer:
        #    self.pingTimer.cancel()
        #    self.pingTimer = False
            
        if self.player: self.player.disconnect()
        else:
            self.transport.loseConnection()
    
        
    def connectionLost(self,reason):
        print "Web connection lost"
        self.disconnect()
        
    def dataReceived(self,data):
        data = data.decode("utf-8")
        data = data.strip()
        if data == "png":
            print "Ping received, latency",time.time()-self.pingTime
            self.pingTime = False
            return
            
        print "Web connection data recv:",data
        d = defer.Deferred()
        d.addCallback(self.player.recv)
        d.addErrback(self.failure)
        d.callback(data)
        
    def write(self,data):
        
        data = self.colorConvert(data)
        #data = data.replace("\n",'<br>')
        self.transport.write(data.encode("utf-8"))
        
    def colorConvert(self,data):
        # Ensure that color is always reseted to default (</font>)
        
        stack = []
        fallback = "gray"
        regex = '\<.*?\>'
        print "Pre-parse:",data
        for match in re.finditer(regex,data):
            match = match.group()
            color = match[1:-1]
            if self.player.account and color in self.player.account.colors:
                color = self.player.account.colors[color]
            elif color == 'fail':
                color = 'red'
            elif color == 'ok':
                color = 'green'
            elif color == 'default':
                color = '#aaaaff'
            elif color == 'talk':
                color = '#8888ff'
            elif color == 'notify':
                color = 'orange'
            if color == 'reset':
                try:
                    stack.pop()
                    #recolor = stack[-1]
                    color = 0
                except:
                    color = '#aaaaff'
                    stack.append(color)
                
                
            else:
                stack.append(color)
                
            if color:
                data = data.replace(match,'<font color="%s">'%color,1)
            else:
                data = data.replace(match,'</font>',1)
        data = data + '</font>'*len(stack)
        print "Finished:",data
        return data
        
    def sendMessage(self, message):
        self.write(u'msg %f %s' % (time.time(),message))
    def sendColor(self,c1,c2):
        self.write(u"col {c1} {c2}".format(c1=c1,c2=c2))
    def sendFont(self,font,size=8):
        self.write(u"fnt {font} {size}".format(font=font,size=size))
        
    def sendOfftopic(self,message,timestamp):
        if not timestamp: timestamp = time.time()
        self.write(u"oft {timestamp} {message}".format(timestamp=timestamp,message=message))
    def failure(self,failure):
        ''' Failure handles any exceptions '''
        dtb = failure.getTraceback(detail='verbose')
        tb = failure.getTraceback(detail='brief')
        print "!"*30
        print failure.getErrorMessage()
        print "?"*30
        print tb
        print "!"*30
        logid = str(int(time.time())) + "-" + str(self.player.name)
        f=open('failures/{logid}.txt'.format(logid=logid),'w')
        f.write(dtb)
        f.close()
        
        self.sendMessage("<fail>[ERROR] Something you did caused an exception" +
                         " on the server. This is probably a bug. The problem" +
                         " has been logged with id {logid}.".format(logid=logid)+
                         " You may help to solve the problem by filing an issue"+
                         " at www.github.com/voneiden/ropeclient - Please mention"+
                         " this log id and what you were writing/doing when the"+
                         " error happened. Thank you!")
class WebNetwork(Factory):
    def __init__(self,core):
        self.protocol = WebPlayer
        self.core = core
        
class RopeNetwork(Factory):

    def __init__(self, core):
        self.protocol = RopePlayer
        self.core = core

class TelnetNetwork(Factory):

    def __init__(self, core):
        self.protocol = TelnetPlayer
        self.core = core

class Account:
    def __init__(self,name,password,style):
        self.name = name
        self.password = password
        self.style = style
        
        self.colors = {}
        


if __name__ == '__main__':
    core = Core()
    webnetwork = WebNetwork(core)
    reactor.listenTCP(49500, RopeNetwork(core))
    reactor.listenTCP(10023, TelnetNetwork(core))
    reactor.listenTCP(9091, WebSocketFactory(webnetwork))
    
    
    
    reactor.run()
    
    core.saveWorlds()
    core.saveAccounts()
