from typing import Set

from poodle import Object

NULL = 'null'


class Type(Object):
    pass


class Kind(Object):
    pass


class Mode(Object):
    pass


class Status(Object):
    sequence: int


class State(Object):
    sequence: int


class PriorityClass(Object):
    priority: int
    preemptionPolicy: Type


class ContainerConfig(Object):
    service: "Service"
    daemonSet: "DaemonSet"
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    memLimit: int
    cpuLimit: int
    type: Type
    memRequest: int
    cpuRequest: int


class Node(Object):
    cpuCapacity: int
    memCapacity: int
    memCapacityBarier: int
    status: Status
    state: State
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    AmountOfPodsOverwhelmingMemLimits: int
    podAmount: int
    type: Type


class EntityType(Object):
    pass


class GlobalVar(Object):
    numberOfRejectedReq: int
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    memCapacity: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    issue: Type
    lastNodeUsedByRRalg: Node
    lastNodeUsedByPodRRalg: Node
    amountOfNodes: int
    schedulerStatus: Status
    amountOfPods: int
    queueLength: int


class Calculation(Object):
    id: int
    value: int

class Controller(Object):
    "Kubernetes controller abstract class"
    pass
class Pod(Object):
    podId: int
    podConfig: ContainerConfig
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    atNode: Node
    toNode: Node
    status: Status
    state: State
    bindedToNode: Node
    # podNotOverwhelmingLimits: bool
    memLimit: int
    memLimitsStatus: Status
    cpuLimit: int
    cpuLimitsStatus: Status
    type: Type
    _label = ""
    memRequest: int
    cpuRequest: int
    targetService: "Service"
    amountOfActiveRequests: int
    firstNodeForRRAlg: Node
    counterOfNodesPassed: int
    priorityClass: PriorityClass
    ownerReferences: Controller

    def __str__(self): return str(self.value)

class Label(Object):
    name: str
    value: str

class Service(Object):
    lastPod: Pod
    atNode: Node
    labels: Set[Label]
    _label = ""
    amountOfActivePods: int
    status: Status
    selector: Label

class Deployment(Controller):
    labels: Set[Label]
    replicas: int

class DaemonSet(Controller):
    lastPod: Pod
    atNode: Node
    _label = ""
    amountOfActivePods: int
    status: Status


class Container(Object):
    hasPod: Pod
    cpuRequest: int
    memRequest: int
    cpuLimit: int
    memLimit: int
    config: ContainerConfig


class Scheduler(Object):
    queueLength: int
    # active = Bool
    status: Status
    podQueue: Set[Pod]

class NameSpace(Object):
    cpuLimitRange: int
    memLimitRange: int

