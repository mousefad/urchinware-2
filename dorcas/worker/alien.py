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
from dorcas.worker import PwmFader


log = logging.getLogger(__name__)


@singleton
class Alien(PwmFader):
    """For making the alien chest burser servo activate"""

    PwmChannel = "0"
    ShowPos = 30
    HidePos = 70
    PwmPeriodNs = 20_000_000 # 50Hz
    PwmLowerBoundNs = int(0.030 * PwmPeriodNs)
    PwmUpperBoundNs = int(0.125 * PwmPeriodNs)

    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        super().__init__(
            channel=self.PwmChannel,
            period_ns=self.PwmPeriodNs,
            enable=True,
            fade_time_seconds=0.25,
            steps_per_second=100,
            only_active_while_fading=True,
            lower_bound_duty_ns=self.PwmLowerBoundNs,
            upper_bound_duty_ns=self.PwmUpperBoundNs,
        )
        self.brain = brain
        self.fade_to_percent(self.HidePos)

    def start(self):
        pass

    def stop(self):
        pass

    def wait(self):
        pass

    def show(self, duration=None, bg=True):
        if self.brain.get("silence"):
            log.debug("SILENCED")
            return
        self.fade_to_percent(self.ShowPos, duration)
        if not bg:
            self.thread.join()
            self.thread = None

    def hide(self, duration=None, bg=False):
        if self.brain.get("silence"):
            log.debug("SILENCED")
            return
        self.fade_to_percent(self.HidePos, duration)
        if not bg:
            self.thread.join()
            self.thread = None

