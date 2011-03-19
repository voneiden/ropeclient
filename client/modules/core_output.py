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

class RopeModule:
    ''' This module defines the basic output textbox
    '''
    def __init__(self,parent):
        self.parent = parent
        self.widget = ScrolledText(self.parent.frame,width=80,height=20,
                                     wrap=WORD,
                                     state=DISABLED, background="black",foreground="white")
        self.widget.yview(END)
    def enable(self):
        self.widget.grid(row=0,column=0,sticky=N+S+W+E)
        self.widget.bind(sequence="<FocusIn>", func=self.defocus)
        self.parent.addHook('output',self.output)
        
    def disable(self):
        self.widget.grid_remove()
        self.parent.delHook('output',self.output)
        
    def defocus(self,event):
        pass
    
    def output(self,data):
        self.widget.config(state=NORMAL)
        self.widget.insert(END,data)
        self.widget.insert(END,'\n')
        self.widget.config(state=DISABLED)
    