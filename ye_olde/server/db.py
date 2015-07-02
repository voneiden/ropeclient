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

    This is now the 3rd complete -from scratch- version of the server.
    The original version was functional, but featured rather hacky code
    and was not really expandable. The second version was designed towards
    a plugin based approach, however it turned out to be rather painful
    to develop as utilizing object-oriented code became increasingly difficult.
    Now I'm after a 3rd version, this time sacrificing the plugin support
    for fast development but with a clean logic. Hopefully this turns out well.

    == Few words on the rope protocol ==

    The protocol between the client and server is pretty straightforward
    The packet starts with a 3-letter command. The most crucial ones are
    msg and pwd. The server to client msg packet looks like this

    msg timestamp owner payload

    And the client to server msg packet looks simply like this
    msg payload

    This time around I plan on implementing also standard telnet protocol.



'''

'''
The server should send some kind of line to the client describing a clickable event..
clk id;color;command;text

better even! 

$(clicktocommand:id;color;command;text)


'''
import cPickle, time

class db:

    def __init__(self):
        try:
            f = open('accounts.db', 'rb')
            self.accounts = cPickle.load(f)
            f.close()
        except IOError:
            self.accounts = []
         
        
        
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
        results = []
        for obj in target:
            if owner.lower() in obj.owner.lower(): results.append(obj)
        if len(results) == 0: 
            return None
        elif len(results) == 1: 
            return results[0]
        else:
            for obj in results:
                if owner.lower() == obj.owner.lower():
                    return obj
            return results
            
    def save(self):
        print "Saving accounts.db.."
        f = open('accounts.db','wb')
        cPickle.dump(self.accounts,f,-1)
        f.close()
        
class Account:
    def __init__(self,name,password):
        self.name = name
        self.password = password
        self.style = 0
        
