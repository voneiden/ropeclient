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
from Tkinter import N,S,E,W,WORD,DISABLED,NORMAL, StringVar, END
from ScrolledText import ScrolledText
import time,re

class RopeModule:
    ''' This module defines the basic output textbox
    '''
    def __init__(self,parent):
        self.parent = parent

    def enable(self):
        self.parent.addHook('receiveMessage',self.receiveMessage)
    def disable(self):
        self.parent.delHook('receiveMessage',self.receiveMessage)
        
 
 
    def receiveMessage(self,data):
        tok = data.split(" ")
        header = tok[0].lower()
        
        if header == 'mod' and len(tok) > 2:
            status  = tok[1]
            module   = tok[2]
            if status == 'enable':
                if module in self.parent.mods:
                    self.parent.mods[module].enable()
                    print "enabled mod",module
                    self.sendModStatus("enabled",module)
                else:
                    x = self.parent.modLoad(module)
                    if x:
                        print "Loaded module",module
                        self.parent.mods[module].enable()
                        self.sendModStatus("enabled",module)
                    else:
                        print "Failed to load module",module
                        self.sendModStatus("disabled",module)
            else:
                if module in self.parent.mods:
                    self.parent.mods[module].disable()
                    self.sendModStatus("disabled",module)
                    print "Disabled module",module
        
        
    def sendModStatus(self,status,module):
        self.parent.connection.write("mod %s %s"%(status,module))
        