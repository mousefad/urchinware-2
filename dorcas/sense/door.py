# Built-in python modules
import os
import sys
import logging
import time

# PIP-installed modules
import arrow

# Project modules
from dorcas.sensation import Sensation
from dorcas.sense import ThreadedHalterSense
from dorcas.sense.time import duration_to_str
from dorcas.worker.mqttclient import MqttClient

log = logging.getLogger(__name__)


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
        door = self.brain.get("door_1")
        if not door:
            return
        try:
            if not door["open"]:
                return
            if door["notifications_left"] <= 0:
                return
            now = arrow.now()
            if (
                now - door["last_notified"]
            ).seconds >= self.brain.config.door_open_seconds:
                time_open = duration_to_str(now - door["open_since"])
                self.brain.experience(
                    Sensation(
                        self.brain.topic("door-left-open"),
                        f"{door['name']} has been open for {time_open}",
                    )
                )
                door["last_notified"] = now
                door["notifications_left"] -= 1
        except:
            log.error(f"Doorception problem", exc_info=True)
