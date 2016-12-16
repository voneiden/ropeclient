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

import utils.crypt
from pony.orm import PrimaryKey, Required, Optional, Set, db_session
from models.database import db


class Universe(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 128, unique=True)
    places = Set("Place")
    beings = Set("Being")
    things = Set("Thing")

    password = Optional(str, 64)
    salt = Optional(str, 64)
    god_accounts = Set("Account")
    offtopics = Set("Offtopic")

    @classmethod
    @db_session
    def create(cls, name, owner, password=None):
        """

        :param name: Name of the universe
        :param owner: Account of the universe owner
        :param password: Password, or none
        :type name: str
        :type owner: models.account.Account
        :type password: str
        :return:
        """

        universe = cls(name=name)
        if password:
            universe.salt = utils.crypt.generate_salt()
            universe.password = utils.crypt.hash(password, universe.salt)
        universe.god_accounts.add(owner)