from dorcas.urge import Urge
from dorcas.worker.mqttclient import MqttClient

class Publish(Urge):
    def __init__(self, topic, message, cause, priority=Urge.Normal, state=dict()):
        super().__init__(cause, priority, state)
        self.topic = topic
        self.message = message

    def __repr__(self):
        return f"Publish(topic={self.topic!r}, message={self.message!r}, cause={self.cause!r}, priority={self.priority}, state={self.state!r})"

    def perform(self):
        MqttClient().publish(self.topic, self.message)

