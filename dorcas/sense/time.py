# Built-in python modules
import time
import json
import datetime
import random
from collections import namedtuple

# PIP-installed modules
import arrow
import cachetools.func
from sqlalchemy import or_, and_

# Project modules
from dorcas.sensation import Sensation
from dorcas.sense import ThreadedHalterSense
from dorcas.database import *


log = logging.getLogger(os.path.basename(sys.argv[0]))

class Cronoception(ThreadedHalterSense):
    """The Time Sense annouces the passing of time, including details of special days."""
    WeekdayNames = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
    }
    MonthNames = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
    }
    BoredomSettings = namedtuple("BoredomSettings", ["min", "amt"])
    def __init__(self, brain):
        super().__init__(brain)
        self.interval = self.brain.config.time_interval
        self.special_day = None
        self.last_date = None
        self.last_minute = None

    @property
    @cachetools.func.ttl_cache(ttl=23)
    def boredom_settings(self):
        return Cronoception.BoredomSettings(self.brain.config.boredom_minimum, self.brain.config.boredom_minimum)

    @property
    @cachetools.func.ttl_cache(ttl=23)
    def door_open_time(self):
        return self.brain.config.door_open_time

    def run(self):
        log.debug("Cronoception.run")
        while not self.halt:
            self.tick(arrow.now().datetime)
            time.sleep(self.interval)
        log.debug("Cronoception.run END")

    def tick(self, now):
        self.boredom(now)
        if now.minute == self.last_minute:
            return
        self.last_minute = now.minute
        self.clock(now)

    def boredom(self, now):
        # Boredom
        last_utterance = self.brain.get('last_utterance')
        if last_utterance is not None:
            seconds_since_utterance = (arrow.now() - last_utterance).seconds 
            if seconds_since_utterance > self.boredom_settings.min:
                if random.random() < self.boredom_settings.amt:
                    self.brain.experience(Sensation("urchin/bored", seconds_since_utterance))

    def open_door(self):
        open_doors = filter(lambda x: x.get("open") and x.get('open_since') and not x.get("notified"), self.brain.doors())
        log.info(f"un-notified open doors: {open_doors}")
        for id, deets in open_doors.items():
            open_dur = (arrow.now() - deets['open_since']).seconds
            if open_dur > self.door_open_time:
                self.brain.experience(Sensation("urchin/bored", seconds_since_utterance))

    def clock(self, now):
        self.update_date(now.date())
        data = {
                "year": now.year,
                "month": now.month,
                "dom": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "day_name": Cronoception.WeekdayNames[now.weekday()],
                "month_name": Cronoception.MonthNames[now.month],
                "special_day": self.special_day,
        }
        self.brain.experience(Sensation("time/now", json.dumps(data)))
        self.brain.set("special_day", self.special_day)
        if now.time() < datetime.time(hour=4):
            day_period = "night"
        elif now.time() < datetime.time(hour=12):
            day_period = "morning"
        elif now.time() < datetime.time(hour=17, minute=45):
            day_period = "afternoon"
        elif now.time() < datetime.time(hour=22):
            day_period = "evening"
        else:
            day_period = "night"
        self.brain.set("day_period", day_period)

    def update_date(self, date):
        if date == self.last_date:
            return
        self.last_date = date
        sd = DB().session.query(SpecialDay).filter(and_(SpecialDay.month==date.month, SpecialDay.day==date.day, or_(SpecialDay.year==None, SpecialDay.year==date.year))).first()
        self.special_day = sd.name if sd else None


def duration_to_str(dur):
    hours = dur.seconds // 3600
    minutes = (dur.seconds-(hours*3600)) // 60
    seconds = dur.seconds % 60
    a = list()
    if dur.days > 0:
        a.append(f"{dur.days} day{'s' if dur.days > 1 else ''}")
    if hours > 0:
        a.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        a.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0:
        a.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    return ', '.join(a)
    
