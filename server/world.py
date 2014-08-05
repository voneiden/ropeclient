#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
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

    Copyright 2010-2013 Matti Eiden <snaipperi()gmail.com>

"""
import logging
from core import Core
from database import Database
from redis import StrictRedis


class WorldManager(Database):
    def __init__(self, core=None, client=None):
        """
        WorldManager provides interface for database actions involving
        listing, creating and deleting world objects.

        @param core: Core object
        @type core: Core
        @type client: StrictRedis
        """
        assert isinstance(core, Core)
        assert isinstance(client, StrictRedis)

        Database.__init__(self, core=core, client=client)

        self.interfaces = {}  # The dictionary of world idents mapped to world instances
        idents = self.list()
        logging.info("IDENTS: {}".format(str(idents)))
        logging.info("Creating world interface instances..")
        for ident in idents:
            assert isinstance(ident, str)
            if ident not in self.interfaces:
                logging.info("Loading new world (ident: {})".format(ident))
                self.interfaces[ident] = World(core, client, ident)

        # If not worlds exist, create a default world
        if len(idents) == 0:
            logging.info("No default worlds found, creating one")
            self.new(name="Official Sandbox")

    def list(self):
        idents = self.client.smembers("rp:worlds.list")
        return idents  # TODO: Generate dict

    def new(self, name="New world", password="", masters=[], **kwargs):
        """ Used to create a new world

        @param name: World name
        @param password: World password (empty string for none)
        @param masters: List of game masters
        @param **kwargs: Optional
        @type name: str
        @type password: str
        @type masters: (list, tuple)
        @return:
        """
        assert isinstance(name, str)
        assert isinstance(password, str)
        assert isinstance(masters, list) or isinstance(masters, tuple)

        logging.info("Generating a new world..")

        # Generate a new ident for the player and verify it is unused
        i_break = 0
        while True:
            ident = str(self.incr("ident"))
            if ident not in self.interfaces:
                break

            if i_break > 10:
                logging.error("Unable to generate a unique ident. Aborting.")
                return False

        # Add the ident to world members
        self.sadd("list", ident)

        # Create world object
        world = World(core=self.core, client=self.client, ident=ident)
        assert isinstance(world, Database)  # PyCharm assert hint

        # Update interfaces (we already verified the ident is unique above)
        self.interfaces[ident] = world

        # Add details
        world.set("name", name)
        world.set("password", password)
        world.sadd(ident, "masters", masters)

        logging.info("New world generated successfully!")

    def path(self, *args):
        """
        Path to world root (rp:worlds) and optional key (arg0)

        @param args: Optional key
        @return:
        """

        if len(args) > 0 and isinstance(args[0], str):
            return "rp:worlds.{}".format(args[0])
        else:
            return "rp:worlds"




class World(Database):
    def __init__(self, core=None, client=None, ident=None): # FIXME: THIS DOES NOT WORK!
        """
        World object provides interface to access a world object
        in the database.

        @param core: Core object
        @param ident: Identity of the object
        @type core: Core
        @type ident: str
        """
        assert isinstance(core, Core)
        assert isinstance(client, StrictRedis)
        assert isinstance(ident, str)

        Database.__init__(self, core=core, client=client)
        self.ident = ident

    def path(self, *args):
        """ Provides path for world objects

        @param args: May contain optionally a key or list of keys
        @return:
        """

        if len(args) == 0:
            return "rp:worlds:{}".format(self.ident)

        elif len(args) == 1 and isinstance(args[0], str):
            return "rp:worlds:{}.{}".format(self.ident, args[0])

        else:
            keys = list(args)
            for i, k in enumerate(keys):
                keys[i] = "rp:worlds:{}.{}".format(self.ident, k)
            return keys

        # TODO: dicts?
# NOTE character deleting has potential memory leak issue: memorize function might
#contain a reference to the character? too lazy to check right now
#FIXME

#TODO Make it so that souls can see the last 100 lines that have been happening in a location.

"""
import pickle, time, re, random, logging
from collections import OrderedDict

