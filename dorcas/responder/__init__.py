# Built-in modules
import logging
import sys
import os
from abc import ABC, abstractmethod


log = logging.getLogger(__name__)


class Responder(ABC):
    """Experiences Sensations, produces Urges."""

    def __init__(self, brain):
        self.brain = brain

    @abstractmethod
    def __call__(self, sensation):
        """Returns a list of Urge objects."""
        pass
