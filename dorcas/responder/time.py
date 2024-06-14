import os
import sys
import logging
import random
from dorcas.responder import Responder
from dorcas.urge import Urge
from dorcas.urge.act import Act


log = logging.getLogger(__name__)


class Time(Responder):
    def __init__(self, brain):
        log.info(f"Responder {self.__class__.__name__}.__init__")
        super().__init__(brain)

    def __call__(self, sensation):
        urges = list()
        if sensation.topic != self.brain.topic("time/now"):
            return urges

        try:
            data = sensation.json
            if data['minute'] == 0:
                urges.extend(self.on_the_hour(data['hour']))
        except Exception as e:
            log.exception(f"while responding to the time: {sensation}")
        return urges

    def on_the_hour(self, hour):
        bongs = hour % 12
        if bongs == 0:
            bongs = 12
        if hour == 0:
            text = f"It's mid night. I should go to bed."
        elif hour == 12:
            text = f"It mid day. What's for dinner?"
        elif hour == 18:
            text = f"It's 6 o clock, what's for tea?"
        else:
            text = f"It's {bongs} o clock."
        program =  f"for _ in range({bongs}):\n"
        program += f"    play('cuckoo_chime.wav', bg=True)\n"
        program += f"    pause({random.randrange(700, 800) / 1000.0})\n"
        program += f"say({text!r})\n"
        return [Act(program, cause=f"Time is {hour:02d}:00", priority=Urge.Normal)]


