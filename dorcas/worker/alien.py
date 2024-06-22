# Build-in modules
import os
import sys
import logging
import time
import threading
from math import exp

# PIP-installed modules
from singleton_decorator import singleton
from gpiozero import LED

# Project modules
from dorcas.worker import ServoFader


log = logging.getLogger(__name__)


@singleton
class Alien(ServoFader):
    """For making the alien chest burser servo activate"""

    Pin = 27
    ShowPos = 1000
    HidePos = 1500

    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        super().__init__(
            self.Pin,
            min(self.ShowPos, self.HidePos),
            max(self.ShowPos, self.HidePos),
            default_duration=0.25,
            default_steps_per_second=100,
        )
        self.brain = brain
        self.set(self.HidePos)

    def start(self):
        pass

    def stop(self):
        pass

    def wait(self):
        pass

    def show(self, duration=None, bg=True):
        self.fade_to(self.ShowPos, duration)
        if not bg:
            self.thread.join()
            self.thread = None

    def hide(self, duration=None, bg=False):
        self.fade_to(self.HidePos, duration)
        if not bg:
            self.thread.join()
            self.thread = None
