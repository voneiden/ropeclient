#!/usr/bin/env python
"""
    Setup functions for the server instance. Also development environment stuff.

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

from pony.orm import sql_debug, db_session
from models.database import db
from models.account import *
from models.universe import *
from models.place import *
from models.things import *
from models.abstract import *


def mapping():
    db.generate_mapping(create_tables=True)


@db_session
def setup_development_environment():
    """
    Setups a development environment by enabling SQL debug and generates some default objects

    :return:
    """
    import hashlib

    # Enable SQL debug
    sql_debug(True)

    # Create test user
    test_name = "test"
    test_salt = "salt"
    test_password = hashlib.sha256("{name}{salt}".format(name=test_name, salt=test_salt).encode("utf8")).hexdigest()
    account = Account(name=test_name,
                      password=test_password,
                      salt=test_salt)

    # Create test universe
    universe = Universe.create(name="Test universe", owner=account)
    place = Place(
        name="Void",
        description="You are in the void",
        universe=universe
    )





