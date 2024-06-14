import os
import sys
import logging
import random
from dorcas.responder import Responder
from dorcas.urge import Urge
from dorcas.urge.publish import Publish


log = logging.getLogger(__name__)


class Instrumentation(Responder):
    def __init__(self, brain):
        log.info(f"Responder {self.__class__.__name__}.__init__")
        super().__init__(brain)

    def __call__(self, sensation):
        if sensation.topic != "nh/status/req" or sensation.message != "STATUS":
            return []
        topic = "nh/status/res"
        message = f"Running: {self.brain.get('instrument_id')}"
        return [Publish(topic=topic, message=message, cause="status request", priority=Urge.High)]
