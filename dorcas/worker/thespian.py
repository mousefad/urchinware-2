# Python built-in modules
import os
import sys
import threading
import subprocess as sp
import logging
import time
import ast
import re
import copy
import glob
import random
from collections import deque

# PIP-installed modules
from singleton_decorator import singleton
import cachetools.func

# Project modules
from dorcas import database
from dorcas.worker import Worker
from dorcas.worker.voice import Voice
from dorcas.worker.audio import Audio
from dorcas.worker.eyes import Eyes
from dorcas.worker.mqttclient import MqttClient


log = logging.getLogger(__name__)


@singleton
class ActionRunner:
    """A class for compiling and executing action programs in a (hopefully) safe way."""
    def say(*args, **kwargs):
        return Voice().say(*args, **kwargs)
    def eyes(final, duration=0.5):
        return Eyes().fade(final, duration, 21.0 / duration)
    def play(*args, **kwargs):
        return Audio().play(*args, **kwargs)
    def audio_find(*args, **kwargs):
        return Audio().find(*args, **kwargs)
    def publish(*args, **kwargs):
        return MqttClient().publish(*args, **kwargs)

    FunctionMap = {
        "say": say,
        "eyes": eyes,
        "pause": time.sleep,
        "play": play,
        "audio_find": audio_find,
        "publish": publish,
        "random": random.random,
        "random_int": random.randint,
        "random_choice": random.choice,
        "log": log.info,
    }
    def run(self, act):
        try:
            context = copy.deepcopy({} if act.state is None else act.state)
            for k, v in self.FunctionMap.items():
                context[k] = v
            eval(self.compile(act.program), {}, context)
        except Exception as e:
            log.exception(f"while running action {act!r}")

    def compile(self, program):
        tree = ast.parse(program)
        return compile(tree, "<string>", "exec")



@singleton
class Thespian(Worker):
    """Urchin's inner Thespian - for performing Act urges."""

    # Lessen flooding...
    MaxQueueLength = 3

    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        super().__init__(brain)
        self.queue = deque()
        self.current = None 

    def add(self, act):
        # TODO: if current, and higher priority, interrupt
        if len(self.queue) < self.MaxQueueLength:
            self.queue.append(act)

    def run(self):
        log.info(f"{self.__class__.__name__}.run BEGIN")
        while not self.halt:
            time.sleep(0.25)
            if self.current:
                if not self.current.is_alive():
                    self.current.join()
                    log.debug("Thespian.run joined a completed Act")
                    self.current = None
            if not self.current and len(self.queue) > 0:
                self.join() # wait for any existing act to finish
                act = self.queue.popleft()
                log.debug(f"Thespian.run starting {act!r}")
                self.current = threading.Thread(target=self.perform, args=(act,))
                self.current.start()
        self.join()
        log.info(f"{self.__class__.__name__}.run END")

    def perform(self, act):
        try:
            log.info(f"Thespian.perform START {act.cause}")
            ActionRunner().run(act)
            log.debug(f"Thespian.perform END")
        except Exception as e:
            log.exception("Thespian.perform EXCEPTION {act!r}")

    def join(self):
        if self.current:
            self.current.join()
            self.current = None

