# Base modules
import os
import sys
import logging
import re
import time
from threading import Timer

# Project modules
from responder import Responder
from urge import Urge
from urge.say import Say
from sensation import Sensation


log = logging.getLogger(os.path.basename(sys.argv[0]))


class MuteSwitch(Responder):
    """This responder monitors the "last man our switch", and mutes the urchin when it is set.

    Unlike most other settings, this will be written into the database config because there is
    no way to know on startup what the switch state is, so startup state will be taken from
    the db.
    """
    def __init__(self, brain):
        super().__init__(brain)
        self.timer = None

    def __call__(self, sensation):
        if sensation.topic != "nh/gk/LastManState":
            return []
    
        if sensation.message == "Last Out":
            self.brain.experience(Sensation("nh/urchin/silence", "yes"))
            self.timer = Timer(5, lambda : self.brain.set_silence(True))
            self.timer.start()
        if sensation.message == "First In":
            if self.timer is not None:
                self.timer.cancel()
            self.brain.set_silence(False)
            self.brain.experience(Sensation("nh/urchin/silence", "no"))

        return []

