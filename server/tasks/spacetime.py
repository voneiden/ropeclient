import time
import math
import asyncio

from utils import autonumber
from pony.orm import db_session

#import models.universe

#print(dir(models))
from models.universe import Planet


class TimeModes(autonumber.AutoNumber):
    manual = ()





class Spacetime(object):
    """
    Spacetime is really just time management for a universe

    This module aims to provide support for both. Epoch 0 starts at winter

    """
    solar_rise_set_altitude = math.radians(-0.83)

    def __init__(self, planet_id, runtime):
        self.planet_id = planet_id
        self.runtime = runtime

        self.state = {}
        self.load_state()
        #if self.state.get("mode", None) is None:
        #    self.state.mode = self.mode

        self.last_update = time.time()
        self.update()

    @db_session
    def load_state(self):
        state = Planet[self.planet_id].spacetime
        if state is not None:
            self.state = state
        else:
            self.state = {
                "epoch": 0,
                "tilt": 23.5,
                "days_per_year": 365,
                "hours_per_day": 24,
                "declination": 0

            }

    @db_session
    def update(self):
        # TODO allow faking the elapsed time
        now = time.time()
        seconds_since_last_update = now - self.last_update
        seconds_since_last_update = 3600*24*90

        epoch = self.state.get("epoch", 0)
        epoch += seconds_since_last_update / 60 / 60 / self.state.get("hours_per_day", 24)

        planet = Planet[self.planet_id]

        self.last_update = now
        self.state["epoch"] = epoch
        self.state["declination"] = Spacetime.solar_declination(epoch,
                                                                self.state.get("days_per_year", 365),
                                                                self.state.get("tilt", 23.5))
        planet.spacetime = self.state
        loop = asyncio.get_event_loop()
        loop.call_later(5, self.update)
        print("Updated spacetime to", str(self.state))
        print("Localtime at lon0", str(self.localtime(0)))
        print("Solar altitude", math.degrees(self.insolation_multiplier(58, 0)))


    @staticmethod
    def solar_declination(epoch, days_per_year, tilt):
        return -math.cos(epoch * 2 * math.pi / days_per_year) * math.radians(tilt)

    def sun_hour_angle(self, latitude):
        latitude = math.radians(latitude)
        declination = self.state.get("declination", 0)
        return abs(math.acos(
            (math.sin(Spacetime.solar_rise_set_altitude) - math.sin(latitude) * math.sin(declination)) /
            (math.cos(latitude) * math.cos(declination)))
        )*-1

    def hours_per_day(self):
        return self.state.get("hours_per_day", 24)

    def delta_hours(self, longitude):
        """
        :param longitude: [-180, 180]
        :return:
        """
        return longitude / 360 * self.hours_per_day()

    def noon(self):
        return self.state.get("hours_per_day", 24) / 2

    def insolation_multiplier(self, latitude, longitude):
        latitude = math.radians(latitude)
        longitude = math.radians(longitude)
        epoch = self.state.get("epoch", 0)
        local_epoch = epoch + self.delta_hours(longitude)
        noon = self.hours_per_day()
        hour = (local_epoch % 1) * self.hours_per_day()
        hour_angle = ((local_epoch % 1) - 0.5)*2*math.pi
        print("Hour angle", hour_angle)
        declination = self.state.get("declination", 0)

        altitude = math.asin(math.sin(declination) * math.sin(latitude) + math.cos(declination) * math.cos(latitude) * math.cos(hour_angle))
        return max(math.sin(altitude), 0)





    def sunrise_sunset(self, latitude):
        sun_hour_angle = self.sun_hour_angle(latitude)
        print("Sun hour angle is", sun_hour_angle)
        hours_from_noon = sun_hour_angle / (2*math.pi) * self.hours_per_day()
        print("Hours from noon", hours_from_noon)
        noon = self.state.get("hours_per_day", 24) / 2
        return [noon + hours_from_noon, noon - hours_from_noon]

    def localtime(self, longitude):
        epoch = self.state.get("epoch", 0)
        delta_hours = longitude / 360 * self.state.get("hours_per_day", 24)
        local_epoch = epoch + delta_hours
        days_per_year = self.state.get("days_per_year", 365)
        year = int(local_epoch / days_per_year)
        day = int(local_epoch % days_per_year) + 1
        hour = (local_epoch % 1) * self.state.get("hours_per_day", 24)
        return {
            "year": year,
            "day": day,
            "hour": hour,
            "sunrise_sunset": self.sunrise_sunset(58)
        }

