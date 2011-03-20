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




Ropeserver singelchannel core module
- - - - - - - - - - - - - - - - - - -
This module intends to provide the basic functionality for delivering messages
to clients. It uses the standard format of sending
msg owner timestamp/id datastring
'''

class RopeModule:
    def __init__(self,parent):
        self.parent = parent
        self.players = {}
        self.timestamps = []
        
    def enable(self):
        self.parent.addHook('sendMessage',self.sendMessage)
    
    def disable(self):
        pass
    
    def sendMessage(self,data):
        ''' The data has to be a list with 4 items:
            data[0] target player or list of players
            data[1] this is the data string
            data[2] optional owner
            data[3] optional timestamp
            '''
        if type(data) != list: self.display("Data not a list");return
        if len(data) < 2: self.display("List too short.");return
        player = data[0]
        text   = data[1]
        if len(data) > 2: owner = data[2]
        else: owner = "?"
        if len(data) > 3: msgid    = data[3]
        else: msgid = self.generateTimestamp()
        msg = "msg %s %i %s"%(owner,msgid,text)
        
        self.display("Dispatching message: %s"%text)
        if type(player) == list:
            for p in player:
                p.write(msg)
        else:
            player.write(msg)
    def display(self,data):
        self.parent.display("core_dispatcher: %s"%data)
        
        
    def generateTimestamp(self):
        ''' this function should generate a unique timestamp '''
        timestamp = time.time()
        while timestamp in self.timestamps:
            timestamp += 0.00001
        self.timestamps.append(timestamp)
        return timestamp
    '''
    def makeMessage(self,owner,content):
        timestamp = self.timestamp()
        content = self.messageWrap(content)
        self.messages[timestamp] = [owner,content]
        return timestamp
    '''