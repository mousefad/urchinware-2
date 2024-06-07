from dorcas.urge import Urge
from dorcas.worker.mqttclient import MqttClient

class Publish(Urge):
    def __init__(self, topic, message, priority=Urge.Normal, state=dict()):
        super().__init__(priority, state)
        self.topic = topic
        self.message = message

    def __repr__(self):
        return f"Publish(topic={self.topic!r}, message={self.message!r}, priority={self.priority})"

    def perform(self):
        MqttClient().publish(self.topic, self.message)