class World(object):
    def __init__(self,name,pw,gamemasters):
        self.name = name                # Can be unicode name?
        self.pw = pw                    # Password
        self.objects = []               # List of all objects
        self.locations = []             # List of all  - locations
        self.characters = []            # List of all  - characters
        self.players    = []            # List of all  - players
        self.messages = OrderedDict()              # Dictionary of all messages..
        self.gamemasters = gamemasters  # List of all gamemaster id's
        self.creator = gamemasters[0] if len(gamemasters) > 0 else None
        #self.memory = {} # Whats this? 
        #self.idents = {} # Contains all id()'s of objects    OBSOLETE?
        self.unique = 0                 # Unique counter
        self.spawn      = Location(self,"Void","Black flames rise from the eternal darkness. You are in the void, a lost soul, without a body of your own.")
        self.offtopicHistory = []
        
        self.limitSpawn = True
        
        # Experimental
        self.calledRolls = {}
    def timestamp(self):
        timestamp = time.time()
        #print "timestamp",timestamp,self.messages.keys()
        while timestamp in self.messages.keys():
            timestamp += 0.01
        return timestamp
        
    def saveWorld(self):
        f = open('worlds/%s.world'%self.name,'wb')
        pickle.dump(self,f)
        f.close()
        
    def editName(self):
        pass #TODO should also modify the world save location!
        
    def setup(self,core):
        logging.info("Setting up loaded world '{0}'".format(self.name))
        self.players = []
        self.calledRolls = {}
        
        oldworld = [world for world in core.worlds if world.name.lower() == self.name.lower()]
        if oldworld:
            #TODO move all old players to the new world
            core.worlds.remove(oldworld[0])
            logging.info("Removing old world {}".format(oldworld[0].name))
        core.worlds.append(self)
        
        # Fix soul bug, temporary
        logging.info( "Fixing soul bug")
        for character in self.characters:
            if isinstance(character,Soul):
                logging.info( "Destroying soul")
                self.remCharacter(character)
                continue
            if not hasattr(character,"talk"):
                character.talk = '<talk>'
                
        for location in self.locations:
            if not hasattr(location,'history'):
                logging.info( "Fixing history")
                location.history = []
                
        # Updating to new message format and ordereddict.
        if not isinstance(self.messages,OrderedDict):
            logging.info( "Regenerating message list")
            newmessages = OrderedDict()
            oldkeys = self.messages.keys()
            oldkeys.sort()
            for key in oldkeys:
                newmessages[key] = (None,self.messages[key])
            logging.info( "Done..")
            self.messages = newmessages

    def sendMessage(self,message,recipients=[]):
        ''' This function creates message id
            and forwards the message id's to characters '''
        
        timestamp = self.timestamp() # Message ID
        if isinstance(message,tuple):
            owner = message[0]
            content = message[1]
        else:
            owner = None
            content = message 
            
        
        #content = self.diceSub(content) #This is now handled in player class
        if content[0] != '<':
            content = '<default>' + content
        self.messages[timestamp] = (owner,content)
        #print "Preparing to message"
        if len(recipients) == 0:
            recipients = self.characters

        for recipient in recipients:
            recipient.message(timestamp)
        return timestamp
    
    def sendOfftopic(self,content,recipients=None):
        # TODO all offtopic needs to be logged, and upon player
        # connecting, the last.. say, 50 lines will be sent.
        # Do the dice rolling too..
        #content = self.diceSub(content) This is now handled in player
        if content[0] != '<':
            content = '<offtopic>' + content
            
        timestamp = self.timestamp()
        
        # Send to every user and log
        if not recipients: 
            recipients = self.players
            self.offtopicHistory.append((content,timestamp))
            
        
        #print "Sending offtopic message",content
        for player in recipients:
            player.sendOfftopic((content,timestamp))
            
    def sendEdit(self,id,message):
        #TEST>
        if message[0] != '<':
            message = '<default>'+message
        for player in self.players:
            content = player.replaceCharacterNames(message)
            content = player.createHighlights(content)
            player.connection.sendEdit(id,content)
            
            
    def updatePlayers(self):
        #print "Updating player list.."
        typinglist = []
        for player in self.players: #TODO update here
            typinglist.append(
                "{name}:{typing}:$(name={unique})".format(
                    name=player.name,
                    typing="1" if player.typing else "0",
                    unique=player.character.unique if player.character else "-1"))
        
        
        
        
             #if player.typing: typinglist.append("%s:1:$(name=%s)"%(player.name,player.character.name))
             #else: typinglist.append("%s:0:$(name=%s)"%(player.name,player.character.name))
        lop = ";".join(typinglist)
        for player in self.players:
            #print "LOP",lop
            #print "REP",player.replaceCharacterNames(lop)
            
            player.connection.write("plu %s"%player.replaceCharacterNames(lop))
             
    def updatePlayer(self,player):
        #print "Updating just one player"
        #if not player.character: return
        buffer = "{name}:{typing}:{charname}".format(
            name=player.name,
            typing=player.typing,
            charname=player.character.name if player.character else "None")
        #print "Got buffer as",buffer

        for player in self.players:
            player.connection.write("ptu %s"%player.replaceCharacterNames(buffer))
        
    def addPlayer(self,player):
        if [p for p in self.players if p.name == player.name]:
            p.connection.disconnect() #This will automatically call remPlayer etc.
        
        self.players.append(player)
        self.updatePlayers()
        
        #[obj[1] if not i else "%i %s"%(obj[0],obj[1]) for i,obj in enumerate(l)]
        #offtopic = [message[0] if not i else u"{0} {1}".format(message[1],message[0]) 
        #            for i,message in enumerate(self.offtopicHistory[-100:])]
        
        # Deliver a list to player.sendOfftopic
        
        player.sendOfftopic(self.offtopicHistory[-100:])
        #if offtopic:
        #    player.sendOfftopic("".join(offtopic),self.offtopicHistory[-100:][0][1])
        
        self.sendOfftopic("<notify>%s has joined the game!"%player.name)
        if not player.character:
            player.character = Soul(self,player)
        if player.name in self.gamemasters:
            player.gamemaster = True
            player.sendOfftopic("<notify>GM mode enabled!")
        
        #print "Do looky"
        player.sendMessage(player.handle_look())
            
    def remPlayer(self,player):
        #print "REMOVING player"
        if player in self.players:
            self.players.remove(player)
            self.updatePlayers()
            
            self.sendOfftopic("<notify>%s has left the game!"%player.name)
        if player.gamemaster:
            player.gamemaster = False
            
    
        
    def diceSub(self,message):
        ''' This function performs a regex substitution for a string of text '''
        return re.sub("\![d0-9\+\-\*\/]+",self.diceParse,message)
        
    def diceParse(self,match):
        diceregex = "[0-9]*d[0-9]+"
        equation = match.group()[1:]
        resultequation = equation
        allrolls = []
        try:
            for dice in re.finditer(diceregex,equation):
                dice = dice.group()
                tok = dice.split('d')
                roll = self.diceRoll(tok[0],tok[1])
                resultequation = resultequation.replace(dice,str(roll[0]),1)
                allrolls.append(roll[1])
        except OverflowError:
            return message
        try: 
            total = eval(resultequation)
        except SyntaxError:
            return "$(dice=[Bad syntax];N/A)"
        return "$(dice=[%s: %i];%s)"%(equation,total,str(allrolls))
            
            # Handle special rolls here?
                  
    def diceRoll(self,x,y):
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
        self.unique += 1
        obj.unique = self.unique
        
    def remObject(self,obj):
        if obj in self.objects:
            self.objects.remove(obj)
    
    def addLocation(self,location):
        self.locations.append(location)
        self.addObject(location)
        
    def remLocation(self,location):
        self.locations.remove(location)
        self.remObject(location)
        
    def addCharacter(self,character):
        #print "DEBUG",character.player
        self.characters.append(character)
        self.addObject(character)
        if character.location == None:
            character.move(self.spawn)
        else:
            character.move(character.location)
            
    def remCharacter(self,character):
        if character in self.characters:
            self.characters.remove(character)
        self.remObject(character)
        #if character.location.sendMessage("%s disappears in a flash."%(self.name))
        character.location.characters.remove(character)
        if character.player:
            character.detach()
            
        
    def addExit(self,exit):
        self.addObject(exit)
       
    def remExit(self,exit):
        self.remObject(exit)
        
