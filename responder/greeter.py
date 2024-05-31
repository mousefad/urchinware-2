import os
import sys
import logging
import re
import datetime
import copy
import random
from collections import namedtuple

# PIP installed modules
from sqlalchemy import or_

# Project modules
from condition import evaluate_condition
from responder import Responder
from database import *
from urge import Urge
from urge.say import Say


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Greeter(Responder):
    """Produces one verbal greeting for members entering via the Door."""
    TopicFilter = "nh/gk/entry_announce/known"
    CandidateGreeting = namedtuple("CandidateGreeting", ["id", "weight", "text"])
    AgoPeriods = [
        (re.compile(r"(\d+)d"), 3600 * 24),
        (re.compile(r"(\d+)h"), 3600),
        (re.compile(r"(\d+)m"), 60),
        (re.compile(r"(\d+)s"), 1),
    ]

    def __call__(self, sensation):
        # 1. check we will react to this sensation
        if sensation.topic != Greeter.TopicFilter or not sensation.message.startswith("Door "):
            return []

        # 2. create augmented state with name of person who has arrived and so on
        state = copy.copy(self.brain.state)
        m = re.match(r"Door opened by: (.*) \(last seen (.*) ago\)", sensation.message)
        if m:
            state["member_name"] = m.group(1)
            state["absense_message"] = self.get_absense_message(m.group(2))
        else:
            log.warning("Greeter message regex failed to match for {sensation.message!r}")
            return []

        self.brain.set("arrival", True)

        # 3. filter list of greetings from database by condition
        candidates = list()
        for id, rec in [(f"Greeting #{x.id}", x) for x in DB().session.query(Greeting).filter(or_(Greeting.member == state["member_name"], Greeting.member == None)).all()]:
            if self.want(rec.condition, state, id):
                candidate = self.CandidateGreeting(id, rec.weight, rec.text)
                log.debug(f"adding candidate {candidate}")
                candidates.append(candidate)
        log.debug(f"Greeter: {len(candidates)} candidates to choose from")
        if len(candidates) == 0:
            return []

        # 4. select one of the filtered conditions using randomness + weights
        choice = random.choices(candidates, [x.weight for x in candidates])[0]
        urge = Say(choice.text, priority=Urge.Normal, state=state)
        log.info(f"{choice.id} => {urge} in response to {sensation}")
        return [urge]

    def get_absense_message(self, ago):
        seconds = 0
        for rx, multiplier in Greeter.AgoPeriods:
            m = rx.search(ago)
            if m:
                seconds += int(m.group(1)) * multiplier
        period = datetime.timedelta(seconds=seconds)
        if period.days < 1:
            if period.seconds < 3600:
                return "I din't know you'd left."
            elif period.seconds < 3600 * 3:
                return "Back again?"
            else:
                return "You're back!"
        elif period.days < 2:
            return "You were here yesterday."
        elif period.days < 3:
            return "I think I say you a couple of days ago."
        elif period.days < 30:
            return "You're a familiar face."
        elif period.days < 60:
            return "It's been at least a month."
        elif period.days < 30 * 6:
            return "I don't see you around here very often."
        elif period.days < 365:
            return "It's been a while!"
        else:
            return "Old friend, it's been so long."

    def want(self, condition, state, condition_id):
        if condition is None:
            return True
        else:
            return evaluate_condition(condition, state, condition_id)