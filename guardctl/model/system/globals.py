from poodle import Object
from guardctl.model.system.primitives import Type, Status
from guardctl.model.kinds.Node import Node


class GlobalVar(Object):
    numberOfRejectedReq: int
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    memCapacity: int
    cpuCapacity: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    issue: Type
    lastNodeUsedByRRalg: Node
    lastNodeUsedByPodRRalg: Node
    amountOfNodes: int
    schedulerStatus: Status
    amountOfPods: int
    queueLength: int
    is_service_interrupted: bool
    is_depl_interrupted: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_service_interrupted = False
        