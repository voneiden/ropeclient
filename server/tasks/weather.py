import math
from utils.autonumber import AutoNumber


import transitions


import math
class WeatherModel(object):
    pass

class TemperateWeatherModel(WeatherModel):
    pass





# sin(x*(2*pi) / 365)*30 + sin(x*(2*pi))*8+10
class Weather(object):
    """
    Weather is a state machine
    """
    def __init__(self, weather_model):
        self.machine = transitions.Machine(model=weather_model)


    # fascinating