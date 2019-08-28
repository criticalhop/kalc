from typing import Set

from poodle import Object

NULL = 'null'


class Type(Object):
    pass

class Status(Object):
    sequence: int

class StatusPod(Object):
    sequence: int

class StatusNode(Object):
    sequence: int

class StatusReq(Object):
    sequence: int

class StatusSched(Object):
    sequence: int
    
class StatusServ(Object):
    sequence: int
    
class StatusLim(Object):
    sequence: int

class State(Object):
    sequence: int


class PriorityClass(Object):
    priority: int
    preemptionPolicy: Type


class Node(Object):
    cpuCapacity: int
    memCapacity: int
    memCapacityBarier: int
    status: StatusNode
    state: State
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    AmountOfPodsOverwhelmingMemLimits: int
    podAmount: int
    type: Type


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

class Controller(Object):
    "Kubernetes controller abstract class"
    pass
class Pod(Object):
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    atNode: Node
    toNode: Node
    status: StatusPod
    state: State
    memLimit: int
    memLimitsStatus: StatusLim
    cpuLimit: int
    cpuLimitsStatus: StatusLim
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
    pass

class Service(Object):
    lastPod: Pod
    atNode: Node
    labels: Set[Label]
    _label = ""
    amountOfActivePods: int
    status: StatusServ
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



class Scheduler(Object):
    queueLength: int
    status: StatusSched
    podQueue: Set[Pod]

class NameSpace(Object):
    cpuLimitRange: int
    memLimitRange: int