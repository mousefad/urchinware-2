# Built-in modules
import logging
import sys
import os
import threading
import time
import pigpio
from abc import ABC, abstractmethod


log = logging.getLogger(__name__)


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


def frange(start, end, steps):
    assert type(steps) is int
    assert steps > 0
    increment = (end - start) / steps
    while True:
        if increment > 0:
            if start >= end:
                break
        else:
            if start <= end:
                break
        yield start
        start += increment
    if start != end:
        yield end


try:
    PigPi = pigpio.pi()
    assert PigPi.connected is True
except:
    log.warning("pigpio not connected - PWM functions disabled")
    PigPi = None


class PwmFader(ABC):
    def __init__(self, pin, min_value, max_value, default_duration, default_steps_per_second, only_active_while_fading):
        log.debug("PwmFader.__init__")
        self.pin = pin
        self.min = min_value
        self.max = max_value
        self.default_duration = default_duration
        self.default_steps_per_second = default_steps_per_second
        self.only_active_while_fading = only_active_while_fading
        self.thread = None
        self.value = None
        self.fading = False

    def __del__(self, *args):
        log.debug("PwmFader.del")
        try:
            self.deactivate()
        except:
            pass

    def activate(self):
        log.debug(f"PwmFader.activate pin={self.pin}")
        if PigPi and PigPi.get_mode(self.pin) != pigpio.OUTPUT:
            PigPi.set_mode(self.pin, pigpio.OUTPUT)

    def deactivate(self):
        log.debug(f"PwmFader.deactivate pin={self.pin}")
        if PigPi and PigPi.get_mode(self.pin) != pigpio.INPUT:
            PigPi.set_mode(self.pin, pigpio.INPUT)

    def cancel_fade(self):
        log.debug("PwmFader.cancel_fade")
        if self.thread:
            self.fading = False
            self.thread.join()
            self.thread = None

    @abstractmethod
    def set(self, value):
        pass

    def fade_to(self, value, duration=None, steps_per_second=None):
        log.debug(f"PwmFader.fade(value={value}, duration={duration} steps_per_second={steps_per_second})")
        if duration is None:
            duration = self.default_duration
        if steps_per_second is None:
            steps_per_second = self.default_steps_per_second
        self.cancel_fade()
        self.thread = threading.Thread(target=self._fade, args=(self.value, value, duration, steps_per_second))
        self.thread.start()

    def _fade(self, start, end, duration, steps_per_second):
        if start is None:
            self.set(end)
            return
        steps = int(duration * self.default_steps_per_second)
        step_duration = duration / steps
        self.activate()
        self.fading = True
        for v in frange(start, end, steps):
            if not self.fading:
                return
            self.set(int(v))
            time.sleep(step_duration)
        self.set(end)
        self.fading = False
        if self.only_active_while_fading:
            self.deactivate()


class ServoFader(PwmFader):
    def __init__(self, pin, min_value, max_value, default_duration=0.25, default_steps_per_second=100):
        log.debug("ServoFader.__init__")
        super().__init__(pin, min_value, max_value, default_duration, default_steps_per_second, True)

    def set(self, value):
        assert value >= self.min and value <= self.max, f"value={value} min={self.min} max={self.max}"
        if PigPi:
            PigPi.set_servo_pulsewidth(self.pin, value)
        self.value = value

class LedFader(PwmFader):
    Min = 0
    Max = 255
    def __init__(self, pin, default_duration=0.25, default_steps_per_second=50):
        log.debug("LedFader.__init__")
        super().__init__(pin, self.Min, self.Max, default_duration, default_steps_per_second, False)
        self.blink_thread = None

    def set(self, value):
        assert value >= self.Min and value <= self.Max
        if PigPi:
            PigPi.set_PWM_dutycycle(self.pin, value)
        self.value = value

