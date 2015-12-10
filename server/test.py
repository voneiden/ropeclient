import unittest

class TestEverything(unittest.TestCase):
    from models.database import db
    db.bind("sqlite", "database_test.sqlite", create_db=True)
    
    from models.account import *
    from models.universe import *
    from models.place import *
    from models.things import *
    from models.abstract import *

    db.generate_mapping(create_tables=True)


    # Create test universe
    import os
    testverse_password = os.urandom(64)
    testverse_salt = os.urandom(64)
    testverse = Universe(name="Testverse", password=testverse_password, salt=testverse_salt)
    
    # Create test account
    testaccount = Account(name="Testaccount", password=testverse_password, salt=testverse_salt)
    
    # Create test place
    testplace = Place(universe=testverse,
                      description="Long description "*10000)


