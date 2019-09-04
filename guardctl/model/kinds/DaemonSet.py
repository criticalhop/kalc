from guardctl.model.system.Controller import Controller
from guardctl.model.system.base import HasLimitsRequests
from guardctl.model.kinds.Node import Node
import guardctl.model.kinds.Pod as mpod
from guardctl.model.system.primitives import Status
from guardctl.misc.const import *
from poodle import *
from typing import Set

class DaemonSet(Controller, HasLimitsRequests):
    lastPod: "mpod.Pod"
    amountOfActivePods: int
    status: Status
    podList: Set["mpod.Pod"]


    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

    def hook_after_create(self, object_space):
        nodes = filter(lambda x: isinstance(x, Node), object_space)
        i = 0
        for node in nodes:
            i += 1
            new_pod = mpod.Pod()
            new_pod.metadata_name = str(self.metadata_name) + '-' + str(i)
            new_pod.toNode = node
            new_pod.cpuRequest = self.cpuRequest
            new_pod.memRequest = self.memRequest
            new_pod.cpuLimit = self.cpuLimit
            new_pod.memLimit = self.memLimit
            new_pod.status_phase = STATUS_POD_PENDING
            self.podList.add(new_pod)
            object_space.append(new_pod)

