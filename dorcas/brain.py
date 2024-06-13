# Build-in modules
from collections import deque
import logging
import sys
import os
import time
import arrow
import json
import random

# PIP-installed modues
from singleton_decorator import singleton

# Project modules
from dorcas.sensation import Sensation
from dorcas.sense.mqtt import Mqtt
from dorcas.sense.journal import Journal
from dorcas.sense.time import Cronoception, duration_to_str
from dorcas.sense.door import Doorception

from dorcas.responder.security import Security
from dorcas.responder.time import Time
from dorcas.responder.instrumentation import Instrumentation
from dorcas.responder.temperature import Temperature
from dorcas.responder.doormonitor import DoorMonitor
from dorcas.responder.muteswitch import MuteSwitch
from dorcas.responder.greeter import Greeter
from dorcas.responder.muser import Muser

from dorcas.worker.mqttclient import MqttClient
from dorcas.worker.voice import Voice
from dorcas.worker.audio import Audio
from dorcas.worker.thespian import Thespian
from dorcas.worker.eyes import Eyes
from dorcas.database import DB

log = logging.getLogger(os.path.basename(sys.argv[0]))


@singleton
class Brain:

    # Prevent flooding
    MaxQueuedSensations = 3

    def __init__(self, config, mute_mqtt):
        self._state = {"mute_mqtt": mute_mqtt, "arrival": False}
        self.config = DB().config(config)
        self.set_silence(self.config.mute_switch)
        log.info(f"using config {config} ==> {self.config}")
        assert self.config
        self.sensations = deque()

        # Config some singletons with self
        self.workers = [
            MqttClient(self),
            Voice(self),
            Audio(self),
            Thespian(self),
            Eyes(self),
        ]

        self.responders = [
            Security(self),
            Time(self),
            Instrumentation(self),
            Greeter(self),
            Muser(self),
            Temperature(self),
            DoorMonitor(self),
            MuteSwitch(self),
        ]

        self.senses = [
            Mqtt(self),             # primary sense of the world is via MQTT
            Journal(self),          # watch system logs for interesting activity
            Cronoception(self),     # notice the passage of time
            Doorception(self),      # notice open doors
        ]

        self.set('boot_time', arrow.now())

    @property
    def state(self):
        self._state['uptime'] = (arrow.now() - self._state['boot_time']).seconds
        self._state['random'] = random.random()
        return self._state

    def uptime(self):
        return duration_to_str(arrow.now() - self.get('boot_time'))

    def get(self, var, default=None):
        value = self.state.get(var)
        return value if value else default

    def set(self, var, value, overwrite=True, diagnostic_level=logging.DEBUG):
        old = self._state.get(var)
        self._state[var] = value
        log.log(diagnostic_level, f"Brain.set {var}={value} (old={old})")
        return old

    def experience(self, sensation):
        # thread safe (I hope!)
        if len(self.sensations) < self.MaxQueuedSensations:
            self.sensations.append(sensation)

    def stop(self):
        self.halt = True

    def run(self):
        """A blocking function that runs the show"""
        start_message = {
            "system_time": str(self.get('boot_time')), 
        }
        MqttClient().publish("nh/status/res", "Restart")
        self.handle_sensation(Sensation("nh/urchin/start", json.dumps(start_message)))
        for thing in self.workers + self.senses:
            thing.start()

        self.halt = False
        while not self.halt:
            while len(self.sensations) > 0:
                self.handle_sensation(self.sensations.popleft())
            time.sleep(self.get("tick_time", 0.5))
        stop_message = {
            "system_time": str(self.get('boot_time')), 
            "uptime_text": self.uptime(),
            "uptime": self.get("uptime"),
        }
        self.handle_sensation(Sensation("nh/urchin/stop", json.dumps(stop_message)))
        time.sleep(1.0)
        MqttClient().publish("nh/status/res", "Terminated")

        log.debug("requesing things stop")
        for thing in self.senses + self.workers:
            thing.stop()

        log.debug("waiting for things to stop")
        for sense in self.senses + self.workers:
            thing.wait()

        log.debug("Brain.run END")

    def handle_sensation(self, sensation):
        urges = list()
        if sensation.topic.startswith("nh/donationbot/"):
            log.info(f"sense: {sensation}")
        else:
            log.debug(f"sense: {sensation}")
        for responder in self.responders:
            urges.extend(responder(sensation))
        # TODO: be more sophisticated about this.  For now, just perform the most urgent one
        if len(urges) > 0:
            selection = sorted(urges, key=lambda x: x.priority, reverse=True)[0]
            selection.perform()

    def door_ids(self):
        return [x for x in self._state.keys() if x.startswith("door_")]

    def set_silence(self, new):
        assert type(new) is bool
        log.info(f"set_silence({new})")
        self._state["silence"] = new
        self._state["last_utterance"] = None
        self.config.mute_switch = new
        DB().session.commit()
