import os
import sys
import logging
import random
from dorcas.responder import Responder
from dorcas.urge import Urge
from dorcas.urge.say import Say


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Time(Responder):
    def __init__(self, brain):
        super().__init__(brain)

    def __call__(self, sensation):
        urges = list()
        if sensation.topic != "time/now":
            return urges

        try:
            data = sensation.json
            if data['minute'] == 0:
                urges.extend(self.on_the_hour(data['hour']))
        except Exception as e:
            log.exception(f"while responding to the time: {sensation}")

        return urges

    def on_the_hour(self, hour):
        if not random.random() < 0.75:
            return []
        if hour == 0:
            text = f"It's mid night. I should go to bed."
        elif hour == 12:
            text = f"It mid day. What's for lunch?"
        elif hour == 23:
            text = f"It's the witching hour. Spooky."
        else:
            text = f"It's {hour % 12} o clock. "
        return [Say(priority=Urge.Low, text=text)]
