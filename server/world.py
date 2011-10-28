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

# NOTE character deleting has potential memory leak issue: memorize function might
#contain a reference to the character? too lazy to check right now


import cPickle, time, re, random

class World(object):
    def __init__(self,name='default',pw=None):
        self.name = name
        self.pw = pw
        self.objects = []
        self.locations = []
        self.characters = []
        self.players    = []
        self.messages = {}
        self.memory = {} # Whats this?
        self.idents = {} # Contains all id()'s of objects   
        self.spawn      = Location(self,"Void","Black flames rise from the eternal darkness. You are in the void, a lost soul, without a body of your own.")
    
    def timestamp(self):
        timestamp = time.time()
        print "timestamp",timestamp,self.messages.keys()
        while timestamp in self.messages.keys():
            timestamp += 0.01
        return timestamp
        
    def save(self):
        f = open('worlds/%s.world'%self.name,'wb')
        cPickle.dump(self,f)
        f.close()
        
    def load(self,core,name):
        print "Loading world..",name
        try:
            f = open('worlds/%s.world'%name,'rb')
            world = cPickle.load(f)
            f.close()
        except:
            print "Failed!"
            return False
        print "Success!"
        #world.core = self.core
        core.world = world
        world.players = []
        for player in self.players:
            player.send("<fail>### GAMEMASTER HAS LOADED A NEW WORLD ###")
            player.world = world
            player.login()
            
        return True

    def message(self,recipients,message):
        ''' This is the function to send messages to character. The message is given an ID which can be later retrieved! '''
        timestamp = self.timestamp()
        # Do the dice rolling too..
        message = self.doDice(message)
        self.messages[timestamp] = message
        print "Preparing to message"
        if isinstance(recipients,Character):
            recipients.message(timestamp)
            print "1"
        elif isinstance(recipients, list):
            print "2"
            for recipient in recipients:
                recipient.message(timestamp)
    
    def offtopic(self,message,recipients=None):
        # TODO all offtopic needs to be logged, and upon player
        # connecting, the last.. say, 50 lines will be sent.
        if not recipients: 
            recipients = self.players
        timestamp = self.timestamp()
        print "Sending offtopic message",message
        for player in recipients:
            player.sendOfftopic(message,timestamp)
            
    def updatePlayers(self):
        print "Updating player list.."
        typinglist = []
        for player in self.players: #TODO update here
            typinglist.append(
                "{name}:{typing}:$(name={charname})".format(
                    name=player.name,
                    typing="1" if player.typing else "0",
                    charname=player.character.name if player.character else "None"))
        
        
        
        
             #if player.typing: typinglist.append("%s:1:$(name=%s)"%(player.name,player.character.name))
             #else: typinglist.append("%s:0:$(name=%s)"%(player.name,player.character.name))
        lop = ";".join(typinglist)
        for player in self.players:
            player.connection.write("plu %s"%player.replaceCharacterNames(lop))
            
             
    def updatePlayer(self,player):
        print "Updating just one player"
        #if not player.character: return
        buffer = "{name}:{typing}:{charname}".format(
            name=player.name,
            typing=player.typing,
            charname=player.character.name if player.character else "None")
        print "Got buffer as",buffer
        #if player.typing: 
        #    buffer = "%s:1:$(name=%s)"%(player.name,player.character.name)
        #else: 
        #    buffer = "%s:0:$(name=%s)"%(player.name,player.character.name)
        for player in self.players:
            player.connection.write("ptu %s"%player.replaceCharacterNames(buffer))
            
    def addPlayer(self,player):
        if [p for p in self.players if p.name == player.name]:
            p.disconnect() #This will automatically call remPlayer etc.
        
        self.players.append(player)
        self.updatePlayers()
        self.offtopic("<notify>%s has joined the game!"%player.name)
        if not player.character:
            player.character = Soul(self,player)
            
    def remPlayer(self,player):
        print "REMOVING player"
        if player in self.players:
            self.players.remove(player)
            self.updatePlayers()
            
            self.offtopic("<notify>%s has left the game!"%player.name)
            
    def find(self,name,target):
        """ 
            Will search target list for an identity.
            Returns None if not found, object if single
            occurence found, or a list if multiple choices
            were found
        """
        # TODO check that the object has .name attribute?
        results = []
        for obj in target:
            if name.lower() in obj.name.lower(): results.append(obj)
        if len(results) == 0: 
            return None
        elif len(results) == 1: 
            return results
        else:
            for obj in results:
                if name == obj.name:
                    return [obj]
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
        #elif len(results) == 1: 
        #    return results[0]
        else:
            return results   
      
    def findId(self,ident,objects):
        print "findID",ident
        try:
            int(ident)
        except ValueError:
            return False
        
        if int(ident) < len(objects):
            return [objects[int(ident)]]
        else:
            print "Searching for static id"
            print self.idents.keys()
            if ident in self.idents.keys():
                obj = self.idents[ident]
                print "obj found"
                if obj in objects:
                    return [obj]
                else:
                    print "Not in objects"
                    return False
            else:
                print "not found"
                return False
   

    def findAny(self,key,target):
        match = self.findId(key,target)
        if match: return match
        match = self.find(key,target)
        if match: return match
        
        

    def doDice(self,message):
        evalregex = "\![d0-9\+\-\*\/]+"
        diceregex = "[0-9]*d[0-9]+"
        resultmessage = message[:]
        for equation in re.finditer(evalregex,message):
            equation = equation.group()[1:]
            resultequation = equation
            allrolls = []
            try:
                for dice in re.finditer(diceregex,message):
                    dice = dice.group()
                    tok = dice.split('d')
                    roll = self.doRoll(tok[0],tok[1])
                    resultequation = resultequation.replace(dice,str(roll[0]),1)
                    allrolls.append(roll[1])
            except OverflowError:
                return message
            total = eval(resultequation)
            resultmessage = resultmessage.replace("!%s"%equation,"$(dice=[%s: %i];%s)"%(equation,total,str(allrolls)),1)
                
        return resultmessage
                
    def doRoll(self,x,y):
        if x == '': x = 1
        x = int(x)
        y = int(y)
        if x > 20 or x < 1: 
            raise OverflowError
        if y > 100 or y < 1: 
            raise OverflowError
        
        total = 0
        rolls = []
        for i in xrange(x):
            r = random.randint(1,y)
            total += r
            rolls.append(r)
        return (total,rolls)
    
    def addObject(self,obj):
        self.objects.append(obj)
    def remObject(self,obj):
        self.objects.remove(obj)
    
    def addLocation(self,location):
        self.locations.append(location)
        self.addObject(location)
        
    def remLocation(self,location):
        self.locations.remove(location)
        self.remObject(location)
        
    def addCharacter(self,character):
        self.characters.append(character)
        self.addObject(character)
        if character.location == None:
            character.move(self.spawn)
        else:
            character.move(location)
    def remCharacter(self,character):
        self.characters.remove(character)
        self.remObject(character)
        character.location.announce("%s has been terminated."%(self.name))
        character.location.characters.remove(character)
        
    def addExit(self,exit):
        self.addObject(exit)
       
    def remExit(self,exit):
        self.remObject(exit)
        

        
        
        
        
