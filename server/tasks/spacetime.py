import time

from utils import autonumber
from pony.orm import db_session

from models.universe import Planet

class TimeModes(autonumber.AutoNumber):
    manual = ()


class Spacetime(object):
    """
    Spacetime is really just time management for a universe

    This module aims to provide support for both

    """

    def __init__(self, planet_id, runtime, mode=TimeModes.manual):
        self.planet_id = planet_id
        self.runtime = runtime
        self.mode = mode

        self.state = {}
        self.load_state()
        if self.state.get("mode", None) is None:
            self.state.mode = self.mode

        self.last_update = time.time()

    @db_session
    def load_state(self):
        state = Planet[self.planet_id].spacetime
        if state is not None:
            self.state = state
        else:
            self.state = {}

    @db_session
    def update(self):
        # TODO allow faking the elapsed time
        now = time.time()
        time_elapsed = now - self.last_update

        planet = Planet[self.planet_id]

        # TODO calculate sidereal and orbital angles

        self.last_update = now