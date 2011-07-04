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
        self.characters = []
        self.locations  = []
           
    def save(self):
        f = open('worlds/%s.world','w')
        cPickle.dump(self,f)
        f.close()
        
    def find(self,identity,target):
        """ 
            Will search target list for an identity.
            Returns None if not found, object if single
            occurence found, or a list if multiple choices
            were found
        """
        results = []
        for obj in target:
            if identity.lower() in obj.name.lower(): results.append(obj)
        if len(results) == 0: 
            return None
        elif len(results) == 1: 
            return results[0]
        else:
            for obj in results:
                if identity.lower() == obj.name.lower():
                    return obj
            return results
        
class Character(object):
    def __init__(self,name='unnamed',owner=None):
        self.owner = owner
        self.player = None
        self.name = name
        
        
class Location(object):
    def __init__(self,name="New location",description = ""):
        self.name = name
        self.description = description
        self.characters = []
