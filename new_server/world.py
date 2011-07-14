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
'''
Design some kind of nice system when loading a saved world that checks for missing
attributes
'''

import cPickle

class World(object):
    def __init__(self,name='default'):
        self.name = name
        self.spawn      = Location("Void","Black flames rise from the eternal darkness. You are in the void, a lost soul, without a body of your own.")
        self.characters = []
        self.locations  = [self.spawn]
        
           
    def save(self):
        f = open('worlds/%s.world','w')
        cPickle.dump(self,f)
        f.close()

        
class Character(object):
    def __init__(self,world,name='unnamed',owner=None):
        self.world = world
        self.owner = owner
        self.player = None
        self.name = name
        self.description = ''
        self.info        = ''
        
        # TODO set location here
        self.location = None
        
        self.invisible = False
        self.mute      = False
        self.deaf      = False
        self.blind     = False
        
    def move(self,location):
        if self.location != None:
            print "Left from location"
            if self in self.location.characters:
                self.location.characters.remove(self)
                self.location.announce("%s has left."%(self.name))
        self.location = location
        self.location.characters.append(self)
        self.location.announce("%s has left."%(self.name))
        
    
        
class Location(object):
    def __init__(self,name="New location",description = ""):
        self.name = name
        self.description = description
        self.characters = []
        
    def announce(self,message,ignore=None):
        for character in self.characters:
            if character == ignore: continue
            character.player.sendMessage(message)
            