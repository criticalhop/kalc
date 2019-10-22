from poodle import Object, planned
from typing import Set
from guardctl.misc.const import *
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.Node import Node
from guardctl.model.system.primitives import StatusSched
from guardctl.model.scenario import ScenarioStep, describe
import sys


class Scheduler(Object):
    queueLength: int
    status: StatusSched
    podQueue: Set["mpod.Pod"]
    # debug_var: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queueLength = 0
        # self.debug_var = False
        self.status = STATUS_SCHED["Changed"]

    