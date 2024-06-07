import os
import sys
import logging
from dorcas.responder import Responder
from dorcas.urge import Urge
from dorcas.urge.say import Say


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Security(Responder):
    def __init__(self, brain):
        super().__init__(brain)

    def __call__(self, sensation):
        urges = list()
        try:
            x = sensation.json
            # if sensation.topic == "os/login":
            #     urges.append(
            #         Say(
            #             priority=Urge.High,
            #             text=f"security notice: someone logged into me with account {x['user']}, from {x['from_hostname']}, auth type {x['method']}.",
            #         )
            #     )
            if sensation.topic == "os/portscan":
                urges.append(
                    Say(
                        priority=Urge.High,
                        text=f"security notice: someone's doing a port scan from host {x['from_hostname']}.",
                    )
                )
        except Exception as e:
            log.error(
                "Security failed to react to topic {sensation.topic}", exc_info=True
            )
        return urges
