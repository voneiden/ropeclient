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
from Tkinter import Entry,N,S,E,W

class RopeModule:
    ''' This is the entry module, it takes user input
    '''
    def __init__(self,parent):
        self.parent   = parent
        self.depends  = []
        self.contents = StringVar()
        self.widget = Entry(self.parent.frame,
                             textvariable=self.contents,
                           background="black",foreground="white",
                             state=NORMAL, insertbackground="white")
        
        ''' If hide is set to true, entrybox will display stars instead of letters '''
        self.hide = False
        
        ''' If hash is set to true, entrybox will hash the contents it's going to send '''
        self.hash = False
        
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
    
    def scroll(self,event):
        pass
    
    def receiveMessage(self,data):
        tok = data.split()
        header = tok[0].lower()
        
        if   header == 'pwd':
            self.hide = (self.hide+1)%2
            if self.hide: self.widget.config(show='*')
            else:         self.widget.config(show='')