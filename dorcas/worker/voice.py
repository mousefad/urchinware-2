# Build-in modules
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
from dorcas.getem import GeTem
from dorcas import database
from dorcas.worker import Worker
from dorcas.worker.eyes import Eyes
from dorcas.worker.mqttclient import MqttClient

log = logging.getLogger(os.path.basename(sys.argv[0]))


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
    def __init__(self):
        self.is_talking = False
        self.speech_proc = None
        self.effect_proc = None
        self.thread = None
        self.last_text = ""

    def utter(self, text, voice, pause):
        """start speaking (non-blocking)"""
        if self.is_talking:
            return False
        self.wait()
        self.thread = threading.Thread(target=self._utter, args=(text, voice, pause))
        self.thread.start()
        return True

    def interrupt(self):
        if self.is_talking:
            [x.kill() for x in (self.speech_proc, self.effect_proc) if x is not None]
            [x.wait() for x in (self.speech_proc, self.effect_proc) if x is not None]
            self.brain.experience(Sensation("urchin/speech/interrupted", self.last_text))
        self.wait()

    def wait(self):
        """Block until existing urrerances are complete"""
        if self.thread:
            self.thread.join()
            self.thread = None
        self.is_talking = False

    def _utter(self, text, voice, pause):
        """blocking utterances"""
        log.debug(f"utter START text={text} voice_id={voice.id}")
        if self.is_talking:
            return False
        try:
            self.is_talking = True
            self.last_text = text
            speech_cmd = make_speech_cmd(text, voice)
            effect_cmd = make_effect_cmd(voice.effect)
            time.sleep(pause)
            MqttClient().publish("nh/urchin/talking", "voice start")
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
            MqttClient().publish("nh/urchin/said", text)
            log.debug(f"utter END ok={ok}")
            return ok


class Utterance:
    def __init__(self, text, voice, pause=0.0):
        self.text = text
        self.voice = voice
        self.pause = pause

    def __repr__(self):
        return f"Utterance(text={self.text!r}, voice={self.voice.id!r}, pause={self.pause!r})"


@singleton
class Voice(Worker):
    """A voice queue manager

    Actual speaking is done by the Gob() singleton. This class is used to queue up things
    to say, and split things into chunks with different characteristics"""

    def __init__(self, brain):
        super().__init__(brain)
        self.default_voice = brain.config.voice
        self.queue = deque()

    def run(self):
        log.debug("Voice.run START")
        self.halt = False
        while not self.halt:
            while len(self.queue) > 0:
                utterance = self.queue.popleft()
                Gob().wait()
                Gob().utter(utterance.text, utterance.voice, utterance.pause)
                self.brain.set("last_utterance", arrow.now())
                time.sleep(1)
            time.sleep(0.5)
        log.debug("Voice.run END")

    def say(self, text, state=None):
        """queue up something to say. Voice changes should be 'in' the text with [directives]."""
        if self.brain.get("silence"):
            log.debug("SILENCED")
            return
        if state is None:
            state = self.brain.state
        text = GeTem(text)(state)
        for utterance in self.split(text):
            self.queue.append(utterance)

    def split(self, text):
        matches = list(re.finditer(r"({[^}]*})([^{]*)", text))
        if len(matches) == 0:
            return [Utterance(text, self.default_voice)]

        items = list()
        first_match_idx = matches[0].span()[0] 
        if first_match_idx > 0:
            # text before the first {...} 
            items.append(Utterance(text[:first_match_idx], self.default_voice))
        for m in matches:
            if not re.match(r"\s*$", m.group(2)):
                params = self.get_params(m.group(1))
                items.append(Utterance(m.group(2), params["voice"], params["pause"]))
        return items

    def get_params(self, json_str):
        params = {"voice": self.default_voice, "pause": 0.0}
        try:
            data = json.loads(json_str)
        except:
            log.warning(f"failed to json.loads for {json_str!r} : {e} ; using defaults")
            return params
        try:
            if "pause" in data:
                params["pause"] = float(data["pause"])
        except Exception as e:
            log.warning(f"failed to get \"pause\" from json {json_str!r} : {e}")
        try:
            if "voice" in data:
                voice_id = data["voice"]
                voice = database.DB().session.get(database.Voice, voice_id)
                assert voice is not None
                params["voice"] = voice
        except Exception as e:
            log.warning(f"failed to get \"voice\" from json {json_str!r} : {e}")
        return params

    