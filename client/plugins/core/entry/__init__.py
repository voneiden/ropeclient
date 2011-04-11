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
from Tkinter import Entry,N,S,E,W,StringVar,NORMAL

class Plugin:
    ''' This is the entry module, it takes user input
    '''
    def __init__(self,core):
        self.parent   = core
        self.depends  = []
        self.contents = StringVar()
        self.widget = Entry(self.parent.frame,
                             textvariable=self.contents,
                           background="black",foreground="white",
                             state=NORMAL, insertbackground="white")
        
        ''' If hide is set to true, entrybox will display stars instead of letters '''
        self.hide = False
        
        ''' Tracks the user typing status '''
        self.typing = False
        
    def enable(self):
        self.widget.grid(row=1,column=0,sticky=E+W)
        self.widget.bind(sequence="<KeyRelease>",  func=self.keypress)
        self.widget.bind("<MouseWheel>",    func=self.scroll)
        self.widget.bind("<Button-4>",      func=self.scroll)
        self.widget.bind("<Button-5>",      func=self.scroll)
        #self.widget.bind(sequence="<Up>",   func=self.browseHistory)
        #self.widget.bind(sequence="<Down>", func=self.browseHistory)
        self.widget.focus_set()
        
        self.parent.event.add('lineReceived',self.receiveMessage)
    def disable(self):
        self.listbox.grid_remove()
        self.parent.event.add('lineReceived',self.receiveMessage)
        
    def keypress(self,event):
        buffer = self.contents.get()
        if event.keysym == "BackSpace":
            buffer = buffer[:-1]
        elif event.keysym == "Return":
            if self.parent.connection:
                self.parent.connection.write("msg %s"%buffer)
                self.contents.set("")
                buffer=""
        
        else:
            buffer += event.char
            
        if len(buffer) == 0 and self.typing: 
            self.typing = False
            print "PNT" #Send PNT
        elif len(buffer) > 0 and not self.typing: 
            self.typing = True
            print "PIT" #Send PIT
    
        #print dir(event)
        #print event.keycode
        print event.keysym
        #print event.char
    
    def scroll(self,event):
        pass
    
    def receiveMessage(self,kwargs):
        tok = kwargs['tok']
        header = tok[0].lower()
        
        if   header == 'pwd':
            self.hide = (self.hide+1)%2
            if self.hide: self.widget.config(show='*')
            else:         self.widget.config(show='')
            msg = " ".join(tok[1:])
            self.parent.display(msg)
            
        if header == 'nck':
            pass
        