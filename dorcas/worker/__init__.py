# Built-in modules
import logging
import sys
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Generator


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


def frange(start: float, end: float, steps: int) -> Generator[float, None, None]:
    """Generator to make a sequence of floats in a specified range.

    Args:
        start is the first value that woill be returned
        end tells us when to stop (less than or equal to)
        steps tells us how many values we will get
    """
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


class PwmChannel:
    """Control Raspberry Pi hardware PWM channels"""
    ControllerDir = "/sys/class/pwm/pwmchip0"

    @staticmethod
    def write(path: str, value: str):
        log.debug(f"PwmChannel.write(path={path!r}, value={value!r})")
        with open(path, "w") as f:
            f.write(value)

    @staticmethod
    def percent_linear(percent: float, lower: int, upper: int) -> int:
        bound_range = upper - lower
        return int((bound_range * percent)/100. + lower)

    def __init__(self, 
        channel: str, 
        period_ns: int, 
        enable,
        default_duty_ns: Optional[int]=None, 
        lower_bound_duty_ns: Optional[int]=None,
        upper_bound_duty_ns: Optional[int]=None,
        percent_fn: Callable[[float, int, int], int]=percent_linear,
    ) -> None:
        """Create a PwmChannel.

        Args:
            - channel is either "0" or "1" referring to PWM0 or PWM1 pins on Raspberry Pi
            - period_ns is the PWM period in nanoseconds. e.g. for 50Hz, use 1e9//50 = 20_000_000 nanoseconds
            - enable if True, activate the PWM waveform of new object, else do not activate it.
            - default_duty_ns initial duty system to set (high duration in nanoseconds). If None, use lower bound
            - lower_bound_duty_ns if set limit min duty system, else 0
            - upper_bound_duty_ns if set limit min duty system, else period_ns
            - percent_fn is a function that computes the duty_ns from (percent, lower_bound, upper_bound)
        """
        assert channel in ["0", "1"]
        assert period_ns > 0
        if lower_bound_duty_ns is None:
            lower_bound_duty_ns = 0
        if upper_bound_duty_ns is None:
            upper_bound_duty_ns = period_ns 
        assert lower_bound_duty_ns >=0 and lower_bound_duty_ns <= period_ns
        assert upper_bound_duty_ns >=0 and upper_bound_duty_ns <= period_ns and upper_bound_duty_ns >= lower_bound_duty_ns
        self.channel = channel
        self.pin_dir = f"{PwmChannel.ControllerDir}/pwm{channel}"
        self.period_ns = period_ns
        self.lower_bound_duty_ns = lower_bound_duty_ns
        self.upper_bound_duty_ns = upper_bound_duty_ns
        self.bound_range = upper_bound_duty_ns - lower_bound_duty_ns
        self.percent_fn = percent_fn

        # Activate the device in sysfs if needed
        if not os.path.exists(self.pin_dir):
            # Creates the pwm<channel> subdir to enable the driver for this channel
            PwmChannel.write(f"{PwmChannel.ControllerDir}/export", self.channel)
            time.sleep(0.1)
        self.set_enabled(False)
        PwmChannel.write(f"{self.pin_dir}/period", str(period_ns))
        self.set_duty_cycle(default_duty_ns or self.lower_bound_duty_ns)
        self.set_enabled(enable)

    def __del__(self, *args):
        log.debug(f"PwmChannel[channel={self.channel}].del")
        try:
            self.deactivate()
        except:
            pass

    def set_enabled(self, value: bool):
        PwmChannel.write(f"{self.pin_dir}/enable", "1" if value else "0")
        self.is_enabled = value

    def activate(self):
        self.set_enabled(True)

    def deactivate(self):
        self.set_enabled(False)

    def set_duty_cycle(self, duty_ns: int):
        if duty_ns < self.lower_bound_duty_ns:
            duty_ns = self.lower_bound_duty_ns
        if duty_ns > self.upper_bound_duty_ns:
            duty_ns = self.upper_bound_duty_ns
        PwmChannel.write(f"{self.pin_dir}/duty_cycle", str(duty_ns))
        self.duty_ns = duty_ns

    def set_percent(self, percent: float):
        self.set_duty_cycle(self.percent_fn(percent, self.lower_bound_duty_ns, self.upper_bound_duty_ns))


