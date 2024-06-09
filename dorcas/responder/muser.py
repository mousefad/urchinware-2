import copy
import random
from collections import namedtuple

# Project modules
from dorcas.condition import evaluate_condition
from dorcas.responder import Responder
from dorcas.database import *
from dorcas.urge import Urge
from dorcas.urge.act import Act


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Muser(Responder):
    CandidateMusing = namedtuple("CandidateMusing", ["id", "weight", "action"])

    """General reactions to events."""
    def __call__(self, sensation):
        # 1. create augmented state, extracting details from message
        state = self.augmented_state(sensation)
        
        # 2. filter list of musings from database by condition
        candidates = list()
        for id, rec in [(f"Musing #{x.id}", x) for x in DB().session.query(Musing).filter(Musing.topic == sensation.topic).all()]:
            if self.want(rec.condition, state, id):
                candidate = self.CandidateMusing(id, rec.weight, rec.action)
                log.debug(f"adding candidate {candidate}")
                candidates.append(candidate)

        # cancel arrivals when the door closes
        if sensation.topic == "nh/gk/1/DoorState" and sensation.message == "LOCKED":
            self.brain.set("arrival", False)
        
        log.debug(f"Muser: {len(candidates)} candidates to choose from")
        if len(candidates) == 0:
            return []

        # 3. select one of the filtered conditions using randomness + weights
        choice = random.choices(candidates, [x.weight for x in candidates])[0]
        urge = Act(choice.action, cause=f"{choice.id} because {sensation}", priority=Urge.Normal, state=state)
        log.debug(f"{choice.id} => {urge} in response to {sensation}")
        return [urge]

    def augmented_state(self, sensation):
        state = copy.copy(self.brain.state)
        state['topic'] = sensation.topic
        state['message'] = sensation.message
        data = sensation.json
        if type(data) is dict:
            for k, v in sensation.json.items():
                state[k] = v
        return state

    def want(self, condition, state, id):
        if condition is None:
            return True
        else:
            return evaluate_condition(condition, state, id)
