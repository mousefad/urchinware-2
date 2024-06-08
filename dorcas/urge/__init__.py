# Built-in modules
import logging
import sys
import os
from abc import ABC, abstractmethod


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Urge(ABC):
    # Priorities
    Low = 0
    Normal = 10
    High = 20

    """Urges are a desire to perform an action, e.g. the urge to say something naughty."""
    def __init__(self, cause, priority=Normal, state=dict()):
        self.cause = cause
        self.priority = priority
        self.state = state

    def __lt__(self, other):
        return self.priority < other.priority

    @abstractmethod
    def perform(self):
        """must implement the method to perform the urge here."""
        pass


