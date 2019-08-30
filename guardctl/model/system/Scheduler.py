from poodle import Object
from typing import Set
from guardctl.model.kinds.Pod import Pod
from guardctl.model.system.primitives import StatusSched, String


class Scheduler(Object):
    queueLength: int
    status: String
    podQueue: Set[Pod]

