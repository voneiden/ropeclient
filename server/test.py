import unittest
from pony.orm import db_session
from controllers.base import BaseController
from models.database import db
from models.account import *
from models.universe import *
from models.place import *
from models.things import *
from models.abstract import *

import string
import random
import hashlib

class TestEverything(unittest.TestCase):
    db.bind("sqlite", "database_test.sqlite", create_db=True)
    db.generate_mapping(create_tables=True)

    @db_session
    def test_all(self):


        # Create test universe
        import os
        testverse_password = ''.join(random.choice(string.ascii_uppercase) for i in range(64))
        testverse_salt = ''.join(random.choice(string.ascii_uppercase) for i in range(64))
        testverse_crypted_password = hashlib.sha256((testverse_password + testverse_salt).encode("utf8")).hexdigest()
        testverse = Universe(name="Testverse", password=testverse_crypted_password, salt=testverse_salt)

        # Create test account
        testaccount = Account(name="Testaccount", password=testverse_password, salt=testverse_salt)

        # Create test place
        testplace = Place(name="Test place",
                          universe=testverse,
                          description="Long description "*10000)

    @db_session
    def test_basecontroller(self):
        # Create a test offtopic message
        testverse = Universe(name="Testverse Basecontrol")
        class MockConnection(object):
            def send(self, obj):
                pass

        base = BaseController(MockConnection())
        base.send_offtopic("Text message")

        offtopic = Offtopic(text="Test message",
                            universe=testverse)
        base.send_offtopic(offtopic)


if __name__ == '__main__':
    unittest.main()