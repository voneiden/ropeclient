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
import sys
import traceback

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
            buf.append({"key": "msg", "value": line})
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
        if self.player:
            self.player.disconnect()

        return

        if self.player: self.player.disconnect()
        else:
            self.transport.loseConnection()
    
    def get_player_name(self):
        if self.player: #hasattr(self.player, "name"):
            try:
                return self.player.get("name")
            except:
                return "unknown-player"
        else:
            return "unknown-player"
        
    def onClose(self, clean, code, reason):
        logging.info("Connection lost: %s"%(self.get_player_name()))
        self.disconnect()
        
    def onMessage(self, data, isBinary):
        """ 
        Decode received data and forward it to the respective handler function
        """
        if isBinary:
            logging.warning("Received binary data from client, ignoring")
            return
        try:
            data = data.decode("utf8")
        except UnicodeDecodeError:
            logging.error("Unable to decode received data")
            return

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
        logging.info("Received message: " + str(content))
        # Forward the request to appropriate handler
        # Example: self.player.handler.process_msg
        if not content["key"].isalpha():
            logging.warning("Invalid process cmd ({}) received from player {}".format(content["key"], self.get_player_name()))
            return

        try:
            if self.player:
                f = getattr(self.player.handler, "process_{}".format(content["key"]))
            else:
                f = getattr(self.login_handler, "process_{}".format(content["key"]))
        except AttributeError:
            self.failure()
            return

        try:
            f(content)
        except:
            self.failure()
        
    def write(self, data):
        """
        Encodes the data (utf8) and passes it to the network framework for delivery

        @param data: data to be sent to client
        @type data: str
        @return: None
        """
        logging.info("WRITE: " + data)
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
            message = {"key": "msg", "value": message}

        try:
            if isinstance(message, list):  # Multi-line messages
                assert len(message) > 0

                for si, submessage in enumerate(message):
                    if isinstance(submessage, dict) and "value" in submessage:  # Sanitize
                        submessage["value"] = self.core.sanitize(submessage["value"])
                        if "key" not in submessage:
                            submessage["key"] = "msg"

                    elif isinstance(submessage, str):  # Convert str to dict & sanit.
                        message[si] = {"key": "msg", "value": self.core.sanitize(submessage)}
                    else:
                        logging.error("Error, unable to process submessages in list")
                        raise AssertionError
            else:
                assert isinstance(message, dict)
                if message["key"] == "msg" and "value" in message:
                    message["value"] = self.core.sanitize(message["value"])
        except:
            logging.error("sendMessage got invalid format: {}".format(str(message)))
            raise
            return
        
        if isinstance(message, list) and len(message) > 0:
            if "key" in message[0] and message[0]["key"] == "msg":
                self.write(json.dumps({"key": "msg_list", "value": message}))
            elif "key" in message[0] and message[0]["key"] == "oft":
                self.write(json.dumps({"key": "oft_list", "value": message}))
            else:
                logging.error("Unable to determine key type of list send: " + message[0]["key"])
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
        
    def failure(self):
        """
        failure prints detailed information about exceptions

        @return: None
        """
        # In the local var display, any item containing the following will be ignored
        # ignore = ["__", "class '", "module '"]

        # buf will be filled with the detailed stack trace
        buf = []

        # Grab traceback
        tb = sys.exc_info()[2]

        # Get the latest traceback
        while 1:
            if not tb.tb_next:
                break
            tb = tb.tb_next

        # Load up the stack
        stack = []
        tb_frame = tb.tb_frame
        while tb_frame:
            stack.append(tb_frame)
            tb_frame = tb_frame.f_back

        # Reverse the stack (from high level to low level)
        stack.reverse()

        logging.error("Exception has occured, printing stack trace")
        for i, frame in enumerate(stack):

            buf.append("Frame %s in %s at line %s" % (frame.f_code.co_name,
                                                 frame.f_code.co_filename,
                                                 frame.f_lineno))

            if i+1 == len(stack):
                for key, value in frame.f_locals.items():
                    try:
                        k = str(key)
                        v = str(value)
                        #skip = False
                        #for ig in ignore:
                        #    if ig in k or ig in v:
                        #        #skip = True
                        #        break
                        #if skip:
                        #    continue
                        #else:
                        buf.append("\t%20s = %s" %(key, value))
                    except:
                        buf.append("\t%20s = <ERROR WHILE PRINTING VALUE>"%key)

        stack_trace = "\n".join(buf)

        # Output to terminal
        print(stack_trace)
        traceback.print_exc()

        # Output to file
        log_id = str(int(time.time())) + "-" + self.get_player_name()

        f = open('failures/{log_id}.txt'.format(log_id=log_id), 'w')
        traceback.print_exc(file=f)
        f.write(stack_trace)
        traceback.print_exc(file=f)
        f.close()

        try:
            self.send_message_fail("<fail>[ERROR] Something you did caused an exception" +
                     " on the server. This is probably a bug. The problem" +
                     " has been logged with id {log_id}.".format(log_id=log_id)+
                     " You may help to solve the problem by filing an issue"+
                     " at www.github.com/voneiden/ropeclient - Please mention"+
                     " this log id and what you were writing/doing when the"+
                     " error happened. Thank you!")

        except:
            logging.error("Was unable to deliver the error message to the player")
            pass


if __name__ == '__main__':
    core = Core()
    #webnetwork = WebNetwork(core)

    factory = WebSocketServerFactory("ws://localhost:9091", debug=False)
    factory.protocol = WebPlayer
    factory.core = core

    loop = asyncio.get_event_loop()
    loop.set_debug(False)  # Note, current version of asyncio doesn't seem to respect this variable. Fixed base_events.py
    coro = loop.create_server(factory, 'localhost', 9091)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
