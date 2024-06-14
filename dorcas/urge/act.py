from dorcas.urge import Urge
from dorcas.worker.thespian import Thespian


class Act(Urge):
    def __init__(self, program, cause, priority=Urge.Normal, state=dict()):
        super().__init__(cause, priority, state)
        self.program = program

    def __repr__(self):
        return f"Act(program={self.program!r}, cause={self.cause}, priority={self.priority}, state={self.state!r})"

    def perform(self):
        Thespian().add(self)