class Character(object):
    def __init__(self,world,owner=None,name='unnamed',info="A soul",description="A new character",location = None):

        self.world = world
        self.owner = owner
        self.player = None
        self.name = name
        self.rename = "$(name=%s)"%(self.name)
        self.description = description
        self.info        = info
        self.color = "default"
        self.location = None

        
        
        self.invisible = False
        self.mute      = False
        self.deaf      = False
        self.blind     = False
        self.soul      = False
        
        self.read = []
        self.unread = []
        
        self.memory = {}
        
        self.world.addCharacter(self)
        
        ''' ID update '''
        self.ident = str(id(self))
        self.world.idents[self.ident] = self
        
        
            
    def __setstate__(self): #TODO test this!
        print "Loading saved character.."
        print "Updating ident!"
        if self.ident in self.world.idents.keys():
            del self.world.idents[self.ident]
        self.ident = str(id(self))
        self.world.idents[self.ident] = self
       
    def id(self):
        ''' Unique id of character '''
        return (str(self.world.characters.index(self)),str(id(self)))
        
    def setRename(self):
        self.rename = "<%s>$(name=%s)<reset>"%(self.color,self.name)    
    
    def move(self,location):
        if self.location == location: return
        if self.location != None:
            print "Left from location"
            if self in self.location.characters:
                if not self.invisible:
                    self.location.announce("%s has left."%(self.rename))
                self.location.characters.remove(self)
        self.location = location
        self.location.characters.append(self)
        if not self.invisible:
            self.location.announce("%s has arrived."%(self.rename),self)
        self.world.message(self,"You have arrived.") #TODO decide whether send on world.message
        if self.player: self.player.send(self.player.handle_look([]))
        
    def attach(self,player):
        self.player = player
        self.player.character = self
        self.player.connection.write("clr main")
        for message in self.read[-50:-1]:
            self.message(message)
        while len(self.unread):
            message = self.unread.pop(0)
            self.message(message)
            self.read.append(message)
        self.player.sendOfftopic("<ok>Attached to %s!"%self.name)
            
    def detach(self):
        self.player.character = None
        self.player = None
        
    def message(self,timestamp): 
        print "sending message id",timestamp
        if self.player:
            #self.player.send(self.parse(self.world.messages[timestamp])) #TODO
            if timestamp not in self.read:
                self.read.append(timestamp)
        else:
            self.unread.append(timestamp)
            
    #def parse(self,message):
    #    ''' This functions solves name-memory '''
    #    nameregex = "\$\(name\=.+?\)"
    #    print "Parsing.."
    #    for match in re.finditer(nameregex,message):
    #        name = self.memoryCheck(match)
    #        print "Replacing..",match.group(),name
    #        message = message.replace(match.group(),name,1)
    #    
    #    return message
    
    # Todo update these things to work with unique id's
    #def memoryCheck(self,match):
    #    print "Checking my memory.."
    #    print self.memory
    #    for key in self.memory.keys():
    #        print "Remembering",key,type(key)
    #    name = match.group()[7:-1]
    #    character = self.world.find(name,self.world.characters)
    #   
    #    if not character: 
    #        print "character not found"
    #        return name
    #    else:
    #        character = character[0] #TODO temp fix
    #    if character in self.memory.keys():
    #        return self.memory[character]
    #    elif character == self:
    #        return character.name
    #    else:
    #        return character.info
    def introduce(self,name):
        print "Introducing.."
        self.location.announce("%s introduces himself as %s"%
                              (self.rename,"$(clk2cmd:%s;notify;/memorize %s %s;%s)"%
                              (self.name,self.ident,name,name)))
        
