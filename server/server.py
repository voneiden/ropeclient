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


import asyncio
from autobahn.asyncio.websocket import WebSocketServerProtocol
from autobahn.asyncio.websocket import WebSocketServerFactory

#from collections import OrderedDict

import json
import logging
import time

from handler import HandlerLogin
from core import Core


class WebPlayer(WebSocketServerProtocol):


    def __init__(self, *args, **kwargs):
        WebSocketServerProtocol.__init__(self, *args, **kwargs)
        self.core = None
        self.player = None
        self.login_handler = None

        self.ping_timer = False
        self.ping_time = False
        self.ping_timestamp = False


    def onOpen(self):
        logging.info("Web connection made")

        self.core = self.factory.core
        self.send_font("Monospace")

        self.login_handler = HandlerLogin(self)

        # Send MOTD
        buf = []
        for line in self.core.greeting:
            buf.append({"value": line})
        self.send_message(buf)

        #self.do_ping()
    
    def do_ping(self,*args):
        self.ping_timer = False
        if self.ping_time: # This means last request was not replied
            logging.info("ping not replied, disconnecting")
            self.disconnect()
        else:
            self.ping_timestamp = time.time()
            self.write(json.dumps({"key":"ping"}))
            self.ping_timer = reactor.callLater(10,self.do_ping)
            
    def disconnect(self):
        #if self.pingTimer:
        #    self.pingTimer.cancel()
        #    self.pingTimer = False
        # TODO: ^ why is this commented out? 2013-11-30
        return

        if self.player: self.player.disconnect()
        else:
            self.transport.loseConnection()
    
    def get_player_name(self):
        if self.player and hasattr(self.player, "name"):
            return self.player.name
        else:
            return "Unknown player"
        
    def onClose(self, clean, code, reason):
        logging.info("Connection lost: %s"%(self.get_player_name()))
        self.disconnect()
        
    def onMessage(self, data, isBinary):
        """ 
        Decode received data and forward it to the respective handler function
        """
        try:
            content = json.loads(data)
        except ValueError:
            logging.error("Invalid data received from {} (data: {})".format(self.get_player_name(), data))
        
        if "key" not in content:
            logging.error("Invalid content received from {} (content: {})".format(self.get_player_name(), content))
            return
            
        if not content["key"].isalpha():
            logging.error("Invalid content key received from {} (content: {})".format(self.get_player_name(), content))
        
        if content["key"] == "pong":
            self.ping_time = False
            return

        # Forward the request to appropriate handler
        # Example: self.player.handler.process_msg
        if self.player:
            f = getattr(self.player.handler, "process_{}".format(content["key"]))
        else:
            f = getattr(self.login_handler, "process_{}".format(content["key"]))
        
        d = defer.Deferred()
        d.addCallback(f)
        d.addErrback(self.failure)
        d.callback(content)
        
    def write(self,data):
        # TODO: json
        
        #data = data.replace("\n",'<br>')

        self.sendMessage(data.encode("utf-8"))

    def send_message(self, message):
        """
        message may be either a dictionary or a list of dictionaries
        a dictionary must contain "value" key which is the body of the text
        it may also contain: 
            - timestamp  - if defined, the client will display a timestamp
            - edit       - if true, the user can edit the line
        """
        # Convert string/unicode based messages into correct dict format
        if isinstance(message, str):
            message = {"key":"msg", "value":message}

        try:
            if isinstance(message, list):  # Multi-line messages
                for si, submessage in enumerate(message):
                    if isinstance(submessage, dict) and "value" in submessage:  # Sanitize
                        submessage["value"] = self.core.sanitize(submessage["value"])
                    elif isinstance(submessage, str) or isinstance(submessage, unicode):  # Convert str to dict & sanit.
                        message[si] = {"key": "msg", "value": self.core.sanitize(submessage)}
                    else:
                        logging.error("Error, unable to process submessages in list")
                        raise AssertionError
            else:
                assert isinstance(message, dict) and "value" in message
                message["value"] = self.core.sanitize(message["value"])
        except:
            logging.error("sendMessage got invalid format: {}".format(str(message)))
            raise
            return
        
        if isinstance(message, list):
            self.write(json.dumps({"key":"msg_list", "value":message}))
        else:
            self.write(json.dumps(message))

    def send_message_fail(self, message):
        if isinstance(message, str):
            message = {"key":"msg", "value":message}
        else:
            assert isinstance(message, dict)
            assert "value" in message

        message["value"] = "<fail>" + message["value"]
        self.send_message(message)

    def send_password(self):
        self.write(json.dumps({"key":"pwd"}))
            
    def sendColor(self,c1,c2):
        self.write(u"col {c1} {c2}".format(c1=c1,c2=c2))
        
    def send_font(self,font,size=12):
        self.write(json.dumps({"key":"font", "font": font, "size": size}))
        
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
        #dtb = failure.getTraceback(detail='verbose')
        tb = failure.getTraceback(detail='brief')
        logging.info("!"*30)
        logging.info(failure.getErrorMessage())
        logging.info("?"*30)
        logging.info(tb)
        logging.info("!"*30)
        if hasattr(self.player, "name"):
            log_id = str(int(time.time())) + "-" + str(self.player.name)
        else:
            log_id = str(int(time.time())) + "-" + "unnamed"
        f=open('failures/{log_id}.txt'.format(log_id=log_id),'w')
        #f.write(dtb)
        failure.printDetailedTraceback(file=f)
        f.close()
        
        self.player.send_message("<fail>[ERROR] Something you did caused an exception" +
                         " on the server. This is probably a bug. The problem" +
                         " has been logged with id {log_id}.".format(log_id=log_id)+
                         " You may help to solve the problem by filing an issue"+
                         " at www.github.com/voneiden/ropeclient - Please mention"+
                         " this log id and what you were writing/doing when the"+
                         " error happened. Thank you!")


if __name__ == '__main__':
    core = Core()
    #webnetwork = WebNetwork(core)

    factory = WebSocketServerFactory("ws://localhost:9091", debug = False)
    factory.protocol = WebPlayer
    factory.core = core

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, 'localhost', 9091)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
