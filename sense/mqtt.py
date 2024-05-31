# Built-in python modules
import os
import sys
import logging
import json
import re
import time
from collections import namedtuple

# PIP-installed modules
import paho.mqtt.client as mqtt
import coloredlogs
import cachetools.func
from singleton_decorator import singleton

# Project modules
from sensation import Sensation
from sense import Sense
from database import *
from worker.mqttclient import MqttClient


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Mqtt(Sense):
    """The Mqtt Sense creates a sensation for every MQTT message that it observes"""
    def __init__(self, brain):
        super().__init__(brain)

    def start(self):
        log.debug(f"mqtt.start")
        MqttClient().register_receiver(self.brain.experience)

    def stop(self):
        log.debug(f"mqtt.stop")
        MqttClient().unregister_receiver(self.brain.experience)

    def wait(self):
        pass


