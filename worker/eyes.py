# Build-in modules
import os
import sys
import subprocess as sp
import time
import logging
import re
import json
import time
import threading
from math import exp

# PIP-installed modules
from singleton_decorator import singleton

# Project modules
from getem import GeTem
import database
from worker import Worker
from worker.mqttclient import MqttClient
try:
    from gpiozero import LED 
except ModuleNotFoundError:
    pass


log = logging.getLogger(os.path.basename(sys.argv[0]))

class FakeLED:
    def __init__(self, *args):
        pass
    def off(self):
        pass
    def on(self):
        pass
    def blink(self, *args):
        pass


@singleton
class Eyes:
    """For making the eyes glow"""
    LinearScaleFactor = 4
    GpioPin = 17 # TODO: make this database config driven

    def __init__(self, brain):
        self.brain = brain
        try:
            self.led = LED(self.GpioPin)
        except:
            log.warning("failed to use GPIO pin for LED, eyes will be disabled.")
            self.led = FakeLED()
        self.thread = None
        self.halt = None
        self.off()

    def __del__(self):
        # make sure we reap our fader thread if there is one
        self.cancel_fade()

    def start(self):
        pass

    def stop(self):
        pass

    def wait(self):
        pass

    def cancel_fade(self):
        if self.thread:
            self.halt = True
            self.thread.join()

    def on(self):
        self.cancel_fade()
        self._on()

    def _on(self):
        self.led.on()
        self.intensity = 1.0

    def off(self):
        self.cancel_fade()
        self._off()

    def _off(self):
        self.led.off()
        self.intensity = 0.0

    def fade_on(self, duration=1.0, steps=50):
        self.fade(1.0, duration, steps)

    def fade_off(self, duration=1.0, steps=50):
        self.fade(0.0, duration, steps)

    def fade(self, final, duration, steps, initial=None):
        if initial is None:
            initial = self.intensity
        self.cancel_fade()
        self.thread = threading.Thread(target=self._fade, args=(final, duration, steps, initial))
        self.thread.start()

    def _fade(self, final, duration, steps, initial):
        step_size = (final - initial) / steps
        step_duration = duration / steps
        self.halt = False
        for i in range(steps):
            if self.halt:
                return
            self.set_intensity(initial + (i * step_size))
            time.sleep(step_duration)
        self.set_intensity(final)
        if self.intensity >= 0.999:
            self._on()
        elif final <= 0.001:
            self._off()

    def set_intensity(self, intensity):
        assert type(intensity) is float
        assert intensity >= 0.0 and intensity <= 1.0
        if intensity < 0.001:
            self._off()
        elif intensity > 0.999:
            self._on()
        self.intensity = intensity
        on_time = self.intensity_to_pwm(intensity) / 300.0
        off_time = self.intensity_to_pwm(1.0 - intensity) / 300.0
        self.led.blink(on_time, off_time, None)

    def intensity_to_pwm(self, lin_value):
        return exp(lin_value * self.LinearScaleFactor) / exp(self.LinearScaleFactor)