"""
        
        
        
        
class Character(object):
    def __init__(self,world,owner=None,name='unnamed',info="A soul",description="A new character",location = None):

        self.world = world
        self.owner = owner
        self.player = None
        self.name = name
        #self.rename = "$(name=%s)"%(self.name) #TODO
        self.description = description
        self.info        = info
        #self.color = "default"
        
        
        self.talk = '<talk>'
        
        
        self.invisible = False
        self.mute      = False
        self.deaf      = False
        self.blind     = False
        self.soul      = False
        
        self.read = []
        self.unread = []
        
        self.memory = {}
        
        self.location = location
        self.world.addCharacter(self) #This will move the char too.

            
        #''' ID update '''
        #self.ident = str(id(self))
        #self.world.idents[self.ident] = self
        
    def rename(self):
        return "$(name={name})".format(name=self.unique)
            
            
    #def __setstate__(self,what): #TODO test this!
    #    print "Loading saved character.."
    #    print "Updating ident!"
    #    if self.ident in self.world.idents.keys():
    #        del self.world.idents[self.ident]
    #    self.ident = str(id(self))
    #    self.world.idents[self.ident] = self
       
    #def id(self):
    #    ''' Unique id of character '''
    #    return (str(self.world.characters.index(self)),str(id(self)))
        
    #def setRename(self):
    #    self.rename = "<%s>$(name=%s)<reset>"%(self.color,self.name)    
    
    def move(self,location):
        ''' Move the character to a location. '''
        ''' If location is the same that's already set, don't display arrive or leave messages '''
        #print "DEBUG2",self.player
        if self.location is not None and self.location is not location:
            #print "Left from location"
            if self in self.location.characters:
                if not self.invisible:
                    self.location.sendMessage("%s has left."%(self.rename()))
                self.location.characters.remove(self)
        
        
        #if self.location is location and self not in self.location characters: #TODO is this good?
        #    self.location.characters.append(self)
        #if self.location is not location:
        self.location = location
        self.location.characters.append(self)
        if not self.invisible and not isinstance(self,Soul): #FIXME multiple arrive messages, work on these.
            self.location.sendMessage("%s has arrived."%(self.rename()),self)
        self.world.sendMessage("You have arrived.",[self]) #TODO decide whether send on world.message
        if self.player: self.player.sendMessage(self.player.handle_look([]))
        
    def attach(self,player):
        self.player = player
        self.owner  = player.account.name
        self.player.character = self
        self.player.connection.write("clr main")
        #for message in self.read[-50:]:
        #    self.message(message)
        #while len(self.unread):
        #    message = self.unread.pop(0)
        #    self.message(message)
            #self.read.append(message)
        self.message(self.read[-50:] + self.unread)
        self.unread = []
        
        self.player.sendOfftopic("<ok>Attached to %s!"%self.name)
        self.world.updatePlayer(self.player)
            
    def detach(self):
            self.player.character = None
            self.player = None
        
    def message(self,stuff): 
        #print "sending message id",timestamp
        if self.player:
            
            if isinstance(stuff,list):
                buf = []
                for timestamp in stuff:
                    message = self.world.messages[timestamp]
                    buf.append((timestamp,message[0],message[1]))
                    if timestamp not in self.read:
                        self.read.append(timestamp)
                message = buf
                
            elif isinstance(stuff,float):
                #print "To player",self.player,self.player.name
                message = self.world.messages[stuff]
                message = (stuff,message[0],message[1])
                if stuff not in self.read:
                    self.read.append(stuff)
                    
                    
            #print "character.message:",message
            self.player.sendMessage(message)
        else:
            if isinstance(stuff,float):
                self.unread.append(stuff) 
            
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
        #print "Introducing.."
        self.location.announce("%s introduces himself as %s"%
                              (self.rename,"$(clk2cmd:%s;notify;/memorize %s %s;%s)"%
                              (self.name,self.ident,name,name)))
        
class Soul(Character):
    ''' Souls are temporary invisible characters '''
    def __init__(self,world,player,location=None):
        Character.__init__(self,world,"","","",location)
        self.world = world
        self.owner = player.name
        self.name  = "Soul"
        self.description = "Soul"
        self.info = "Soul"
        
        self.attach(player)
 
    def attach(self,player):
        #for msg in self.location.history[-50:]:
        #    self.message(msg)
           
        Character.attach(self,player)
        self.message(self.location.history[-50:]) 
        
    def detach(self):
        #print "Destroying soul!!!"
        self.player.character = None
        self.player = None
        self.world.remCharacter(self)
        
class Location(object):
    def __init__(self,world,name="New location",description = ""):
        self.world = world
        self.name = name
        self.description = description
        self.characters = []
        self.links = []
        self.history = []
        self.world.addLocation(self)
        
        #self.ident = str(id(self))
        #self.world.idents[self.ident] = self
        
    #def __setstate__(self): #TODO test this!
    #    print "Loading saved location.."
    #    print "Updating ident!"
    #    if self.ident in self.world.idents.keys():
    #        del self.world.idents[self.ident]
    #    self.ident = str(id(self))
    #    self.world.idents[self.ident] = self

    def sendMessage(self,message,ignore=None): 
        ''' This function compiles a list of characters
            in the location, removes the ignored (which is not a list..)
            and forwards it to world.sendMessage'''
        recipients = self.characters[:]
        #print "Announcing to",recipients,message
        if ignore in recipients: recipients.remove(ignore)
        if len(recipients) > 0: 
            timestamp = self.world.sendMessage(message,recipients)
            self.history.append(timestamp)
        else:
            #print "Nobody to receive this message, ignoring.."
            logging.info("Message sent to nobody: {}".format(message))
    
    def link(self,name,destination):
        
        # First check that exit name is not yet in use
        if not isinstance(destination,Location):
            #print "FAIL FAIL FAIL"
            #print destination
            logging.info("Major error in destination")
        if [link for link in self.links if link.name == name]:
            return "(<fail>Exit name exists already"
        
        elif [link for link in self.links if link.destination == destination]:
            return "(<fail>Only one exit to destination is allowed.."
        
        else:
            link = Link(name,destination)
            self.links.append(link)
            return "(<ok>Exit created from %s (->%s->) %s"%(self.unique,name,destination.unique)
        
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
        
