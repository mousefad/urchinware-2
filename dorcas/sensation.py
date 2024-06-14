# Build-in modules
import logging
import sys
import os
import arrow
import json


log = logging.getLogger(__name__)


class Sensation:
    def __init__(self, topic, message):
        self.received = arrow.now()
        self.topic = topic
        self.message = message.decode() if type(message) is bytes else str(message)

    @property
    def json(self):
        try:
            return json.loads(self.message)
        except json.decoder.JSONDecodeError:
            return {}

    def __str__(self):
        s = self.topic + " "
        s += self.message
        return s

    def __repr__(self):
        return f"Sensation(topic={self.topic!r}, message={self.message!r})"
