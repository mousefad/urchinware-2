import os
import sys
import logging
import random
from dorcas.responder import Responder
from dorcas.urge import Urge
from dorcas.urge.publish import Publish


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Instrumentation(Responder):
    def __init__(self, brain):
        super().__init__(brain)

    def __call__(self, sensation):
        if sensation.topic != "nh/status/req" or sensation.message != "STATUS":
            return []
        return [Publish(priority=Urge.High, topic="nh/status/res", message="Running: Creepy Urchin")]
