# Build-in modules
import os
import sys
import logging
import time
import threading
from math import exp

# PIP-installed modules
from singleton_decorator import singleton

# Project modules
from dorcas.worker import LedFader


log = logging.getLogger(__name__)


@singleton
class Eyes(LedFader):
    """For making the eyes glow"""
    Pin = 17 

    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        super().__init__(self.Pin)
        self.brain = brain 
        self.set(0)

    def start(self):
        pass

    def stop(self):
        pass

    def wait(self):
        pass
