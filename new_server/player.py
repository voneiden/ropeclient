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


class Player(object)):
    '''
    Player is the standard class that handles basic client processing
    Player can be attached to various characters, or if unattached, it
    will be just a soul floating in space. Souls, unless GM's, may only
    send offtopic messages.
    '''

    def __init__(self, connection, core):
        self.connection = connection
        self.core = core
        self.username   = 'Unknown'
        self.password   = ''

    def recvIgnore(self, message):
        pass

    def recv(self, message):
        print "Recv",message
        message = message.strip()
        tok = message.split(' ')
        if tok[0] == 'msg':
            pass
        elif tok[0] == 'pnt':
            pass
        elif tok[0] == 'pit':
            pass
        elif tok[0] == 'hsk':
            if tok[1] != self.core.version:
                self.send("Your version of ropeclient (%s) is not" +
                          " compatible with this server (%s)"%(tok[1],self.core.version))
                self.recv = self.recvIgnore
        self.send(message)

    def send(self,message):
        print "Send",message
        self.connection.sendMessage(self.core.createMessage(self.username,message))
