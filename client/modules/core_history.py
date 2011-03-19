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
from Tkinter import Listbox,N,S,E,W

class RopeModule:
    ''' This is the history module, it allows users to browse entry history and 
    '''
    def __init__(self,parent):
        self.parent = parent
        self.command = StringVar()
        self.widget = Entry(self.frame,
                             textvariable=self.command,
                           background="black",foreground="white",
                             state=NORMAL, insertbackground="white")
        
        
    def enable(self):
        self.widget.grid(row=1,column=0,sticky=E+W)
        self.widget.bind(sequence="<Key>",  func=self.keypress)
        self.widget.bind("<MouseWheel>",    func=self.scroll)
        self.widget.bind("<Button-4>",      func=self.scroll)
        self.widget.bind("<Button-5>",      func=self.scroll)
        #self.widget.bind(sequence="<Up>",   func=self.browseHistory)
        #self.widget.bind(sequence="<Down>", func=self.browseHistory)
        self.widget.focus_set()
        self.parent.addHook('receiveMessage',self.receiveMessage)

    def disable(self):
        self.listbox.grid_remove()
        self.parent.delHook('receiveMessage',self.receiveMessage)

        
    def keypress(self,event):
        print event
        
    def receiveMessage(self,data):
        tok = data.split()
        header = tok[0].lower()
        
        if header == 'msg' and len(tok) > 3:
            pass
        
