import sys
from typing import Set

from poodle import *

NULL='null'

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
    preemptionPolicy = Property(Type)
    
class ContainerConfig(Object):
    service: "Service"
    daemonSet: "DaemonSet"
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    memLimit: int
    cpuLimit: int
    type = Property(Type)
    memRequest: int
    cpuRequest: int
   
class Node(Object):
    cpuCapacity: int
    memCapacity: int
    memCapacityBarier: int
    status = Property(Status)
    state = Property(State)
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
    issue = Property(Type)
    lastNodeUsedByRRalg = Property(Node)
    lastNodeUsedByPodRRalg = Property(Node)
    amountOfNodes: int
    schedulerStatus = Property(Status)
    amountOfPods: int
    queueLength: int
         
class Calculation(Object):
    id: int
    value: int

class Pod(Object):
    podId: int
    podConfig = Property(ContainerConfig)
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    atNode = Property(Node)
    toNode = Property(Node)
    status = Property(Status)
    state = Property(State)
    bindedToNode = Property(Node)
    # podNotOverwhelmingLimits: bool
    memLimit: int
    memLimitsStatus = Property(Status)
    cpuLimit: int
    cpuLimitsStatus = Property(Status)
    type = Property(Type)
    _label = ""
    memRequest: int
    cpuRequest: int
    targetService = Property("Service")
    amountOfActiveRequests: int
    firstNodeForRRAlg = Property(Node)
    counterOfNodesPassed: int
    priorityClass = Property(PriorityClass)

    def __str__ (self): return str(self.value)
    
class Service(Object):
    lastPod = Property(Pod)
    atNode = Property(Node)
    _label = ""
    amountOfActivePods: int
    status = Property(Status)

class DaemonSet(Object):
    lastPod = Property(Pod)
    atNode = Property(Node)
    _label = ""
    amountOfActivePods: int
    status = Property(Status)

class Container(Object):
    hasPod = Property(Pod)
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