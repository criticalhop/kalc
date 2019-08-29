from poodle import planned
from guardctl.misc.const import *
from guardctl.model.system.primitives import String, Type, Status
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Controller import Controller
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.base import HasLimitsRequests, HasLabel



class Pod(HasLabel, HasLimitsRequests):
    def __init__(self, value):
        super().__init__(self, value)
        self.status = STATUS_POD_PENDING
    # k8s attributes
    metadata_ownerReferences__name: String
    spec_priorityClassName: String

    # internal model attributes
    type: Type
    ownerReferences: Controller
    targetService: "Service"
    atNode: Node
    toNode: Node
    status: StatusPod
    state: State

    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    amountOfActiveRequests: int
    firstNodeForRRAlg: Node
    counterOfNodesPassed: int
    priorityClass: PriorityClass

    TARGET_SERVICE_NULL = Service("NULL")

    def __init__(self, value):
        super().__init__(value)
        self.memRequest = -1
        self.cpuRequest = -1
        self.memLimit = -1
        self.cpuLimit = -1
        self.priority = 0
        self.targetService = self.TARGET_SERVICE_NULL
        
    # we just ignore priority for now
    # @property
    # def spec_priority(self):
    #     pass
    # @spec_priority.setter
    # def spec_priority(self, value):
    #     if value > 1000: value = 1000
    #     self.priority = value

    @property
    def status_phase(self):
        pass
    @status_phase.setter
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
            raise NotImplementedError("Unsupported pod phase %s" % str(value))

    def __str__(self): return str(self.value)

    @planned(cost=100)
    def SetDefaultMemRequestForPod(self,
        pod1: Pod,
        memLimit: int
        ):
            assert pod1.memRequest == -1
            assert pod1.memLimit > -1
            assert memLimit == pod1.memLimit
            
            pod1.memRequest = memLimit

    @planned(cost=100)
    def SetDefaultCpuRequestForPod(self,
        pod1: Pod,
        cpuLimit: int
        ):
            assert pod1.cpuLimit > -1
            assert pod1.cpuRequest == -1
            assert cpuLimit == pod1.cpuLimit 
            
            pod1.cpuRequest = cpuLimit
    
    @planned(cost=100)
    def SetDefaultMemLimitForPod(self,
        pod1: Pod,
        node1: Node,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert node1 == pod1.atNode
            assert memCapacity == node1.memCapacity
            pod1.memLimit = memCapacity
            
    @planned(cost=100)
    def SetDefaultCpuLimitForPod(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int
        ):
            assert pod1.cpuLimit == -1
            assert node1 == pod1.atNode
            assert cpuCapacity == node1.cpuCapacity
            
            pod1.cpuLimit = cpuCapacity   
    @planned(cost=100)
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: Pod,
        node1: Node,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert memCapacity == node1.memCapacity
            pod1.toNode = node1
            pod1.memLimit = memCapacity
            
    @planned(cost=100)
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity

    @planned(cost=100)
    def SetDefaultCpuLimitPerLimitRange(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int,
        ):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity

    @planned(cost=100)
    def EvictAndReplaceLessPrioritizedPod(self,
                podPending: Pod,
                podToBeReplaced: Pod,
                node1: Node,
                scheduler1: Scheduler,
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass,
                preemptionPolicyOfPendingPod: Type,
                preemptionPolicyOfPodToBeReplaced: Type,
                statustest: Status,
                podtypetest: Type
                ):
        assert podPending in scheduler1.podQueue
        assert podPending.status == STATUS_POD_PENDING 
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass 
        assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podToBeReplaced.status == STATUS_POD_ACTIVE
        podToBeReplaced.status = STATUS_POD_KILLING