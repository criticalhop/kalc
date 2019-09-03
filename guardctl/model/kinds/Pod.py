from poodle import planned
from logzero import logger
from guardctl.misc.const import *
from guardctl.model.kinds.Node import Node
import guardctl.model.kinds.Service as mservice
import guardctl.model.system.Scheduler as mscheduler
import guardctl.model.kinds.Node as mnode
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Controller import Controller
from guardctl.model.system.primitives import Label

from guardctl.model.system.base import HasLimitsRequests, HasLabel
from guardctl.model.system.globals import GlobalVar


class Pod(HasLabel, HasLimitsRequests):
    # k8s attributes
    metadata_ownerReferences__name: str
    spec_priorityClassName: str

    # internal model attributes
    ownerReferences: Controller
    TARGET_SERVICE_NULL = mservice.Service.SERVICE_NULL
    targetService: "mservice.Service"
    atNode: "mnode.Node" 
    toNode: "mnode.Node" 
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    spec_nodeName: str
    priorityClass: PriorityClass
    status_phase: str
    isNull: bool
    # amountOfActiveRequests: int # For requests

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = 0
        self.targetService = self.TARGET_SERVICE_NULL
        self.toNode = mnode.Node.NODE_NULL
        self.atNode = mnode.Node.NODE_NULL
        self.status_phase = STATUS_POD_PENDING
        self.isNull = True
        # self.amountOfActiveRequests = 0 # For Requests

    def hook_after_load(self, object_space):
        nodes = list(filter(lambda x: isinstance(x, mnode.Node) and self.spec_nodeName == x.metadata_name, object_space))
        if nodes:
            self.atNode = nodes[0]
        else:
            logger.warning("Orphan Pod loaded")

    def __repr__(self):
        return 'Podname : ' + str(self._get_value()) 
        
    # we just ignore priority for now
    # @property
    # def spec_priority(self):
    #     pass
    # @spec_priority.setter
    # def spec_priority(self, value):
    #     if value > 1000: value = 1000
    #     self.priority = value

    def __str__(self): return str(self._get_value())

    @planned(cost=100)
    def SetDefaultMemRequestForPod(self,
        pod1: "Pod",
        memLimit: int
        ):
            assert pod1.memRequest == -1
            assert pod1.memLimit > -1
            assert memLimit == pod1.memLimit
            
            pod1.memRequest = memLimit

    @planned(cost=100)
    def SetDefaultCpuRequestForPod(self,
        pod1: "Pod",
        cpuLimit: int
        ):
            assert pod1.cpuLimit > -1
            assert pod1.cpuRequest == -1
            assert cpuLimit == pod1.cpuLimit 
            
            pod1.cpuRequest = cpuLimit
    
    @planned(cost=100)
    def SetDefaultMemLimitForPod(self,
        pod1: "Pod",
        node1: "mnode.Node" ,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert node1 == pod1.atNode
            assert memCapacity == node1.memCapacity
            pod1.memLimit = memCapacity
            
    @planned(cost=100)
    def SetDefaultCpuLimitForPod(self,
        pod1: "Pod",
        node1: "mnode.Node" ,
        cpuCapacity: int
        ):
            assert pod1.cpuLimit == -1
            assert node1 == pod1.atNode
            assert cpuCapacity == node1.cpuCapacity
            
            pod1.cpuLimit = cpuCapacity   
    @planned(cost=100)
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node1: "mnode.Node" ,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert memCapacity == node1.memCapacity
            pod1.toNode = node1
            pod1.memLimit = memCapacity
            
    @planned(cost=100)
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node1: "mnode.Node" ,
        cpuCapacity: int):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity

    @planned(cost=100)
    def SetDefaultCpuLimitPerLimitRange(self,
        pod1: "Pod",
        node1: "mnode.Node" ,
        cpuCapacity: int,
        ):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity

    @planned(cost=100)
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                node1: "mnode.Node" , # unused
                scheduler1: "mscheduler.Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
        # assert podPending in scheduler1.podQueue
        # assert podPending.toNode == Node.NODE_NULL
        assert podPending.status_phase == STATUS_POD_PENDING 
        # assert priorityClassOfPendingPod == podPending.priorityClass
        # assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass 
        # # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        # assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        # assert podToBeReplaced.status_phase == STATUS_POD_RUNNING 
        podToBeReplaced.status_phase = STATUS_POD_KILLING

    @planned(cost=100)
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_defined(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "mnode.Node" , # unused
                scheduler1: "mscheduler.Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
        # assert podPending in scheduler1.podQueue
        # assert podPending.toNode == nodeForPodPending
        # assert nodeForPodPending.isNull == False
        # assert podToBeReplaced.atNode == nodeForPodPending
        assert podPending.status_phase == STATUS_POD_PENDING 
        # assert priorityClassOfPendingPod == podPending.priorityClass
        # assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass 
        # # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        # assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        # assert podToBeReplaced.status_phase == STATUS_POD_RUNNING 
        podToBeReplaced.status_phase = STATUS_POD_KILLING

    @planned
    def connect_pod_service_labels(self, 
            pod: "Pod",  
            service: "mservice.Service", 
            label: Label):
        # TODO: full selector support
        assert pod.targetService == pod.TARGET_SERVICE_NULL
        assert label in pod.metadata_labels
        assert label in service.spec_selector
        pod.targetService = service
        service.amountOfActivePods += 1
        service.status = STATUS_SERV_STARTED
    
    @planned 
    def fill_priority_class_object(self,
            pod: "Pod",
            pclass: PriorityClass):
        assert pod.spec_priorityClassName == pclass.metadata_name
        pod.priorityClass = pclass

    @planned(cost=100)
    def MarkPodAsOverwhelmingMemLimits(self, podTobeKilled: "Pod",nodeOfPod: "mnode.Node" ):
        assert podTobeKilled.memLimitsStatus == STATUS_LIM_MET
        assert nodeOfPod == podTobeKilled.atNode
        assert podTobeKilled.memLimit <  podTobeKilled.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits += 1
        podTobeKilled.memLimitsStatus = STATUS_LIM_EXCEEDED
        
    @planned(cost=100)
    def MarkPodAsNonoverwhelmingMemLimits(self, podTobeReanimated: "Pod",
        nodeOfPod: "mnode.Node" , globalVar1: GlobalVar):            
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimitsStatus == STATUS_LIM_EXCEEDED
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimit >  podTobeReanimated.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits -= 1
        podTobeReanimated.memLimitsStatus = STATUS_LIM_MET
        
    @planned(cost=100)
    def MemoryErrorKillPodOverwhelmingLimits(self,
    nodeOfPod: "mnode.Node" ,
    pod1TobeKilled: "Pod"
    ):
        assert pod1TobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert pod1TobeKilled.memLimitsStatus == STATUS_LIM_EXCEEDED 
        pod1TobeKilled.status_phase = STATUS_POD_KILLING


    @planned(cost=100)
    def MemoryErrorKillPodNotOverwhelmingLimits(self,
        nodeOfPod: "mnode.Node" ,
        podTobeKilled: "Pod"):
        assert podTobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert podTobeKilled.memLimitsStatus == STATUS_LIM_MET

        podTobeKilled.status_phase = STATUS_POD_KILLING
    
    @planned(cost=100)
    def KillPod(self,
            podBeingKilled : "Pod",
            nodeWithPod : "mnode.Node" ,
            serviceOfPod: "mservice.Service",
            globalVar1: "GlobalVar",
            scheduler1: "mscheduler.Scheduler",
            amountOfActivePodsPrev: int
            
         ):
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.targetService == serviceOfPod
        assert podBeingKilled.status_phase ==  STATUS_POD_KILLING
        # assert podBeingKilled.amountOfActiveRequests == 0 #for requests
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
        scheduler1.status = STATUS_SCHED_CHANGED 

    # Scheduler effects



Pod.POD_NULL = Pod("NULL")
Pod.POD_NULL.isNull = True

