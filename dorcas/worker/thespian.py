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

log = logging.getLogger(os.path.basename(sys.argv[0]))


# Define the functions that can be called from Act programs...
def say(text, voice="default"):
    assert type(text) is str
    assert type(voice) is str
    Voice().say(text, voice)


def pause(seconds):
    assert type(seconds) in (int, float)
    time.sleep(seconds)


def play(path, bg=True):
    assert type(path) is str
    assert not path.startswith("/"), "may not use absolute paths for audio files"
    assert not re.search(r"(^|/)\.\./", path), "may not use .. in audio file paths"
    found = None
    for root in audio_search_paths():
        candidate = os.path.join(root, path)
        if os.path.exists(candidate):
            found = candidate
            break
    log.info(f"play({path!r}) => {found!r}")
    if found is None:
        raise FileNotFoundError(path)
    Audio().play(found, bg=bg)


def audio_search_paths():
    paths = list()
    def add_path(p):
        if p not in paths:
            paths.append(p)
    try:
        [add_path(p) for p in os.environ["DORCAS_AUDIO_DIRS"].split(":")]
    except:
        pass
    add_path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample", "audio")))
    log.info(f"audio_search_paths: {' '.join(paths)}")
    return paths


def publish(topic, message):
    assert type(topic) is str
    if message is None:
        message = ""
    assert type(message) is str
    MqttClient.publish(topic, message)


def eyes(final, duration=0.5):
    Eyes().fade(final, duration, 21.0 / duration)


def get_audio_files(subdir=None):
    paths = set()
    for d in audio_search_paths():
        if subdir:
            d = os.path.join(d, subdir)
        for ext in (".mp3", ".wav", ".flac"):
            [paths.add(p[len(d)-len(subdir):]) for p in glob.glob(os.path.join(d, f"*{ext}")) if os.path.isfile(p)]
    return list(paths)
    

@singleton
class ActionRunner:
    """A class for compiling and executing action programs in a (hopefully) safe way."""
    def run(self, act):
        try:
            tree = ast.parse(act.program)
            scope = copy.copy(act.state)
            scope["say"] = say
            scope["pause"] = pause
            scope["play"] = play
            scope["publish"] = publish
            scope["eyes"] = eyes
            scope["random"] = random.random
            scope["random_choice"] = random.choice
            scope["audio_files"] = get_audio_files
            eval(compile(tree, "<string>", "exec"), {}, scope)
        except Exception as e:
            log.exception(f"oopsie: {e}")


@singleton
class Thespian(Worker):
    """Urchin's inner Thespian - for performing Act urges."""
    def __init__(self, brain):
        super().__init__(brain)
        self.queue = deque()
        self.current = None 

    def add(self, act):
        # TODO: if current, and higher priority, interrupt
        self.queue.append(act)

    def run(self):
        log.debug("Thespian.run BEGIN")
        while not self.halt:
            time.sleep(0.25)
            if self.current:
                if not self.current.is_alive():
                    self.current.join()
                    log.debug("Thespian.run joined a completed Act")
                    self.current = None
            if not self.current and len(self.queue) > 0:
                act = self.queue.popleft()
                log.info(f"Thespian.run starting {act!r}")
                self.current = threading.Thread(target=self.perform, args=(act,))
                self.current.start()
        if self.current:
            log.info(f"Thespian.run waiting for current Act to end")
            self.current.join()
            self.current = None
            log.info(f"Thespian.run last Act ended")
        log.debug("Thespian.run END")

    def perform(self, act):
        try:
            log.info(f"Thespian.perform START {act!r}")
            ActionRunner().run(act)
            log.info(f"Thespian.perform END")
        except Exception as e:
            log.exception("Thespian.perform EXCEPTION {act!r}")


