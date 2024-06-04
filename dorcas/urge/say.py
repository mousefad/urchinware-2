from dorcas.urge import Urge
from dorcas.worker.voice import Voice

class Say(Urge):
    def __init__(self, text, priority=Urge.Normal, state=dict()):
        super().__init__(priority, state)
        self.text = text

    def __repr__(self):
        return f"Say(text={self.text!r}, priority={self.priority})"

    def perform(self):
        Voice().say(self.text, state=self.state)

