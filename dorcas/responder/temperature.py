import os
import sys
import logging
import re
import statistics
from dorcas.responder import Responder

log = logging.getLogger(os.path.basename(sys.argv[0]))


class Temperature(Responder):
    """This responder doesn't create and urges, but updates the brain state with the temperature of each room, and the median temp"""
    def __init__(self, brain):
        super().__init__(brain)
        self.temperatures = dict()

    def __call__(self, sensation):
        if not sensation.topic.startswith("nh/temperature/"):
            return []
        try:
            room = self.sanitize_room_name(sensation.topic)
            self.temperatures[room] = round(float(sensation.message), 1)
            median = self.median_temperature()
            description = self.temperature_description(median)
            self.brain.set("temperature_median", median)
            self.brain.set("temperature_description", description)
            self.brain.set("temperature_coldest", "%s at %s Celcius" % self.coldest_room())
            self.brain.set("temperature_hottest", "%s at %s Celcius" % self.hottest_room())
        except Exception as e:
            log.exception(f"Temp: while handling temperature {sensation}")
        return []

    def sanitize_room_name(self, s):
        s = re.sub(r"^nh/temperature/", "", s)
        s = re.sub(r"-LLAP", "", s)
        s = re.sub(r"^G5", "", s)
        s = s.split("/")[-1]
        s = re.sub(r"[_-]+", " ", s)
        s = re.sub(r"[A-Z]", lambda x: f" {x.group()}", s)
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"^\s+", "", s)
        if s != "3 D Printing":
            s = "The " + s
        return s
        
    def median_temperature(self):
        return round(statistics.median(self.temperatures.values()), 1)

    def temperature_description(self, t):
        if t < 5:
            return "freezing"
        elif t < 10:
            return "cold"
        elif t < 15:
            return "chilly"
        elif t < 20:
            return "nice"
        elif t < 25:
            return "warm"
        else:
            return "hot"

    def coldest_room(self):
        coldest = (None, None)
        for room, temp in self.temperatures.items():
            if coldest[1] is None or coldest[1] > temp:
                coldest = (room, temp)
        return coldest

    def hottest_room(self):
        hottest = (None, None)
        for room, temp in self.temperatures.items():
            if hottest[1] is None or hottest[1] < temp:
                hottest = (room, temp)
        return hottest

