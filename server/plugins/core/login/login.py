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


    Also, this program features very messy code, don't hurt your head
    trying to decypher it.

    Copyright 2010-2011 Matti Eiden <snaipperi()gmail.com>
    
    
    This login module supports basic player authentication through password 
    which is sha hashed client side. Once the login process is completed succesfully
    the module calls core event for loggedIn and other modules can take over.
    
    The module also saves the account name under player.account
    
    The module uses a data file called passwords.pickle
'''
import pickle

class Plugin:
    def __init__(self,core):
        print "Initializing plugin: core.login"
        self.pluginName        = "core - login handler"
        self.pluginAuthor      = "Matti Eiden"
        self.pluginContact     = "Email: Matti Eiden <snaipperi(at)gmail.com>"
        self.pluginDescription = """ This plugin handles basic player authentication"""
        
        self.core  = core
        
        ''' This plugin uses the core event connectionMade and player event lineReceived '''
        
        self.core.event.add("connectionMade",self.connectionMade)
        
        self.motd = open('strings/motd.txt','r').read()
        try: self.passwords = pickle.load(open('data/passwords.pickle','rb'))
        except: self.passwords = {}
        
    def connectionMade(self,kwargs):
        print "plugins.core.login: Connection made"
        player = kwargs['player']
        
        player.version = False
        player.account = False
        player.pw      = False
        
        player.event.add("lineReceived",self.lineReceived)
        
    def lineReceived(self,kwargs):
        print "plugins.core.login: lineReceived - %s"%kwargs['line']
        player = kwargs['player']
        line   = kwargs['line']
        tok = line.split(' ')
        if not player.version:
            if tok[0] != 'hsk': player.disconnect();return
            elif len(tok) != 2: player.disconnect();return
            
            if tok[1] == 'SUPERHANDSHAKE':
                self.core.event.call("sendMessage",{'to':player,'message':"You are running a ropeclient with a very ancient protocol. To connect to this server, update."})
                return
            
            
            self.core.event.call("enablePlugin",{'to':player, 'plugin':'plugins.core.output'})
            self.core.event.call("enablePlugin",{'to':player, 'plugin':'plugins.core.entry'})
            #self.core.event.call("requireModule",{'to':player, 'module':'plugins.core.playerbox'})
            
            if tok[1] != self.core.version:
                self.sendMessage(player,"Outdated version. You're running %s, server is running %s."%(tok[1],self.core.version))
            else:
                self.sendMessage(player,"Version up to date.")
                self.sendMessage(player,self.motd)
                self.sendMessage(player,"What is your name?")
            player.version = tok[1]
                
        elif not player.account and len(tok) > 1:
            name = tok[1].lower()
            if name in self.passwords:
                player.account = name
                self.sendMessage(player,"%s's password?"%name)
                self.core.event.call("modPassword",{'to':player})
            else:
                self.sendMessage(player,"%s is a new account. Do you want to create a new account?"%name)
                player.account = (name,1)
                
                
        elif len(tok) > 1:
            # If player is creating a new account, verify that's what he wants!
            if type(player.account) == tuple:
                if tok[1][0].lower() == "y":
                    player.account = player.account[0]
                    self.sendMessage(player,"What would your password be?")
                    self.core.event.call("modPassword",{'to':player})
                    
                else:
                    player.account = False
                    self.sendMessage(player,"What is your name?")
                    
            
            else:
                pwd = tok[1]
                self.core.event.call("modPassword",{'to':player})
                
                if player.account in self.passwords:
                    if pwd == self.passwords[player.account]:
                        #Login OK
                        print "plugins.core.login: login OK for",player.account
                        self.core.event.call("loggedIn",{'player':player})
                        player.event.rem("lineReceived",self.lineReceived)
                    else:
                        self.sendMessage(player,"Invalid password.")
                        player.disconnect()
                        
                else:
                    self.passwords[player.account] = pwd
                    self.sendMessage(player,"New account created.")
                    print "plugins.core.login: New account created for",player.account
                    self.core.event.call("loggedIn",{'player':player})
                    f = open('data/passwords.pickle','wb')
                    pickle.dump(self.passwords,f)
                    f.close()
                    
                    
        else: print "plugins.core.login: ignored packet",line
                

    def sendMessage(self,to,message):
        self.core.event.call("sendMessage",{'to':to,'message':message})
        