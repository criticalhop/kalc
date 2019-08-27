from typing import Set

from poodle import Object

NULL = 'null'


class Type(Object):
    pass

class Status(Object):
    sequence: int

        STATUSREQATSTART = Status()
        STATUSREQATLOADBALANCER = Status()
        STATUSREQATKUBEPROXY = Status()
        STATUSREQATPODINPUT = Status()
        STATUSREQMEMRESOURCECONSUMED = Status()
        STATUSREQCPURESOURCECONSUMED = Status()
        STATUSREQRESOURCESCONSUMED = Status()
        STATUSREQDIRECTEDTOPOD = Status()
        STATUSREQREQUESTPIDTOBEENDED = Status()
        STATUSREQCPURESOURCERELEASED = Status()
        STATUSREQMEMRESOURCERELEASED = Status()
        STATUSREQRESOURCESRELEASED = Status()
        STATUSREQREQUESTTERMINATED = Status()
        STATUSREQREQUESTFINISHED = Status()
        STATUSPODATCONFIG = Status()
        STATUSPODREADYTOSTART = Status()
        STATUSPODACTIVE = Status()
        STATUSPODPENDING = Status()
        STATUSPODATMANUALCREATION = Status()
        STATUSPODDIRECTEDTONODE = Status()
        STATUSPODCPUCONSUMED = Status()
        STATUSPODRESOURCEFORMALCONSUMPTIONFAILED = Status()
        STATUSPODFAILEDTOSTART = Status()
        STATUSPODREADYTOSTART2 = Status()
        STATUSPODMEMCONSUMED = Status()
        STATUSPODMEMCONSUMEDFAILED = Status()
        STATUSPODBINDEDTONODE = Status()
        STATUSPODRUNNING = Status()
        STATUSPODSUCCEEDED = Status() # MAY BE LOST BE CAREFUL
        STATUSPODKILLING = Status()
        STATUSPODFAILED = Status()
        STATUSNODERUNNING = Status()
        STATUSNODESUCCEDED = Status()
        STATUSPODPENDING = Status()
        STATUSNODEDELETED = Status()
        STATUSPODINACTIVE = Status()
        STATUSNODEACTIVE = Status()
        STATUSNODEINACTIVE = Status()
        STATUSREQDIRECTEDTONODE = Status()
        STATUSREQNODECAPACITYOVERWHELMED = Status()
        STATUSLIMMET = Status()
        STATUSLIMOVERWHELMED = Status()
        TEST = Status()
        STATUSPODTOBETERMINATED = Status()
        STATUSPODTERMINATED = Status()
        STATUSSERVPENDING = Status()
        STATUSSERVSTARTED = Status()
        STATUSSERVINTERRUPTED = Status()
        STATUSREQRUNNING = Status()
        STATUSPODINITIALCONRELEASED = Status()
        STATUSPODGLOBALMEMCONSUMED = Status()
        STATUSPODGLOBALCPUCONSUMED = Status()
        STATUSPODFORMALCONRELEASED = Status()
        STATUSSCHEDCLEAN = Status()
        STATUSSCHEDCHANGED = Status()
        STATUSPODREADYTOSTART = Status()
        STATUSPODFINISHEDPLACEMENT = Status()

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

    def __str__(self): return str(self.value)


class Service(Object):
    lastPod: Pod
    atNode: Node
    _label = ""
    amountOfActivePods: int
    status: Status


class DaemonSet(Object):
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


class Deamonset(Object):
    podList: Set[Pod]


class NameSpace(Object):
    cpuLimitRange: int
    memLimitRange: int

