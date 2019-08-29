from typing import Set
from guardctl.misc.const import *

from poodle import Object

NULL = 'null'

class String(Object):
    pass
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
    metadata_name: String

    priority: int
    preemptionPolicy: Type


class Label(Object):
    pass

class HasLabel(Object):
    metadata_labels: Set[Label]
    metadata_name: String


class Node(HasLabel):
    labels: Set["Label"]
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

class Controller(HasLabel):
    "Kubernetes controller abstract class"
    pass

class Pod(HasLabel):
    # k8s attributes
    metadata_ownerReferences__name: String
    spec_priorityClassName: String
    spec_priority: int # TODO: priority support/setter

    # internal model attributes
    type: Type
    ownerReferences: Controller
    memRequest: int
    cpuRequest: int
    targetService: "Service"
    atNode: Node
    toNode: Node
    status: StatusPod
    state: State

    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    memLimit: int
    memLimitsStatus: StatusLim
    cpuLimit: int
    cpuLimitsStatus: StatusLim
    amountOfActiveRequests: int
    firstNodeForRRAlg: Node
    counterOfNodesPassed: int
    priorityClass: PriorityClass

    @setter
    def status_phase(self, value):
        if value == "Running":
            self.state = STATE_POD_RUNNING
        elif value == "Inactive":
            self.state = STATE_POD_INACTIVE 
        elif value  == "Pending":
            self.state = STATE_POD_PENDING
        elif value == "Succeeded":
            self.state = STATE_POD_SUCCEEDED
        else:
            raise NotImplementedError("Unsupported pod phase %s" % str(podk['status']['phase']))

    def __str__(self): return str(self.value)

class Service(HasLabel):
    spec_selector: Set[Label]
    lastPod: Pod
    atNode: Node
    amountOfActivePods: int
    status: StatusServ

class Deployment(Controller):
    spec_replicas: int

class DaemonSet(Controller):
    lastPod: Pod
    atNode: Node
    amountOfActivePods: int
    status: Status



class Scheduler(Object):
    queueLength: int
    status: StatusSched
    podQueue: Set[Pod]

class NameSpace(Object):
    cpuLimitRange: int
    memLimitRange: int