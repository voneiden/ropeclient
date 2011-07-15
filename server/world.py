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

import cPickle, time

class World(object):
    def __init__(self,name='default'):
        self.name = name
        self.spawn      = Location(self,"Void","Black flames rise from the eternal darkness. You are in the void, a lost soul, without a body of your own.")
        self.characters = []
        self.players    = []
        self.locations  = [self.spawn]
        self.messages = {}
        
    def timestamp(self):
        timestamp = time.time()
        print "timestamp",timestamp,self.messages.keys()
        while timestamp in self.messages.keys():
            timestamp += 0.01
        return timestamp
        
    def save(self):
        f = open('worlds/%s.world','w')
        cPickle.dump(self,f)
        f.close()

    def message(self,recipients,message):
        ''' This is the function to send messages to player. The message is given an ID which can be later retrieved! '''
        timestamp = self.timestamp()
        self.messages[timestamp] = message
        print "Preparing to message"
        if isinstance(recipients,Character):
            recipients.message(timestamp)
            print "1"
        elif isinstance(recipients, list):
            print "2"
            for recipient in recipients:
                recipient.message(timestamp)
    
    def offtopic(self,message):
        timestamp = self.timestamp()
        for player in self.players:
            player.connection.write("oft %f %s"%(timestamp,message))
            
    def updatePlayers(self):
        print "Updating player list.."
        typinglist = []
        for player in self.players:
             if player.typing: typinglist.append("%s:1"%player.name)
             else: typinglist.append("%s:0"%player.name)
        lop = ";".join(typinglist)
        for player in self.players:
            player.connection.write("plu %s"%lop)
            
    def updatePlayer(self,player):
        print "Updating just one player"
        if player.typing: 
            buffer = "%s:1"%(player.name)
        else: 
            buffer = "%s:0"%(player.name)
        for player in self.players:
            player.connection.write("ptu %s"%buffer)
            
    def addPlayer(self,player):
        if player not in self.players:
            self.players.append(player)
            self.updatePlayers()
            self.offtopic("%s has joined the game!"%player.name)
            
    def remPlayer(self,player):
        if player in self.players:
            self.players.remove(player)
            self.updatePlayers()
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
        
        self.read = []
        self.unread = []
        
        self.move(self.world.spawn)
    def move(self,location):
        if self.location != None:
            print "Left from location"
            if self in self.location.characters:
                self.location.characters.remove(self)
                self.location.announce("%s has left."%(self.name))
        self.location = location
        self.location.characters.append(self)
        self.location.announce("%s has arrived."%(self.name))
        self.world.message(self,"You have arrived.")
        
    def attach(self,player):
        self.player = player
        self.player.character = self
        
        while len(self.unread):
            message = self.unread.pop(0)
            self.message(message)
            self.read.append(message)
            
    def detach(self):
        self.player = None
        
    def message(self,timestamp): 
        print "sending message id",timestamp
        if self.player:
            self.player.send(self.world.messages[timestamp])
            self.read.append(timestamp)
        else:
            self.unread.append(timestamp)
        
class Location(object):
    def __init__(self,world,name="New location",description = ""):
        self.world = world
        self.name = name
        self.description = description
        self.characters = []
        
    def announce(self,message,ignore=None):
        recipients = self.characters[:]
        print "Announcing to",recipients,message
        if ignore in recipients: recipients.remove(ignore)
        if len(recipients) > 0: 
            self.world.message(recipients,message)
        else:
            print "Nobody to receive this message, ignoring.."
