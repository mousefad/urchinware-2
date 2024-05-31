# Built-in python modules
import os
import sys
import logging
import re
import time
import json
import datetime
import random
import arrow
import subprocess as sp
from collections import namedtuple

# PIP-installed modules
import arrow
import cachetools.func

# Project modules
from sensation import Sensation
from sense import ThreadedHalterSense
from sense.time import duration_to_str

log = logging.getLogger(os.path.basename(sys.argv[0]))

class Doorception(ThreadedHalterSense):
    def __init__(self, brain):
        super().__init__(brain)
        self.interval = 1.0

    def run(self):
        log.debug("Doorception.run")
        while not self.halt:
            self.tick()
            time.sleep(self.interval)
        log.debug("Doorception.run END")

    def tick(self):
        for id in self.brain.door_ids():
            if id != "door_1":
                continue
            door = self.brain.get(id)
            if door and door.get("open") and door.get("open_since") and not door.get("notified"):
                open_duration = arrow.now() - door.get("open_since")
                open_seconds = open_duration.seconds
                if open_seconds > self.brain.config.door_open_seconds:
                    name = door.get("name")
                    open_dur_desc = duration_to_str(open_duration)
                    self.brain.experience(Sensation("urchin/door-open-warning", f"{name} has been open for {open_dur_desc}"))
                    door["notified"] = True

