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


    Copyright 2010-2011 Matti Eiden <snaipperi()gmail.com>

    The world class file should be saveable as a whole
'''
import copy

class World:
    def __init__(self):
        self.characters = {}
        self.locations  = {}
        
    def save(self):
        selfsave = World()
        for name,character in self.characters.items():
            charactecopy = copy.copy(character)
            charactercopy.player = None
            selfsave.characters[name] = charactercopy
            
class Character:
    def __init__(self):
        self.owner = None
        self.player = None
        