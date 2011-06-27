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
from Tkinter import N,S,E,W,WORD,DISABLED,NORMAL, StringVar, END, Tk, Frame, BOTH
from Tkinter import YES,Entry,Listbox
from ScrolledText import ScrolledText
import time,re

class Window:
    def __init__(self):
        '''
        Tkinter for speedy development!
        We have a root, and then we have a grid over the root, works very nice!
        '''

        ''' Initialize some variables '''
        self.connection = None
        self.host = "localhost"
        self.entryboxTyping = False
        ''' Create the root '''
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.title('Ropeclient')

        ''' Create the frame and define position 0,0 as the main expander '''
        self.frame = Frame(self.root,background="black")
        self.frame.pack(fill=BOTH,expand=YES)
        self.frame.grid_rowconfigure(0,weight=1)
        self.frame.grid_columnconfigure(0,weight=1)

        ''' Main text box '''
        self.textboxMain = ScrolledText(self.frame,width=80,height=20,
                                        wrap=WORD,state=DISABLED,
                                        background="black",foreground="white")
        self.textboxMain.yview(END)
        self.textboxMain.grid(row=1,column=0,sticky=N+S+W+E)
        self.textboxMain.bind(sequence="<FocusIn>", func=self.focusEntrybox)

        ''' Offtopic box, this should be easy to disable or enable! '''
        self.textboxOfftopic = ScrolledText(self.frame,width=80,height=10,
                                        wrap=WORD,state=DISABLED,
                                        background="black",foreground="white")
        self.textboxOfftopic.yview(END)
        self.textboxOfftopic.grid(row=0,column=0,sticky=N+S+W+E)
        self.textboxOfftopic.bind(sequence="<FocusIn>", func=self.focusEntrybox)

        ''' Entry box, for typing shit '''
        self.entryboxMessage = StringVar()
        self.entrybox = Entry(self.frame, textvariable=self.entryboxMessage,
                           background="black",foreground="white",
                             state=NORMAL, insertbackground="white")
        self.entrybox.grid(row=2,column=0,sticky=E+W)
        self.entrybox.bind(sequence="<KeyRelease>",  func=self.entryboxKeypress)
        self.entrybox.bind("<MouseWheel>",    func=self.textboxMainScroll)
        self.entrybox.bind("<Button-4>",      func=self.textboxMainScroll)
        self.entrybox.bind("<Button-5>",      func=self.textboxMainScroll)
        #self.widget.bind(sequence="<Up>",   func=self.browseHistory)
        #self.widget.bind(sequence="<Down>", func=self.browseHistory)
        self.entrybox.focus_set()
        self.entryboxHide = False
        self.entrybox.config(show='')
        
        ''' Player box, for showing who's around!'''
        self.playerbox = Listbox(self.frame,background="black",foreground="white")
        self.playerbox.grid(row=0,column=1,rowspan=3,sticky=N+S)

    def displayMain(self,message):
        self.textboxMain.config(state=NORMAL)
        self.textboxMain.insert(END,message)
        self.textboxMain.insert(END,'\n')
        self.textboxMain.config(state=DISABLED)
        self.textboxMain.yview(END)
    def displayOfftopic(self,message):
        self.textboxOfftopic.config(state=NORMAL)
        self.textboxOfftopic.insert(END,message)
        self.textboxOfftopic.insert(END,'\n')
        self.textboxOfftopic.config(state=DISABLED)
        self.textboxOfftopic.yview(END)

    def entryboxKeypress(self,event):
        ''' Handles the input on entrybox. Slightly hacky, maybe..! '''
        print "emsg:",self.entryboxMessage.get()
        if   event.keysym == "BackSpace" and len(self.entryboxMessage.get()) == 0 and self.entryboxTyping:
            self.write("pnt")
            self.entryboxTyping = False
        elif event.keysym == "Return":
            if self.entryboxHide: self.write("msg %s"%(sha.sha(self.entryboxMessage.get()).hexdigest()))
            else:                 self.write("msg %s"%(self.entryboxMessage.get()))
            self.entryboxMessage.set("")
            self.entryboxTyping = False
        elif len(self.entryboxMessage.get()) >= 1 and not self.entryboxTyping:
            self.write("pit")
            self.entryboxTyping = True

    
    def textboxMainScroll(self,event):
        pass
    def textboxOfftopicScroll(self,event):
        pass

    def write(self,message):
        if self.connection: self.connection.write(message)
        
    def stop(self):
        print "Stopping.."

    def focusEntrybox(self,args):
        print "Focus"