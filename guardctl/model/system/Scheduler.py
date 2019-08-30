from poodle import Object
from typing import Set
import guardctl.model.kinds.Pod as pod
from guardctl.model.system.primitives import StatusSched, String


class Scheduler(Object):
    queueLength: int
    status: String
    podQueue: Set["pod.Pod"]

