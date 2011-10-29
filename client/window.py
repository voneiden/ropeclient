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
from Tkinter import N, S, E, W, WORD, DISABLED, NORMAL, END, BOTH, YES, SUNKEN, RAISED,GROOVE
from Tkinter import Entry, Listbox, StringVar, Tk, Frame, TclError
from ScrolledText import ScrolledText
import time
import re
from hashlib import sha256

class Window(object):

    def __init__(self):
        """
        Tkinter for speedy development!
        We have a root, and then we have a grid over the root, works very nice!
        """
        
        f = open('connect.txt','r')
        self.host = f.read().strip()
        f.close()
        

        # Initialize some variables
        self.connection = None
        
        self.entryboxTyping = False

        # Create the root
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.title('Ropeclient')

        # Create the frame and define position 0, 0 as the main expander
        self.frame = Frame(self.root, background="black")
        self.frame.pack(fill=BOTH, expand=YES)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Main text box
        self.textboxMain = ScrolledText(self.frame, width=80, height=20,
                                        wrap=WORD, state=DISABLED,
                                        background="black", foreground="white")
        self.textboxMain.yview(END)
        self.textboxMain.grid(row=1, column=0, sticky=N+S+W+E)
        self.textboxMain.bind(sequence="<FocusIn>", func=self.focusEntrybox)

        ''' Offtopic box, this should be easy to disable or enable! '''
        self.textboxOfftopic = ScrolledText(self.frame, width=80, height=10,
                                        wrap=WORD, state=DISABLED,
                                        background="black", foreground="white")
        self.textboxOfftopic.yview(END)
        self.textboxOfftopic.grid(row=0, column=0, sticky=N+S+W+E)
        self.textboxOfftopic.bind(sequence="<FocusIn>", func=self.focusEntrybox)

        ''' Entry box, for typing shit '''
        self.entryboxMessage = StringVar()
        self.entrybox = Entry(self.frame, textvariable=self.entryboxMessage,
                           background="black", foreground="white",
                             state=NORMAL, insertbackground="white")
        self.entrybox.grid(row=2,column=0,sticky=E+W)
        self.entrybox.bind(sequence="<KeyRelease>", func=self.entryboxKeypress)
        self.entrybox.bind("<MouseWheel>", func=self.textboxMainScroll)
        self.entrybox.bind("<Button-4>", func=self.textboxMainScroll)
        self.entrybox.bind("<Button-5>", func=self.textboxMainScroll)
        self.entrybox.bind("<Control-a>",func=self.entrySelectAll)
        #self.widget.bind(sequence="<Up>", func=self.browseHistory)
        #self.widget.bind(sequence="<Down>", func=self.browseHistory)
        self.entrybox.focus_set()
        self.entryboxHide = False
        self.entrybox.config(show='')

        ''' Player box, for showing who's around!'''
        self.playerbox = Listbox(self.frame,background="black",foreground="white")
        self.playerbox.grid(row=0,column=1,rowspan=3,sticky=N+S)
        
        # Colors that have been loaded!
        self.usedColors = []
        self.colors = {'default': 'gray'}
        self.dicetags = {}
        
        self.history = []
        self.historypos = 0
        
    # TODO update
    def display(self,message,timestamp=None,offtopic=False):
          
           
        message = self.clickParse(message)
        message = self.diceParse(message)
        message = self.colorParse(message)
        
         
        if timestamp != None: 
            if '\n' in message:pass
            else:  message = "[%s] %s"%(time.strftime("%H:%M",time.localtime(timestamp)), message) 
        
        message = self.colorResetParse(message)
        message = self.colorTags(message)
        
        print "Displaying",message,"with timestamp",timestamp
        if offtopic:
            self.displayOfftopic(message)
        else:
            self.displayMain(message)

    def displayMain(self,message):
        self.textboxMain.config(state=NORMAL)
        for tag,text in message:
            self.textboxMain.insert(END,text,tag)
        self.textboxMain.insert(END,'\n')
        self.textboxMain.config(state=DISABLED)
        self.textboxMain.yview(END)

    def displayOfftopic(self,message):
        self.textboxOfftopic.config(state=NORMAL)
        for tag,text in message:
            self.textboxOfftopic.insert(END,text,tag)
        self.textboxOfftopic.insert(END,'\n')
        self.textboxOfftopic.config(state=DISABLED)
        self.textboxOfftopic.yview(END)

    def entrySelectAll(self,event):
        print "ctrl+a"
        self.entrybox.selection_range(0, END)
        return "break"
    def entryboxKeypress(self,event):
        ''' Handles the input on entrybox. Slightly hacky, maybe..! '''
        message = self.entryboxMessage.get()
        if   event.keysym == "BackSpace" and len(self.entryboxMessage.get()) == 0 and self.entryboxTyping:
            self.write("pnt")
            self.entryboxTyping = False
        elif event.keysym == "Return": #and len(message) > 0:
            if self.entryboxHide:
                self.write("msg %s"%(sha256(message+'r0p3s4lt').hexdigest()))
                self.entryboxHide = False
                self.entrybox.config(show='')
            else:
                self.write("msg %s"%(message))
                self.history.append(message)
                if len(self.history) > 10:
                    self.history.pop(0)
            self.entryboxMessage.set("")
            self.entryboxTyping = False
        elif event.keysym == "Up":
            self.historyUp()
        elif event.keysym == "Down":
            self.historyDown()
            
        elif len(self.entryboxMessage.get()) >= 1 and not self.entryboxTyping:
            self.write("pit")
            self.entryboxTyping = True
  
        #print event.keysym
    def entryboxSet(self,command):
        self.entryboxMessage.set(command)
        self.entrybox.icursor(END)
        
        
    def historyUp(self):
        if len(self.history) == 0: return
        self.historypos += 1
        print "UP",self.historypos
        if self.historypos > len(self.history):
            self.historypos = len(self.history)
        print self.history
        print self.historypos
        self.entryboxSet(self.history[-self.historypos])
    
    def historyDown(self):
        if len(self.history) == 0: return
        self.historypos -= 1
        if self.historypos < 0: self.historypos = 0
        if self.historypos == 0:
            self.entryboxSet('')
        else:
            self.entryboxSet(self.history[-self.historypos])
    def textboxMainScroll(self,event):
        print dir(event)
        print event.keycode
        print event.delta
        scroll = event.delta / 10
        self.textboxMain.yview('scroll', -scroll, 'units')
        

    def textboxOfftopicScroll(self,event):
        pass

    def write(self,message):
        if self.connection:
            self.connection.write(message)

    def stop(self):
        print "Stopping.."
        self.reactor.stop()

    def focusEntrybox(self,args):
        print "Focus"
        self.entrybox.focus_set()
        
    def playerboxUpdate(self):
        ''' playerlist[playername] = [bTyping,bCharname?] '''
        players = self.playerlist.keys()
        players.sort()
        
        self.playerbox.delete(0, END)
        for player in players:
            print "typecheck",player,self.playerlist[player]
            pline = "{typing}{name} {charname}".format(
                typing="*" if self.playerlist[player][0] == "1" else "",
                name=player,
                charname="" if self.playerlist[player][1] == '-1' else "({0})".format(self.playerlist[player][1]))
                
            #if self.playerlist[player][0] == "1": 
            #    self.playerbox.insert(END, "*%s (%s)"%(player,self.playerlist[player][1]))
            #else:
            self.playerbox.insert(END, pline)
       
    def clickParse(self,message):
        regex = '\$\(clk2cmd\:.+?\)'
        for clk2cmd in re.finditer(regex,message):
            cmd = clk2cmd.group()
            tok = cmd.split(':')[1].split(';')
            tag = tok[0]
            color = tok[1]
            if color in self.colors:
                color = self.colors[color]
            command = tok[2]
            text = tok[3][:-1]
            if tag not in self.usedColors:
                self.usedColors.append(tag)
            try:
                self.textboxMain.tag_config(tag,foreground=color)
                self.textboxOfftopic.tag_config(tag,foreground=color)
            except TclError:
                self.textboxMain.tag_config(tag,foreground="white")
                self.textboxOfftopic.tag_config(tag,foreground="white")
            
            self.textboxMain.tag_bind(tag,"<Button-1>",lambda(event): self.entryboxSet(command))
            self.textboxOfftopic.tag_bind(tag,"<Button-1>",lambda(event): self.entryboxSet(command))
            message = message.replace(cmd,"<%s>%s<reset>"%(tag,text),1)
        return message
    def diceParse(self,message):
        regex = '\$\(dice\=.+?\)'
        print "Searching for dice",message
        for dice in re.finditer(regex,message):
            print "FOUND DICE"
            dice = dice.group()
            values = dice.split('=')[1][:-1].split(';')
            tag = "dice"+str(time.time())
            self.usedColors.append(tag)
            self.dicetags[tag] = [0,values[0],values[1]]
            
            self.textboxMain.tag_config(tag,foreground="green",borderwidth=1,relief=GROOVE)
            self.textboxOfftopic.tag_config(tag,foreground="green",borderwidth=1,relief=GROOVE)
            self.textboxMain.tag_bind(tag,"<Button-1>", lambda(event): self.toggleDice(event,tag))
            self.textboxOfftopic.tag_bind(tag,"<Button-1>", lambda(event): self.toggleDice(event,tag))
            message = message.replace(dice,"<%s>%s<reset>"%(tag,values[0]))
            
        return message
            
    def colorResetParse(self,message):
        colorstack = []
        fallback = "<%s>"%self.colors['default']#'<gray>'
        regex = '\<.*?\>'
        print "Pre-parse:",message
        for color in re.finditer(regex,message):
            color = color.group()
            if color == '<reset>':
                try:
                    colorstack.pop()
                    replace = colorstack[-1]
                except:
                    replace = fallback
                message = message.replace(color,replace,1)
                
            else:
                colorstack.append(color)
        print "Finished:",message
        return message
            
    def colorTags(self,message):
        regex = '\<.*?\>'
        colors = [self.colors['default']]+[color[1:-1] for color in re.findall(regex,message)]
        parts  = re.split(regex,message)
        
        print "Colors:",colors
        print "Parts:",parts
        message = []
        for i,color in enumerate(colors):
            if color not in self.usedColors:
                self.usedColors.append(color)
                try:
                    self.textboxMain.tag_config(color,foreground=color)
                    self.textboxOfftopic.tag_config(color,foreground=color)
                except TclError:
                    self.textboxMain.tag_config(color,foreground="white")
                    self.textboxOfftopic.tag_config(color,foreground="white")

            message.append([(color,),parts[i]]) 
        print message
        return message

    def toggleDice(self,event,tag):
        widget = event.widget
        ranges = widget.tag_ranges(tag)
        if self.dicetags[tag][0]: 
            text = self.dicetags[tag][1]
        else: 
            text = self.dicetags[tag][2]
        self.dicetags[tag][0] = not self.dicetags[tag][0]
        
        widget.config(state=NORMAL)
        widget.delete(ranges[0],ranges[1])
        widget.insert(ranges[0],text,tag)
        widget.config(state=DISABLED)
       

    def colorParse(self,message):
        for definedColor in self.colors.keys():
            message = message.replace("<%s>"%definedColor,"<%s>"%self.colors[definedColor])
            
        regex = '\".+?\"'
        for talk in re.finditer(regex,message):
            talk = talk.group()
            message = message.replace(talk,"<%s>%s<reset>"%(self.colors['talk'],talk))
        return message
