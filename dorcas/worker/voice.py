# Python built-in modules
import os
import sys
import threading
import subprocess as sp
import logging
import re
import json
import time
from collections import deque

# PIP-installed modules
from singleton_decorator import singleton
import arrow

# Project modules
from dorcas.database import DB, Voice as VoiceTable
from dorcas import database
from dorcas.worker import Worker
from dorcas.worker.eyes import Eyes
from dorcas.worker.mqttclient import MqttClient

log = logging.getLogger(__name__)


def make_speech_cmd(text, voice):
    """Get speech engine command"""
    cmd = [voice.engine]
    cmd.extend(['-v', voice.voice])
    cmd.extend(['-s', str(voice.speed)])
    cmd.extend(['-p', str(voice.pitch)])
    cmd.extend(['-a', str(voice.amplitude)])
    cmd.extend(['-w', '/dev/stdout'])
    cmd.append(text)
    return cmd


def make_effect_cmd(effect):
    return ["play"] + effect.args.split()


@singleton
class Gob:
    """The Gob is an interruptable utterer of text in a specified voice."""
    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        self.brain = brain
        self.is_talking = False
        self.speech_proc = None
        self.effect_proc = None
        self.thread = None
        self.last_text = ""

    def utter(self, text, voice):
        """start speaking (non-blocking)"""
        if self.is_talking:
            return False
        self.wait()
        self.thread = threading.Thread(target=self._utter, args=(text, voice))
        self.thread.start()
        return True

    def interrupt(self):
        if self.is_talking:
            [x.kill() for x in (self.speech_proc, self.effect_proc) if x is not None]
            [x.wait() for x in (self.speech_proc, self.effect_proc) if x is not None]
            self.brain.experience(Sensation(self.brain.topic("interrupted"), self.last_text))
            log.info("utterance interrupted")
        self.wait()

    def wait(self):
        """Block until existing urrerances are complete"""
        if self.thread:
            self.thread.join()
            self.thread = None
        self.is_talking = False

    def _utter(self, text, voice):
        """blocking utterances"""
        if self.is_talking:
            return False
        exc = False
        try:
            self.is_talking = True
            self.last_text = text
            speech_cmd = make_speech_cmd(text, voice)
            effect_cmd = make_effect_cmd(voice.effect)
            self.brain.be_polite()
            log.info(f"saying v={voice.id!r} {text!r}")
            MqttClient().publish(self.brain.topic("talking"), "voice start")
            Eyes().on()
            log.debug(f"utter: speech cmd: {speech_cmd}")
            log.debug(f"utter: effect cmd: {effect_cmd}")
            log.debug(f"UTTER[voice={voice.id}]: {text}")
            self.speech_proc = sp.Popen(speech_cmd, stdout=sp.PIPE)
            self.effect_proc = sp.Popen(effect_cmd, stdin=self.speech_proc.stdout)
            self.speech_proc.stdout.close()
            self.effect_proc.communicate()[0]
        except Exception as e:
            log.exception(f"exception while uttering utter")
            exc = True
        finally:
            ok = True
            if self.speech_proc:
                if self.speech_proc.wait() != 0:
                    ok = False
                    self.speech_proc = None
            if self.effect_proc:
                if self.effect_proc.wait() != 0:
                    ok = False
                    self.effect_proc = None
            Eyes().fade(0.05, 0.5, 25)
            self.is_talking = False
            MqttClient().publish(self.brain.topic("said"), text)
            log.info(f"said{' [exc]' if exc else ''}   v={voice.id!r} {text!r}")
            log.debug(f"utter END ok={ok}")
            return ok


@singleton
class Voice(Worker):
    """A voice queue manager

    Actual speaking is done by the Gob() singleton. This class is used to queue up things
    to say, and split things into chunks with different characteristics."""

    def __init__(self, brain):
        log.info(f"Worker {self.__class__.__name__}.__init__")
        super().__init__(brain)
        Gob(brain) 
        self.queue = deque()

    def run(self):
        log.info(f"{self.__class__.__name__}.run BEGIN")
        while not self.halt:
            while len(self.queue) > 0:
                try:
                    text, voice_id = self.queue.popleft()
                    voice = DB().session.get(VoiceTable, voice_id)
                    Gob().wait()
                    Gob().utter(text, voice)
                    self.brain.set("last_utterance", arrow.now())
                    time.sleep(0.25)
                except Exception as e:
                    log.exception(f"when trying to speak with voice {voice_id!r}")
            time.sleep(0.25)
        log.info(f"{self.__class__.__name__}.run END")

    def say(self, text, voice=None):
        """queue up something to say.

        Arguments:
        text - in the language-appropriate for the voice in question.
        voice - the id column from the VOICES table in the database to use
        """
        if self.brain.get("silence"):
            log.debug("SILENCED")
            return
        if voice is None or DB().session.get(VoiceTable, voice) is None:
            voice = self.brain.config.voice_id
        self.queue.append((text, voice))

    
