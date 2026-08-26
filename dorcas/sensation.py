# Build-in modules
from datetime import datetime
import logging
import sys
import os
import json


log = logging.getLogger(__name__)


class Sensation:
    def __init__(self, topic, message):
        self.received = datetime.now().astimezone()
        self.topic = topic
        self.message = message.decode(errors="ignore") if type(message) is bytes else str(message)

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
