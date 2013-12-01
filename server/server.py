#!/usr/bin/python3
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

    Copyright 2010-2013 Matti Eiden <snaipperi()gmail.com>
'''

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet import defer
#from twisted.python import log

from txws import WebSocketFactory
from collections import OrderedDict

import json
import logging
import os
import pickle
import player
import re
import sys
import time
import world

#log.startLogging(sys.stdout)

class Core(object):
    """ This class is the core object of the server. It links everything else together. """
    def __init__(self):    
        logger = logging.getLogger("")
        logger.handlers = []
        
        # Initialize logging
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s %(module)-10s:%(lineno)-3s %(levelname)-7s %(message)s',"%y%m%d-%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        logging.info("Logger configured")
		
        self.version = "0.f"
        self.greeting = open('motd.txt', 'r').readlines()
        self.worlds = [world.World("Official sandbox",None,['voneiden'])]
        self.accounts_load()
        self.worlds_load()
        self.players = []
        logging.info("Server ready")
        
    def __getstate__(self):
        return None
        
    def accounts_load(self):
        logging.info("Loading player accounts.")
        try:
            f = open('players.db', 'rb')
            self.players = pickle.load(f)
            f.close()
            if type(self.players) != list:
                logging.info("Invalid type loaded, clearing.")
                self.players = []
        except IOError:
            logging.info("IOError, clearing.")
            self.players = []
            
        for player in self.players:
            #TODO: Consider this
            if not hasattr(account,"colors"):
                logging.info("Fixing missing account color table")
                account.colors = {}
            if not hasattr(account,"font"):
                logging.info("Fixing missing font data")
                account.font = ("Monospace",8)
            if not hasattr(account,"hilights"):
                logging.info("Fixing missing hilights data")
                account.hilights = OrderedDict()
                
    def accounts_save(self):
        logging.info("Saving accounts")
        f = open('players.db','wb')
        cPickle.dump(self.players,f)
        f.close()
        
    def worlds_load(self):
        logging.info("Loading worlds")
        for path,subfolders,files in os.walk('./worlds'):
            for fname in files:
                if fname[-6:] == '.world':
                    logging.info("Loading world {}".format(fname))
                    f = open("{0}/{1}".format(path,fname),'rb')
                    world = pickle.load(f)
                    f.close()
                    world.setup(self)
                    
        
    def worlds_save(self):
        logging.info("CORE: Save the worlds from destruction!")
        for world in core.worlds:
            world.saveWorld()
    
    # TODO improve this function        
    def escape(self,text):
        text = text.replace('<','&lt;')
        text = text.replace('>','&gt;')
        text = text.replace('=','&#61;')
        return text

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
        pattern = re.compile(pattern,re.IGNORECASE)
        
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
        
    

class WebPlayer(Protocol):
    def connectionMade(self):
        #TODO: require version from weblclient too
        logging.info("Web connection made")
        self.core = self.factory.core
        self.player = player.Player(self, self.core)
        self.sendFont("Monospace")
        
        # Send MOTD
        buf = []
        for line in self.core.greeting:
            buf.append((0,0,line))
        self.player.sendMessage(buf)
        
        self.player.recv = self.player.recvMessage
        self.pingTimer = False
        self.pingTime = False
        self.doPing()
    
    def doPing(self,*args):
        self.pingTimer = False
        if self.pingTime != False: # This means last request was not replied
            logging.info("ping not replied, disconnecting")
            self.disconnect()
        else:
            self.pingTime = time.time()
            self.write(json.dumps({"cmd":"ping"}))
            self.pingTimer = reactor.callLater(10,self.doPing)
            
    def disconnect(self):
        #if self.pingTimer:
        #    self.pingTimer.cancel()
        #    self.pingTimer = False
        # TODO: ^ why is this commented out? 2013-11-30
        if self.player: self.player.disconnect()
        else:
            self.transport.loseConnection()
    
        
    def connectionLost(self,reason):
        player = self.player.name if self.player else "Unknown player"
        logging.info("Connection lost: %s"%(player))
        self.disconnect()
        
    def dataReceived(self,data):
        content = json.loads(data)
        
        if content["cmd"] == "ping":
            self.pingTime = False
            return
            
        d = defer.Deferred()
        d.addCallback(self.player.recv)
        d.addErrback(self.failure)
        d.callback(content)
        # ^TODO: update player.recv
        
    def write(self,data):
        # TODO: json
        data = self.colorConvert(data)
        #data = data.replace("\n",'<br>')

        self.transport.write(data.encode("utf-8"))
        
    def colorConvert(self,data):
        # Ensure that color is always reseted to default (</font>)
        # TODO: ^ is this implemented? 2013-11-30
        # This function finds color references like <red> in the text, 
        # And converts them into HTML
        stack = []
        fallback = "grey"
        regex = '\<.*?\>'
        color_table = {"fail": "red",
                       "ok": "green",
                       "default": "#aaaaff",
                       "offtopic": "#4554ff",
                       "notify": "orange",
                       "timestamp": "grey"}
        
        for match in re.finditer(regex,data):
            match = match.group()
            color = match[1:-1]
            
            # Sanitize user input!
            color = re.sub("[^^a-zA-Z0-9\#]+", color)
            
            # Check for custom color maps
            if self.player.account and color in self.player.account.colors:
                color = self.player.account.colors[color]
            elif color in color_table:
                color = color_table[color]
            
            # Handle color reset
            if color == 'reset':
                try:
                    stack.pop()
                    color = 0
                except:
                    color = '#aaaaff'
                    stack.append(color)
            else:
                stack.append(color)
                
            # Replace the actual data
            if color:
                data = data.replace(match,'<font color="%s">'%color,1)
            else:
                data = data.replace(match,'</font>',1)
        data = data + '</font>'*len(stack)
        return data
        
    def sendMessage(self,message):
        '''
        Message format
        msg timestamp editable content \x1b timestamp editable content \1b etc
        '''
        #Todo: maybe send timestamp and default colors to client too?
        #TODO: change message format into dictionary
        
        if isinstance(message,list):
            buf = []
            for part in message:
                buf.append(u"{timestamp}\x1f{editable}\x1f{content}".format(
                           timestamp=repr(part[0]),editable=part[1],content=part[2]))
            message = u"\x1b".join(buf)
        elif isinstance(message,tuple):
            message = u"{timestamp}\x1f{editable}\x1f{content}".format(
                       timestamp=repr(message[0]),editable=message[1],content=message[2])
        elif isinstance(message,unicode):
            message = u"{timestamp}\x1f{editable}\x1f{content}".format(
                       timestamp=0,editable=0,content=message)
        elif isinstance(message,str):
            message = u"{timestamp}\x1f{editable}\x1f{content}".format(
                       timestamp=0,editable=0,content=message)
        else:
            logging.info( type(message))
            logging.info(message)
            logging.info("******** UNABLE TO PROCESS ******"*50)
            return               
        self.write(u'msg {message}'.format(message=message))
        
    def sendColor(self,c1,c2):
        self.write(u"col {c1} {c2}".format(c1=c1,c2=c2))
    def sendFont(self,font,size=8):
        self.write(u"fnt {font} {size}".format(font=font,size=size))
        
    def sendOfftopic(self,message):
        '''
        Offtopic format:
        oft timestamp content \x1b timestamp content \x1b.. etc
        '''
        logging.info( "server.sendOfftopic {}".format(message))
        if isinstance(message,list):
            buf = []
            # Extract parts
            for part in message: 
                buf.append(u"{0} {1}".format(part[1],part[0]))
            
            # Construct message
            message = u"\x1b".join(buf)
            
        elif isinstance(message,tuple):
            content = message[0]
            timestamp = message[1]
            message = u"{0} {1}".format(timestamp,content)
            
        else:
            logging.info( "Got invalid offtopic data {}".format(message))
            return 
            
        logging.info( "-> Offtopic ->")
        self.write(u"oft {message}".format(message=message))
        
    def sendEdit(self,id,message):
        self.write(u"edi {timestamp} {message}".format(timestamp=repr(id),message=message))
        
    def failure(self,failure):
        ''' Failure handles any exceptions '''
        dtb = failure.getTraceback(detail='verbose')
        tb = failure.getTraceback(detail='brief')
        logging.info("!"*30)
        logging.info(failure.getErrorMessage())
        logging.info("?"*30)
        logging.info(tb)
        logging.info("!"*30)
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
        logging.info("Networking initialized")


class Account:
    def __init__(self,name,password):
        self.name = name
        self.password = password
        
        self.colors = {}
        self.hilights = OrderedDict()
        self.font = ("Monospace",8)


if __name__ == '__main__':
    core = Core()
    webnetwork = WebNetwork(core)
    reactor.listenTCP(9091, WebSocketFactory(webnetwork))
    
    
    
    reactor.run()
    
    core.saveWorlds()
    core.saveAccounts()
