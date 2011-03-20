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
This module intends to provide the basic functionality for 
single channel chatting.
'''
import time

class RopeModule:
    def __init__(self,parent):
        self.parent = parent
        self.players = {}
        
        
    def enable(self):
        self.parent.addHook('receiveMessage',self.receiveMessage)
    
    def disable(self):
        pass
    
    def receiveMessage(self,data):
        ''' The server receiveMessage should be type list, and contains
            the sender player and data string '''
        if type(data) != list: self.display("Received data not a list");return
        player = data[0]
        text   = data[1]
        tok    = text.split(' ')
        header = tok[0].lower()
    
        if header == "hsk" and len(tok) > 2:
            if tok[2] == "3": 
                self.parent.callHook("requireModule",[player,"enable","core_output.py"])
                self.parent.callHook("requireModule",[player,"enable","core_entry.py"])
                self.parent.callHook("requireModule",[player,"enable","core_playerbox.py"])
                
                self.msgPlayer(player,"Welcome to Ropeclient")
            else: self.parent.callHook('sendMessage',[player,"Your version is invalid."])
        elif header == "msg" and len(tok) > 2:
            text = " ".join(tok[1:])
            
        else:
            self.display("Received unknown packet")
            
    def display(self,data):
        self.parent.display("core_singlechannel: %s"%data)
        
    def msgPlayer(self,player,text):
        self.parent.callHook('sendMessage',[player,text])
        
        