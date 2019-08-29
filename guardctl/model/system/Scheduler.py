from poodle import Object
from typing import Set
from guardctl.model.kinds.Pod import Pod
from guardctl.model.system.primitives import StatusSched


class Scheduler(Object):
    queueLength: int
    status: StatusSched
    podQueue: Set[Pod]

