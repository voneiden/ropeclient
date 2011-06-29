#!/usr/bin/python
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
'''

from twisted.internet import tksupport, reactor
import window
import network

if __name__ == '__main__':
    print ("Loading..")
    window = window.Window()

    window.displayMain("Installing tksupport")
    tksupport.install(window.root)

    reactor.connectTCP(window.host, 49500, network.connectionFactory(window))

    window.displayMain("Starting reactor!")
    reactor.run()

