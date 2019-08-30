from poodle import planned
from guardctl.misc.const import *
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Controller import Controller
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.base import HasLimitsRequests, HasLabel
from guardclt.model.system.globals import GlobalVar


class Pod(HasLabel, HasLimitsRequests):
    def __init__(self, value=""):
        super().__init__(self, value)
        self.status_phase  = STATUS_SERV_PENDING
    # k8s attributes
    metadata_ownerReferences__name: String
    spec_priorityClassName: String

    # internal model attributes
    ownerReferences: Controller
    targetService: "Service"
    atNode: Node
    toNode: Node
    status: StatusPod
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    spec_nodeName: String
    # amountOfActiveRequests: int # For requests
    priorityClass: PriorityClass
    status_phase: String
    TARGET_SERVICE_NULL = Service.SERVICE_NULL

    def __init__(self, value):
        super().__init__(value)
        self.memRequest = -1
        self.cpuRequest = -1
        self.memLimit = -1
        self.cpuLimit = -1
        self.priority = 0
        self.targetService = self.TARGET_SERVICE_NULL
        self.toNode = Node.NODE_NULL
        self.atNode = Node.NODE_NULL
        # self.amountOfActiveRequests = 0 # For Requests

    def hook_after_load(self, object_space):
        nodes = filter(lambda x: isinstance(x, Node) and self.spec_nodeName == x.metadata_name, object_space)
        self.atNode = nodes[0]
        
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
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
        assert podPending in scheduler1.podQueue
        assert podPending.status_phase == STATUS_POD_PENDING 
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass 
        assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podToBeReplaced.status_phase == STATUS_POD_RUNNING 
        podToBeReplaced.status_phase == STATUS_POD_KILLING

    @planned
    def connect_pod_service_labels(self, 
            pod: Pod,  
            service: Service, 
            label: Label):
        # TODO: full selector support
        assert pod.targetService == pod.TARGET_SERVICE_NULL
        assert label in pod.metadata_labels
        assert label in service.spec_selector
        pod.targetService = service
        service.amountOfActivePods += 1
    
    @planned 
    def fill_priority_class_object(self,
            pod: Pod,
            pclass: PriorityClass):
        assert pod.spec_priorityClassName == pclass.metadata_name
        pod.priorityClass = pclass

    @planned(cost=100)
    def MarkPodAsOverwhelmingMemLimits(self, podTobeKilled: Pod,nodeOfPod: Node):
        assert podTobeKilled.memLimitsStatus == STATUS_LIM_MET
        assert nodeOfPod == podTobeKilled.atNode
        assert podTobeKilled.memLimit <  podTobeKilled.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits += 1
        podTobeKilled.memLimitsStatus = STATUS_LIM_EXCEEDED
        
    @planned(cost=100)
    def MarkPodAsNonoverwhelmingMemLimits(self, podTobeReanimated: Pod,
        nodeOfPod: Node, globalVar1: GlobalVar):            
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimitsStatus == STATUS_LIM_EXCEEDED
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimit >  podTobeReanimated.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits -= 1
        podTobeReanimated.memLimitsStatus = STATUS_LIM_MET
        
    @planned(cost=100)
    def MemoryErrorKillPodOverwhelmingLimits(self,
    nodeOfPod: Node,
    pod1TobeKilled: Pod
    ):
        assert pod1TobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert pod1TobeKilled.memLimitsStatus == STATUS_LIM_EXCEEDED 
        pod1TobeKilled.status_phase = STATUS_POD_KILLING


    @planned(cost=100)
    def MemoryErrorKillPodNotOverwhelmingLimits(self,
        nodeOfPod: Node,
        podTobeKilled: Pod):
        assert podTobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert podTobeKilled.memLimitsStatus == STATUS_LIM_MET

        podTobeKilled.status_phase = STATUS_POD_KILLING
    
    @planned(cost=100)
    def KillPod(self,
            podBeingKilled : Pod,
            nodeWithPod : Node,
            serviceOfPod: Service,
            globalVar1: GlobalVar,
            scheduler1: Scheduler,
            amountOfActivePodsPrev: int
            
         ):
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.targetService == serviceOfPod
        assert podBeingKilled.status_phase ==  STATUS_POD_KILLING
        assert podBeingKilled.amountOfActiveRequests == 0
        assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentRealMemConsumption -= podBeingKilled.realInitialMemConsumption
        nodeWithPod.currentRealCpuConsumption -= podBeingKilled.realInitialCpuConsumption
        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -=  podBeingKilled.cpuRequest
        globalVar1.currentFormalMemConsumption -= podBeingKilled.memRequest
        globalVar1.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        podBeingKilled.status_phase =  STATUS_POD_FAILED
        scheduler1.podQueue.add(podBeingKilled)
        scheduler1.status_phase = STATUS_SCHED_CHANGED 

    # Scheduler effects

    @planned(cost=100)
    def SelectNode(self, 
        pod1: Pod,
        nullNode: Node,
        anyNode: Node):
        assert pod1.toNode == Node.NODE_NULL
        pod1.toNode = anyNode

    @planned(cost=100)
    def StartPod(self, 
        podStarted: Pod,
        node1: Node,
        scheduler1: Scheduler,
        serviceTargetForPod: Service,
        globalVar1: GlobalVar
        ):

        assert podStarted in scheduler1.podQueue
        assert podStarted.toNode == node1
        assert podStarted.targetService == serviceTargetForPod
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node1.currentFormalCpuConsumption + podStarted.cpuRequest < node1.cpuCapacity + 1
        assert node1.currentFormalMemConsumption + podStarted.memRequest < node1.memCapacity + 1

        node1.currentFormalCpuConsumption += podStarted.cpuRequest
        node1.currentFormalMemConsumption += podStarted.memRequest
        globalVar1.currentFormalCpuConsumption += podStarted.cpuRequest
        globalVar1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node1        
        scheduler1.queueLength -= 1
        scheduler1.podQueue.remove(podStarted)
 
        serviceTargetForPod.amountOfActivePods += 1
        podStarted.status_phase = STATUS_POD_RUNNING 
        serviceTargetForPod.status_phase = STATUS_SERV_STARTED
           
    @planned(cost=1000)
    def ScheduleQueueProcessed1(self, scheduler1: Scheduler):
        scheduler1.queueLength -= 1

        #to-do: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
    
    @planned(cost=100)
    def ScheduleQueueProcessed(self, scheduler1: Scheduler):
        assert  scheduler1.queueLength == 0
        scheduler1.status_phase = STATUS_SCHED_CLEAN