class PwmFader(PwmChannel):
    """Control PWM pins with Raspberry Pi hardware PWM controller.

    Note: requires "dtoverlay=pwm-2chan" to be in /[bootdev]/usercfg.txt
    """
    def __init__(
        self, 
        channel: str, 
        period_ns: int, 
        enable: bool,
        fade_time_seconds: float, 
        steps_per_second: float, 
        only_active_while_fading: bool,
        default_duty_ns: Optional[int]=None, 
        lower_bound_duty_ns: Optional[int]=None,
        upper_bound_duty_ns: Optional[int]=None,
        percent_fn: Callable[[float, int, int], int]=PwmChannel.percent_linear,
    ) -> None:
        """Create a PwmFader.

        Args:
            - channel is either "0" or "1" referring to PWM0 or PWM1 pins on Raspberry Pi
            - period_ns is the PWM period in nanoseconds. e.g. for 50Hz, use 1e9//50 = 20_000_000 nanoseconds
            - enable if True, activate the PWM waveform of new object, else do not activate it.
            - fade_time_seconds is the time in seconds to reach new values on setting
            - steps_per_second now many steps to divide fade into
            - only_active_while_fading if True, de-activate the PWM waveform after fade is complete
            - default_duty_ns initial duty system to set (high duration in nanoseconds)
            - lower_bound_duty_ns set lower bound
            - upper_bound_duty_ns set upper bound. If None, use period_ns
            - percent_fn is a function that computes the duty_ns from (percent, lower_bound, upper_bound)
        """
        log.debug("PwmFader.__init__")
        super().__init__(channel, period_ns, enable, default_duty_ns, lower_bound_duty_ns, upper_bound_duty_ns, percent_fn)
        assert fade_time_seconds >= 0.
        assert steps_per_second > 0.
        self.fade_time_seconds = fade_time_seconds
        self.steps_per_second = steps_per_second
        self.only_active_while_fading = only_active_while_fading
        self.thread = None

    def fade_to(self, duty_ns: int, duration: Optional[float]=None, steps_per_second: Optional[float]=None) -> None:
        log.debug(f"PwmFader[channel={self.channel}].fade_to(duty_ns={duty_ns}, duration={duration!r} steps_per_second={steps_per_second!r})")
        if duration is None:
            duration = self.fade_time_seconds
        if steps_per_second is None:
            steps_per_second = self.steps_per_second
        self.cancel_fade()
        self.thread = threading.Thread(target=self._fade, args=(self.duty_ns, duty_ns, duration, steps_per_second))
        self.thread.start()

    def fade_to_percent(self, percent: float, duration: Optional[float]=None, steps_per_second: Optional[float]=None) -> None:
        log.debug(f"PwmFader[channel={self.channel}].fade_to_percent(percent={percent}, duration={duration!r} steps_per_second={steps_per_second!r})")
        duty_ns = self.percent_fn(percent, self.lower_bound_duty_ns, self.upper_bound_duty_ns)
        #log.debug(f" self.lower_bound_duty_ns={self.lower_bound_duty_ns} self.upper_bound_duty_ns={self.upper_bound_duty_ns} duty_ns={duty_ns}")
        self.fade_to(duty_ns, duration, steps_per_second)

    def cancel_fade(self):
        log.debug(f"PwmFader[channel={self.channel}].cancel_fade")
        if self.thread:
            self.fading = False
            self.thread.join()
            self.thread = None
 
    def _fade(self, start, end, duration, steps_per_second):
        """Used as main() for fader thread."""
        if start is None:
            self.set_duty_cycle(end)
            return
        steps = int(duration * steps_per_second)
        step_duration = duration / steps
        self.activate()
        self.fading = True
        for v in frange(start, end, steps):
            if not self.fading:
                return
            self.set_duty_cycle(int(v))
            time.sleep(step_duration)
        self.set_duty_cycle(end)
        self.fading = False
        if self.only_active_while_fading:
            self.deactivate()


if __name__ == "__main__":
    # test with servo on PWM0 and LED on PWM1
    period = 20_000_000
    min_duty = int(0.030  * period)
    max_duty = int(0.125 * period)
    f0 = PwmFader(
        channel="0", 
        period_ns=period, 
        enable=True,
        fade_time_seconds=0.5, 
        steps_per_second=100., 
        only_active_while_fading=True,
        lower_bound_duty_ns=min_duty,
        upper_bound_duty_ns=max_duty,
    )
    f1 = PwmFader(
        channel="1", 
        period_ns=100000, 
        enable=True,
        fade_time_seconds=0.5, 
        steps_per_second=200., 
        only_active_while_fading=False,
    )
    time.sleep(1)
    for _ in range(3):
        f0.fade_to_percent(0.)
        f1.fade_to_percent(100.)
        time.sleep(1)
        f0.fade_to_percent(50.)
        f1.fade_to_percent(50.)
        time.sleep(1)
        f0.fade_to_percent(100.)
        f1.fade_to_percent(0.)
        time.sleep(1)
