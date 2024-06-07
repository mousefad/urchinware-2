# Built-in modules
import logging
import sys
import os
import threading
from abc import ABC, abstractmethod


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Worker(ABC):
    def __init__(self, brain):
        self.brain = brain
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
