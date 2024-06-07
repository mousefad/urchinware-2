# Built-in python modules

# PIP-installed modules

# Project modules
from dorcas.sense import Sense
from dorcas.database import *
from dorcas.worker.mqttclient import MqttClient


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


