# Built-in modules
import logging
import sys
import os
import threading
from collections import deque
from abc import ABC, abstractmethod


log = logging.getLogger(__name__)


class Sense(ABC):
    """Sense derived classes run in a thread, they generate Sensation objects.

    When a sensation is created (e.g. an incoming event in MQTT), call self.brain.experience(sensation)
    """
    def __init__(self, brain):
        self.brain = brain

    def experience(self, sensation):
        self.brain.experience(sensation)

    @abstractmethod
    def start(self):
        """called to start the sense. This function should return, leaving things running in a thread"""
        pass

    @abstractmethod
    def wait(self):
        """blocks until any child thread(s) have ended"""
        pass

    @abstractmethod
    def stop(self):
        """called to stop the sense. This function should block until the sense has shut down"""
        pass


class ThreadedHalterSense(Sense):
    def __init__(self, brain):
        super().__init__(brain)
        self.thread = None
        self.halt = None

    @abstractmethod
    def run(self):
        pass

    def start(self):
        log.debug(f"{self.__class__.__name__}.start")
        if self.thread:
            log.error(f"{self.__class__.__name__}.start: thread already running")
            return False
        self.thread = threading.Thread(target=self.run)
        self.halt = False
        self.thread.start()

    def stop(self):
        log.debug(f"{self.__class__.__name__}.stop")
        self.halt = True

    def wait(self):
        # wait for thread
        log.debug(f"{self.__class__.__name__}.wait")
        if self.thread:
            self.thread.join()
            self.thread = None
            log.info(f"{self.__class__.__name__} END")
            return True

