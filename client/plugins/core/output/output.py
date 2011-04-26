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
from Tkinter import N,S,E,W,WORD,DISABLED,NORMAL, StringVar, END
from ScrolledText import ScrolledText
import time,re

class Plugin:
    ''' This module defines the basic output textbox
    '''
    def __init__(self,core):
        self.parent = core
        self.widget = ScrolledText(self.parent.frame,width=80,height=20,
                                     wrap=WORD,
                                     state=DISABLED, background="black",foreground="white")
        self.widget.yview(END)
    def enable(self):
        self.widget.grid(row=0,column=0,sticky=N+S+W+E)
        self.widget.bind(sequence="<FocusIn>", func=self.defocus)
        self.parent.event.add('output',self.output)
        self.parent.event.add('lineReceived',self.receiveMessage)
    def disable(self):
        self.widget.grid_remove()
        self.parent.event.rem('output',self.output)
        self.parent.event.rem('lineReceived',self.receiveMessage)
        
    def defocus(self,event):
        pass
    
    def output(self,data):
        ''' This function writes the data to the output buffer
        The data can be a string or a [tags,text] list pairs. '''
        self.widget.config(state=NORMAL)
        if type(data) == str: 
            timestamp = time.strftime('[%H:%M:%S]', time.localtime(time.time()))
            self.widget.insert(END,"%s %s"%(timestamp,data))
        elif type(data) == list:
            for tags,text in data:
                self.widget.insert(END,text,tags)
        self.widget.insert(END,'\n')
        self.widget.config(state=DISABLED)
        self.widget.yview(END)
        
    def receiveMessage(self,kwargs):
        print "plugins.core.output: receiveMessage()"
        tok = kwargs['tok']
        header = tok[0].lower()
        
        if header == 'msg' and len(tok) > 3:
            messageOwner  = tok[1]
            messageTime   = tok[2]
            messageContent= " ".join(tok[3:])
            
            self.output(self.parse(messageContent,messageOwner,messageTime))
        
        
    def parse(self,message,owner,timestamp):
        tag = time
        self.widget.tag_config(tag)
        buffer = []
        
        reColor = "(?<=\<)[a-z]+?(?=>)"
        reText  = "<[a-z]+>"
        default = 'gray'
        colors = re.findall(reColor,message)
        text   = re.split(reText,message)
        colors.insert(0,default)
        
        for i in xrange(len(colors)):
            buffer.append(((tag,colors[i]),text[i]))
            
        return buffer
    