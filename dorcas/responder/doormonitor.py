# Base modules
import os
import sys
import logging
import re

# PIP-installed modules
import arrow

# Project modules
from dorcas.responder import Responder
from dorcas.sense.time import duration_to_str
from dorcas.sensation import Sensation


log = logging.getLogger(os.path.basename(sys.argv[0]))


class DoorMonitor(Responder):
    """This responder records when the front door has been open and closed, and sets brain state"""
    TopicRx = re.compile(r"nh/gk/(\d+)/DoorState$")
    MessageRx = re.compile(r"(OPEN|CLOSED|LOCKED)$")

    def __init__(self, brain):
        super().__init__(brain)

    def __call__(self, sensation):
        m = DoorMonitor.TopicRx.match(sensation.topic)
        if not m:
            return []
        door_id = m.group(1)
        state_id = f"door_{door_id}"
        m = DoorMonitor.MessageRx.match(sensation.message)
        if not m:
            return []
        state = m.group(1)

        # a human-readable door name
        if state_id == "door_1":
            door_name = "the front door"
        else:
            door_name = state_id.replace("_", " number ")

        # update the state based on the event details
        if state == "OPEN":
            self.brain.set(state_id, {"name": door_name, "open": True, "open_since": arrow.now(), "notified": False})
        elif state in ("CLOSED", "LOCKED"):
            old = self.brain.get(state_id)
            open_for = None
            if old and 'open_since' in old:
                open_since = old.get('open_since')
                if open_since is not None:
                    open_for = arrow.now() - open_since
                    open_for_str = duration_to_str(open_for)
                    self.brain.experience(Sensation(f"nh/urchin/door/{door_id}/closed", f"was open for {open_for_str}"))
            self.brain.set(state_id, {"name": door_name, "open": False, "open_since": None, "notified": False})
        return []

