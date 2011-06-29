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

'''
import re

class Player(object):
    '''
    Player is the standard class that handles basic client processing
    Player can be attached to various characters, or if unattached, it
    will be just a soul floating in space. Souls, unless GM's, may only
    send offtopic messages.
    '''

    def __init__(self, connection, core):
        self.connection = connection
        self.core = core
        self.db = self.core.db
        self.username = 'Unknown'
        self.password = ''
        self.handler = self.loginHandler

    def recvIgnore(self, message):
        pass

    def recv(self, message):
        print "Recv", message
        message = message.strip()
        tok = message.split(' ')
        if tok[0] == 'msg':
            response = self.handler(tok[1:])
            print "Got resp",response
            print "Type",type(response)
            if type(response) is str or type(response) is unicode:
                self.send(None, response)

        elif tok[0] == 'pnt':
            pass

        elif tok[0] == 'pit':
            pass

        elif tok[0] == 'hsk':
            if tok[1] != self.core.version:
                self.send("Your version of ropeclient (%s) is not" +
                          " compatible with this server (%s)" % (tok[1],
                          self.core.version))
                self.recv = self.recvIgnore

        self.send(None, message)

    def send(self, username, message):
        print "Send", message
        if username == None:
            username == 'Server'
        message = self.core.createMessage(self.username, message)
        self.connection.sendMessage(message)

    def loginHandler(self, message):
        """ Message is tokenized! """

        if self.username == 'Unknown':
            if len(message) == 1:
                if message[0] in self.db.accounts.keys():
                    return "Account foudn"

                elif re.match("^[A-Za-z]+$", message[0]):
                    self.username = (False,message[0])
                    return "The account you typed does not exist. Would you like to create a new account by the name '%s'?" % message[0]
                else:
                    return "This not ok"
            else:
                return "This not ok length"
        else:
            if type(self.username) == tuple and len(message[0]) > 0:
                if self.username[0] == False:
                    if message[0][0].lower() == 'y':
                        self.username = (True,self.username[1])
                        return "Choose your password"
                    else:
                        self.username = 'Unknown'
                        return "Who are you then?"
                else:
                    return "Password chosen!"
            else:
                return "Checking your password"
