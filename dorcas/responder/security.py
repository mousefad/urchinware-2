import os
import sys
import logging
from dorcas.responder import Responder
from dorcas.urge import Urge
from dorcas.urge.act import Act


log = logging.getLogger(__name__)


class Security(Responder):
    def __init__(self, brain):
        log.info(f"Responder {self.__class__.__name__}.__init__")
        super().__init__(brain)

    def __call__(self, sensation):
        urges = list()
        try:
            x = sensation.json
            # if sensation.topic == self.brain.topic("os/login"):
            #     text = f"someone has logged into me from {x['from_hostname']}"
            #     urges.append(
            #         Act(
            #             program=f"say({text!r})",
            #             priority=Urge.High,
            #             cause="Login detected",
            #         )
            #     )
            if sensation.topic == self.brain.topic("os/portscan"):
                text = f"I'm getting port scanned from host {x['from_hostname']}."
                urges.append(
                    Act(
                        program=f"say({text!r})",
                        cause="Port scan detected",
                        priority=Urge.High,
                    )
                )
        except Exception as e:
            log.error(
                "Security failed to react to topic {sensation.topic}", exc_info=True
            )
        return urges
