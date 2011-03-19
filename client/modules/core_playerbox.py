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
from Tkinter import Listbox,N,S

class RopeModule:
    ''' This is the base module, it should define at least
    __init__(self,parent) to initialize itself
    enable(self) to enable the module 
    disable(self) to disable the module
    '''
    def __init__(self,parent):
        self.parent = parent
        self.listbox = Listbox(parent.frame)
        
    def enable(self):
        self.listbox.grid(row=0,column=1,columnspan=2,sticky=N+S)
        
    def disable(self):
        self.listbox.grid_remove()
        