class Soul(Character):
    ''' Souls are temporary invisible characters '''
    def __init__(self,world,player,location=None):
        Character.__init__(self,world)
        self.world = world
        self.owner = player.name
        self.name  = "Soul"
        self.description = "Soul"
        self.info = "Soul"
        
        self.attach(player)
        if location:
            self.location = location
        else:
            self.location = self.world.spawn

        #TODO detach should destroy the soul
  
class Location(object):
    def __init__(self,world,name="New location",description = ""):
        self.world = world
        self.name = name
        self.description = description
        self.characters = []
        self.links = []
        
        
        self.world.addLocation(self)
        
        self.ident = str(id(self))
        self.world.idents[self.ident] = self
        
    def __setstate__(self): #TODO test this!
        print "Loading saved location.."
        print "Updating ident!"
        if self.ident in self.world.idents.keys():
            del self.world.idents[self.ident]
        self.ident = str(id(self))
        self.world.idents[self.ident] = self
       
    def id(self):
        ''' Unique id of location '''
        return (str(self.world.locations.index(self)),str(id(self)))
    def dynid(self):
        return str(self.world.locations.index(self))
          
    def announce(self,message,ignore=None):
        recipients = self.characters[:]
        print "Announcing to",recipients,message
        if ignore in recipients: recipients.remove(ignore)
        if len(recipients) > 0: 
            self.world.message(recipients,message)
        else:
            print "Nobody to receive this message, ignoring.."

    
    def link(self,name,destination):
        
        # First check that exit name is not yet in use
        if self.findLink(name=name):
            return "(<fail>Exit name exists already"
        # Second check if there's an exit between these two locations already
        elif self.findLink(destination=destination):
            return "(<fail>Only one exit to destination is allowed.."
        
        else:
            link = Link(name,destination)
            self.links.append(link)
            return "(<ok>Exit created from %s (->%s->) %s"%(self.ident,name,destination.ident)
        
    def unlink(self,towards,both=True):
        if towards in self.exits:
            if both:
                for exit,location in self.exits[towards].exits.items():
                    if location == self:
                        del self.exits[towards].exits[exit]
            del self.exits[towards]
            return "(<ok>Unlinked"
        else:
            return "(<fail>Exit not found"
           
    def findLink(self,**kwargs):
        if 'name' in kwargs.keys():
             for link in self.links:
                if link.name == kwargs['name']: 
                    return link
             else:
                return False
                
        elif 'destination' in kwargs.keys():
            for link in self.links:
                if link.destination == kwargs['destination']:
                    return link
            else:
                return False

        else:
            return False




        
class Link:
    def __init__(self,name,destination,locked=False):
        self.name = name
        self.destination = destination
        self.locked = locked
        
