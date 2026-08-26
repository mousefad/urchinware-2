# Build-in modules
import os
import sys
import logging
import time
import threading
from math import exp


# Project modules
from dorcas import singleton
from dorcas.worker import PwmFader


log = logging.getLogger(__name__)


@singleton
class Eyes(PwmFader):
    """For making the eyes glow"""
    PwmChannel = "1"
    PwmPeriod = 100_000 # 10 KHz for flicker free

    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        super().__init__(
            channel=self.PwmChannel, 
            period_ns=self.PwmPeriod, 
            enable=True,
            fade_time_seconds=0.25, 
            steps_per_second=50., 
            only_active_while_fading=False,
        )
        self.brain = brain 
        self.fade_to_percent(0)

    def start(self):
        pass

    def stop(self):
        pass

    def wait(self):
        pass
