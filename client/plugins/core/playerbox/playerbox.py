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
from Tkinter import Listbox,N,S, END

class Plugin:
    ''' This is the base module, it should define at least
    __init__(self,parent) to initialize itself
    enable(self) to enable the module 
    disable(self) to disable the module
    '''
    def __init__(self,core):
        self.core = core
        self.widget = Listbox(core.frame,background="black",foreground="white")
        self.playerlist = {}
        
    def enable(self):
        self.widget.grid(row=0,column=1,columnspan=2,sticky=N+S)
        self.core.event.add('lineReceived',self.lineReceived)
        
    def disable(self):
        self.widget.grid_remove()
        self.core.event.rem('lineReceived',self.lineReceived)
    
    def update(self):
        self.widget.delete(0, END)
        for player,state in self.playerlist.items():
            if state[0]: self.widget.insert(END, "*%s"%player)
            else:         self.widget.insert(END, "%s"%player)
    
    def lineReceived(self,kwargs):
        tok = kwargs['tok']
        header = tok[0].lower()
        
        if   header == 'lop' and len(tok) > 1:
            print "plugins.core.playerbox: lop",tok
            players = tok[1:]
            self.playerlist = {}
            for player in players:
                self.playerlist[player] = [False,False]
            self.update()
            
        elif header == 'pit' and len(tok) > 1:
            if tok[1] in self.playerlist:
                self.playerlist[tok[1]][0] = True
                self.update()
                
        elif header == 'pnt' and len(tok) > 1:
            if tok[1] in self.playerlist:
                self.playerlist[tok[1]][0] = False
                self.update()
     
    