#!/usr/bin/env python
"""
    Login controller for ropeclient server
    Copyright (C) 2010 - 2016  Matti Eiden

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
"""
import logging

from controllers.base import BaseController
from utils.decorators.commands import Commands, dynamic_command
from utils.decorators.requirements import *
from utils.autonumber import AutoNumber
from pony.orm import db_session, commit, select, get, MultipleObjectsFoundError
from models.things import Thing, Being
from models.account import Account
from models.universe import Universe
from models.abstract import Utterance, Offtopic

from utils.dice import Dice

import re
import datetime

class State(AutoNumber):
    normal = ()


class PlayController(BaseController):

    def __init__(self, connection, runtime, account_id, universe_id):
        """
        MenuController is used for the main menu where the user can choose which universe to join or
        create a new universe.

        :param connection: Connection of the user
        :param account: Account of user user
        :param universe: Universe where the play happens
        :type connection: main.Connection
        :type account: models.account.Account
        :type universe: models.universe.Universe
        :return:
        """
        BaseController.__init__(self, connection, runtime)
        self.account_id = account_id
        self.universe_id = universe_id
        self.state = State.normal

        #self.thing = get(account for account in self.universe.things if account == self.account)
        #if not self.thing:
        #    self.thing = Thing(account=self.account, universe=self.universe)
        #    # TODO place!

        runtime.add_controller(universe_id, account_id, self)

        self.being_id = None
        self.start()

    @property
    def account(self):
        if self.account_id:
            return Account[self.account_id]
        else:
            return None

    @property
    def universe(self):
        if self.universe_id:
            return Universe[self.universe_id]
        else:
            return None

    @property
    def being(self):
        if self.being_id:
            return Being[self.being_id]
        else:
            return None


    @property
    def ghost(self):
        return self.universe.beings.select(lambda being: being.ghost is True and being.account == self.account).first()




    @db_session
    def start(self):
        # Send player list
        account_names = [Account[controller.account_id].name for controller in self.runtime.find_controllers(self.universe_id)]
        self.send_playerlist(account_names)
        self.send_clear()

        # Send offtopics
        offtopic_history = self.universe.offtopics.select(lambda x: True)[:100]
        if len(offtopic_history):
            self.send_offtopic(*offtopic_history)

        # TODO Universe send offtopic joined

        # TODO either attach to previous being or do_detach to become a ghost
        self.do_detach()
        self.do_look()

    #TODO: db session?
    def handle(self, message={}):
        print("Handle message", message)
        try:
            return BaseController.handle(self, message)
        except KeyError:
            pass

        key = message.get("k")
        value = message.get("v", "")



        # Messages processed in standard mode check only for startswith commands, otherwise default to default action
        if key == "msg":
            # Look for a matching startswith handler
            for startswith_command in self._startswith.keys():
                if value.startswith(startswith_command):
                    print("Startswith command found", startswith_command)
                    cleaned_value = re.sub(re.escape(startswith_command), "", value, 1, re.IGNORECASE)
                    return self._startswith[startswith_command](self, startswith=startswith_command, value=cleaned_value)

            return self._commands.get("default")(self, value=value)

        # TODO command mode
        elif key == "cmd":
            tokens = value.split(" ")
            command = tokens[0].lower()
            print("Command", command)
            print("Self.commands", self._commands)
            raise NotImplementedError


        """

        # Look for a matching handler
        if command in self._commands:
            print("Command found", command)
            return self._commands[command](self, command, tokens[1:])



        # Look for a matching dynamic command handler
        for dcommand in self._dynamic_commands:
            try:
                return dcommand(self, command, tokens[1:])
            except NotImplementedError:
                continue
        """
        return self.syntax_error()

    @Commands("detach")
    @db_session
    def do_detach(self):
        # Get rid of current being
        # TODO
        account = self.account
        universe = self.universe
        place = [place for place in universe.places][0]

        # "Attach" to ghost
        ghost = self.ghost
        if ghost is None:
            ghost = Being(
                name="Ghost of {}".format(account.name),
                universe=universe,
                place=place,
                account=account,
                ghost=True
            )
            commit()

        self.being_id = ghost.id




    @Commands("default", "say")
    @is_being
    @db_session
    def do_say(self, command=None, startswith=None, tokens=None, value=""):
        print("Player would like to say:", value)
        value = Dice.find_and_roll(value)
        being = self.being
        place = being.place
        heard_by = [place_being for place_being in place.beings]
        text = '{{me}} says,"{content}"'.format(content=value)
        utterance = Utterance(
            text=text,
            being=being,
            heard=heard_by,
            timestamp=datetime.datetime.now()
        )
        print("OK", heard_by)
        heard_by_ids = [place_being.id for place_being in heard_by]
        for controller in self.runtime.find_controllers(self.universe_id):
            print("Account id", controller.account_id, "in", heard_by_ids)
            if controller.being_id in heard_by_ids:
                controller.send_ontopic(utterance)

    @Commands("offtopic", startswith=["("])
    @db_session
    def do_offtopic(self, command=None, startswith=None, tokens=None, value=""):
        print("Player would like to offtopic:", value)
        value = Dice.find_and_roll(value)
        offtopic = Offtopic(
            text=value,
            account=Account[self.account_id],
            universe=Universe[self.universe_id],
            timestamp=datetime.datetime.now()
        )

        for controller in self.runtime.find_controllers(self.universe_id):
            controller.send_offtopic(offtopic)


    @gamemaster
    def do_create(self, command=None, startswith=None, tokens=None, value=""):
        pass

    @Commands("move")
    def do_move(self, command=None, startswith=None, tokens=None, value=""):
        pass

    #@dynamic_command
    def do_move_dynamic(self, command=None, startswith=None, tokens=None, value=""):
        pass

    @Commands("look")
    @db_session
    def do_look(self, **kwargs):
        if self.being_id is not None:
            being = Being[self.being_id]
            place = being.place
            place_being_names = [place_being.name for place_being in place.beings]
            buf = [
                place.name,
                place.description,
                ", ".join(place_being_names)
            ]
            self.send_ontopic(*buf)

    @Commands("roll", startswith=["!"])
    def do_roll(self, command=None, startswith=None, tokens=None, value=""):
        pass

    def stop(self):
        self.runtime.remove_controller(self.universe_id, self.account_id)
