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

import cPickle, time, re

class World(object):
    def __init__(self,name='default'):
        self.name = name
        self.spawn      = Location(self,"Void","Black flames rise from the eternal darkness. You are in the void, a lost soul, without a body of your own.")
        self.characters = []
        self.players    = []
        self.locations  = [self.spawn]
        self.messages = {}
        self.memory = {}
        self.unique = 0
    def uniqueID(self):
        self.unique += 1
        return self.unique 
        
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
            player.connection.write("oft %f %s"%(timestamp,player.character.parse(message)))
            
    def updatePlayers(self):
        print "Updating player list.."
        typinglist = []
        for player in self.players:
             if player.typing: typinglist.append("%s:1:$(name=%s)"%(player.name,player.character.name))
             else: typinglist.append("%s:0:$(name=%s)"%(player.name,player.character.name))
        lop = ";".join(typinglist)
        for player in self.players:
            player.connection.write("plu %s"%player.character.parse(lop))
            
    def updatePlayer(self,player):
        print "Updating just one player"
        if not player.character: return
        if player.typing: 
            buffer = "%s:1:$(name=%s)"%(player.name,player.character.name)
        else: 
            buffer = "%s:0:$(name=%s)"%(player.name,player.character.name)
        for player in self.players:
            player.connection.write("ptu %s"%player.character.parse(buffer))
            
    def addPlayer(self,player):
        if player not in self.players:
            self.players.append(player)
            self.updatePlayers()
            self.offtopic("%s has joined the game!"%player.name)
            
    def remPlayer(self,player):
        if player in self.players:
            self.players.remove(player)
            self.updatePlayers()
            
    def find(self,name,target):
        """ 
            Will search target list for an identity.
            Returns None if not found, object if single
            occurence found, or a list if multiple choices
            were found
        """
        results = []
        for obj in target:
            if name.lower() in obj.name.lower(): results.append(obj)
        if len(results) == 0: 
            return None
        elif len(results) == 1: 
            return results[0]
        else:
            for obj in results:
                if name == obj.name:
                    return obj
            return results
    def findOwner(self,owner,target):
        """ 
            Will search target list for an identity.
            Returns None if not found, object if single
            occurence found, or a list if multiple choices
            were found
        """
        print "FINDOWNERS"
        print target
        print owner
        results = []
        for obj in target:
            if owner.lower() in obj.owner.lower(): results.append(obj)
        if len(results) == 0: 
            return None
        elif len(results) == 1: 
            return results[0]
        else:
            return results   
            
    def findUnique(self,unique,target):
        result = []
        for obj in target:
            if unique == obj.unique: return obj
        return None
        
class Character(object):
    def __init__(self,world,owner=None,name='unnamed',info="A soul",description="A new character"):
        self.unique = world.uniqueID()
        self.world = world
        self.owner = owner
        self.player = None
        self.name = name
        self.description = description
        self.info        = info
        
        # TODO set location here
        self.location = None
        
        self.invisible = False
        self.mute      = False
        self.deaf      = False
        self.blind     = False
        
        self.read = []
        self.unread = []
        
        self.memory = {}
        
        self.world.characters.append(self)
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
            self.player.send(self.parse(self.world.messages[timestamp]))
            self.read.append(timestamp)
        else:
            self.unread.append(timestamp)
            
    def parse(self,message):
        #nameregex = "(?<=\(name\=).+?(?=\))"
        nameregex = "\$\(name\=.+?\)"
        #message = re.sub(nameregex, self.memoryCheck, message)
        #return message
        print "Parsing.."
        for match in re.finditer(nameregex,message):
            name = self.memoryCheck(match)
            print "Replacing..",match.group(),name
            message = message.replace(match.group(),name,1)
        
        return message
    def memoryCheck(self,match):
        name = match.group()[7:-1]
        character = self.world.find(name,self.world.characters)
        if not character: 
            print "character not found"
            return name
        if character.name in self.memory:
            return self.memory[character.name]
        elif character == self:
            return character.name
        else:
            return character.info
        
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
