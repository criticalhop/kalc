import sys
from poodle import planned
from logzero import logger
from kalc.model.system.base import HasLimitsRequests, HasLabel
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.model.system.primitives import TypeServ
from kalc.model.system.Controller import Controller
from kalc.model.system.primitives import Label
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from kalc.model.scenario import ScenarioStep, describe
from kalc.misc.const import *
from kalc.misc.problem import ProblemTemplate
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem

class KubernetesModel(ProblemTemplate):
    def problem(self):
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        self.globalVar = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

    @planned(cost=1)
    def Mark_service_as_started(self,
                service1: Service,
                scheduler: "Scheduler",
                globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert service1.amountOfActivePods > 0
        assert service1.isNull == False
        # assert globalVar.block_node_outage_in_progress == False
        service1.status = STATUS_SERV["Started"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Mark service as started",
            parameters={},
            probability=1.0,
            affected=[describe(service1)]
        )
    @planned(cost=1)
    def Fill_priority_class_object(self,
            pod: "Pod",
            pclass: PriorityClass,
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert pod.spec_priorityClassName == pclass.metadata_name
        pod.priorityClass = pclass

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="no description provided",
            parameters={},
            probability=1.0,
            affected=[describe(pod)]
        )
    @planned(cost=1)
    def SetDefaultMemRequestForPod(self,
        pod1: "Pod",
        memLimit: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.memRequest == -1
            assert pod1.memLimit > -1
            assert memLimit == pod1.memLimit

            pod1.memRequest = memLimit

            return ScenarioStep(
                name=sys._getframe().f_code.co_name,
                subsystem=self.__class__.__name__,
                description="Setting default memory request for pod",
                parameters={"currentMemoryRequest": -1, "newMemoryRequest": str(pod1.memLimit)},
                probability=1.0,
                affected=[describe(pod1)]
            )

    @planned(cost=1)
    def SetDefaultCpuRequestForPod(self,
        pod1: "Pod",
        cpuLimit: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.cpuLimit > -1
            assert pod1.cpuRequest == -1
            assert cpuLimit == pod1.cpuLimit

            pod1.cpuRequest = cpuLimit

            return ScenarioStep(
                name=sys._getframe().f_code.co_name,
                subsystem=self.__class__.__name__,
                description="Setting default cpu request for pod",
                parameters={"currentCpuRequest": -1, "newCpuRequest": str(pod1.cpuLimit)},
                probability=1.0,
                affected=[describe(pod1)]
            )

    @planned(cost=1)
    def SetDefaultMemLimitForPod(self,
        pod1: "Pod",
        node: "Node" ,
        memCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.memLimit == -1
            assert node == pod1.atNode
            assert memCapacity == node.memCapacity
            pod1.memLimit = memCapacity

            return ScenarioStep(
                name=sys._getframe().f_code.co_name,
                subsystem=self.__class__.__name__,
                description="Setting default memory limit for pod",
                parameters={"currentMemoryLimit": -1, "newMemoryLimit": str(pod1.memLimit)},
                probability=1.0,
                affected=[describe(pod1)]
            )

    @planned(cost=1)
    def SetDefaultCpuLimitForPod(self,
        pod1: "Pod",
        node: "Node" ,
        cpuCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.cpuLimit == -1
            assert node == pod1.atNode
            assert cpuCapacity == node.cpuCapacity

            pod1.cpuLimit = cpuCapacity

            return ScenarioStep(
                name=sys._getframe().f_code.co_name,
                subsystem=self.__class__.__name__,
                description="Setting default cpu limit for pod to node capacity",
                parameters={"currentCpuLimit": -1, "newCpuLimit": str(pod1.cpuLimit)},
                probability=1.0,
                affected=[describe(pod1)]
            )

    @planned(cost=1)
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node: "Node" ,
        memCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.memLimit == -1
            assert memCapacity == node.memCapacity
            pod1.toNode = node
            pod1.memLimit = memCapacity

            return ScenarioStep(
                name=sys._getframe().f_code.co_name,
                subsystem=self.__class__.__name__,
                description="no description provided",
                parameters={},
                probability=1.0,
                affected=[describe(pod1)]
            )

    @planned(cost=1)
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node: "Node" ,
        cpuCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node.cpuCapacity
            pod1.toNode = node
            pod1.cpuLimit = cpuCapacity

            return ScenarioStep(
                name=sys._getframe().f_code.co_name,
                subsystem=self.__class__.__name__,
                description="no description provided",
                parameters={},
                probability=1.0,
                affected=[describe(pod1)]
            )


    @planned(cost=1)
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_defined_byMEM(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "Node" ,
                scheduler: "Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass,
                globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podPending in scheduler.podQueue
        assert podPending.toNode == nodeForPodPending
        assert nodeForPodPending.isNull == False
        assert podToBeReplaced.atNode == nodeForPodPending
        assert podPending.status == STATUS_POD["Pending"]
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass
        # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podPending.memRequest > nodeForPodPending.memCapacity - nodeForPodPending.currentFormalMemConsumption
        assert podToBeReplaced.status == STATUS_POD["Running"]
        podToBeReplaced.status = STATUS_POD["Killing"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Because pod has lower priority, it is getting evicted to make room for new pod",
            parameters={"podPending": describe(podPending), "podToBeReplaced": describe(podToBeReplaced)},
            probability=1.0,
            affected=[describe(podPending), describe(podToBeReplaced)]
        )

    @planned(cost=1)
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_defined_byCPU(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "Node" ,
                scheduler: "Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass,
                globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        
        # assert globalVar.block_node_outage_in_progress == False
        assert podPending in scheduler.podQueue
        assert podPending.toNode == nodeForPodPending
        assert nodeForPodPending.isNull == False
        assert podToBeReplaced.atNode == nodeForPodPending
        assert podPending.status == STATUS_POD["Pending"]
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass
        # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podPending.cpuRequest > nodeForPodPending.cpuCapacity - nodeForPodPending.currentFormalCpuConsumption
        assert podToBeReplaced.status == STATUS_POD["Running"]
        podToBeReplaced.status = STATUS_POD["Killing"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Because pod has lower priority, it is getting evicted to make room for new pod",
            parameters={"podPending": describe(podPending), "podToBeReplaced": describe(podToBeReplaced)},
            probability=1.0,
            affected=[describe(podPending), describe(podToBeReplaced)]
        )
        
    @planned(cost=1)
    def Mark_Pod_As_Exceeding_Mem_Limits(self, podTobeKilled: "Pod",nodeOfPod: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podTobeKilled.memLimitsStatus == STATUS_LIM["Limit Met"]
        assert nodeOfPod == podTobeKilled.atNode
        assert podTobeKilled.memLimit <  podTobeKilled.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits += 1
        podTobeKilled.memLimitsStatus = STATUS_LIM["Limit Exceeded"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="no description provided",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def Mark_Pod_As_Not_Exceeding_Mem_Limits(self, podTobeReanimated: "Pod",
        nodeOfPod: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimitsStatus == STATUS_LIM["Limit Exceeded"]
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimit >  podTobeReanimated.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits -= 1
        podTobeReanimated.memLimitsStatus = STATUS_LIM["Limit Met"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="no description provided",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def MemoryErrorKillPodExceedingLimits(self,
        nodeOfPod: "Node" ,
        pod1TobeKilled: "Pod",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert pod1TobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert pod1TobeKilled.memLimitsStatus == STATUS_LIM["Limit Exceeded"]
        pod1TobeKilled.status = STATUS_POD["Killing"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="no description provided",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def MemoryErrorKillPodNotExceedingLimits(self,
        nodeOfPod: "Node" ,
        podTobeKilled: "Pod",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podTobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert podTobeKilled.memLimitsStatus == STATUS_LIM["Limit Met"]

        podTobeKilled.status = STATUS_POD["Killing"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="no description provided",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            serviceOfPod: "Service",
            scheduler: "Scheduler",
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled in serviceOfPod.podList
        assert podBeingKilled.status == STATUS_POD["Killing"]
        # assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        assert podBeingKilled.hasService == True 
        assert podBeingKilled.hasDeployment == False #TODO add this for branching
        assert podBeingKilled.hasDaemonset == False #TODO add this for branching
        assert podBeingKilled.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert podBeingKilled.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        #TODO: make sure that calculation excude situations that lead to negative number in the result

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        serviceOfPod.amountOfPodsInQueue += 1
        nodeWithPod.amountOfActivePods -= 1 
        podBeingKilled.status = STATUS_POD["Pending"]
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL
        scheduler.podQueue.add(podBeingKilled)

        scheduler.status = STATUS_SCHED["Changed"]
        scheduler.queueLength += 1

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=1)
    def KillPod_IF_Deployment_isNotNUll_Service_isNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            pods_deployment: Deployment,
            nodeWithPod : "Node" ,
            scheduler: "Scheduler",
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.status == STATUS_POD["Killing"]
        assert podBeingKilled in pods_deployment.podList
        assert podBeingKilled.hasService == False 
        assert podBeingKilled.hasDeployment == True 
        assert podBeingKilled.hasDaemonset == False #TODO add this for branching
        assert podBeingKilled.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert podBeingKilled.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        #TODO: make sure that calculation excude situations that lead to negative number in the result

        ## assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        ## assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        nodeWithPod.amountOfActivePods -= 1 
        pods_deployment.amountOfActivePods -= 1  # ERROR HERE
        podBeingKilled.status = STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"]
        scheduler.queueLength += 1
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL
        # scheduler.debug_var = True # TODO DELETEME
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=1)
    def KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            scheduler: "Scheduler",
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.status == STATUS_POD["Killing"]
        assert podBeingKilled.hasService == False  
        assert podBeingKilled.hasDeployment == False 
        assert podBeingKilled.hasDaemonset == False
        assert podBeingKilled.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert podBeingKilled.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        #TODO: make sure that calculation excude situations that lead to negative number in the result

        ## assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        ## assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        nodeWithPod.amountOfActivePods -= 1
        podBeingKilled.status = STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"] # commented, solves
        scheduler.queueLength += 1
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL
        # scheduler.debug_var = True # TODO DELETEME
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=1)
    def KillPod_IF_Deployment_isNotNUll_Service_isNotNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            serviceOfPod: "Service",
            pods_deployment: Deployment,
            nodeWithPod : "Node" ,
            scheduler: "Scheduler",
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.status == STATUS_POD["Killing"]
        assert podBeingKilled in pods_deployment.podList
        assert podBeingKilled in serviceOfPod.podList
        assert podBeingKilled.hasService == True 
        assert podBeingKilled.hasDeployment == True 
        assert podBeingKilled.hasDaemonset == False #TODO add this for branching
        assert podBeingKilled.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert podBeingKilled.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        #TODO: make sure that calculation excude situations that lead to negative number in the result

        ## assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        ## assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        nodeWithPod.amountOfActivePods -= 1 
        pods_deployment.amountOfActivePods -= 1
        serviceOfPod.amountOfActivePods -= 1
        serviceOfPod.amountOfPodsInQueue += 1
        podBeingKilled.status = STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"]
        scheduler.queueLength += 1
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL
        # scheduler.debug_var = True # TODO DELETEME
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=1)
    def KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNotNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            serviceOfPod: "Service",
            pods_daemonset: DaemonSet,
            scheduler: "Scheduler",
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled in serviceOfPod.podList
        assert podBeingKilled.status == STATUS_POD["Killing"]
        assert podBeingKilled in pods_daemonset.podList
        # assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        assert podBeingKilled.hasService == True 
        assert podBeingKilled.hasDeployment == False #TODO add this for branching
        assert podBeingKilled.hasDaemonset == True #TODO add this for branching

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        serviceOfPod.amountOfPodsInQueue += 1
        nodeWithPod.amountOfActivePods -= 1 
        pods_daemonset.amountOfActivePods -= 1
        podBeingKilled.status =  STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"]
        scheduler.queueLength += 1
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=1)
    def KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            pods_daemonset: DaemonSet,
            scheduler: "Scheduler",
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.status == STATUS_POD["Killing"]
        assert podBeingKilled in pods_daemonset.podList
        # assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        assert podBeingKilled.hasService == False 
        assert podBeingKilled.hasDeployment == False  
        assert podBeingKilled.hasDaemonset == True
        assert podBeingKilled.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert podBeingKilled.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        #TODO: make sure that calculation excude situations that lead to negative number in the result

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        nodeWithPod.amountOfActivePods -= 1 
        pods_daemonset.amountOfActivePods -= 1
        podBeingKilled.status =  STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"]
        scheduler.queueLength += 1
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=1)
    def SelectNode(self, 
        pod1: "Pod",
        SelectedNode: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert pod1.toNode == Node.NODE_NULL
        pod1.toNode = SelectedNode
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Selected node for pod placement",
            parameters={"pod": describe(pod1), "node": describe(SelectedNode)},
            probability=1.0,
            affected=[describe(pod1), describe(SelectedNode)]
        )

    @planned(cost=1)
    def StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podStarted.hasService == True 
        assert podStarted.hasDeployment == False #TODO add this for branching
        assert podStarted.hasDaemonset == False  #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in serviceTargetForPod.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        serviceTargetForPod.amountOfPodsInQueue -= 1
        node.amountOfActivePods += 1
        serviceTargetForPod.amountOfActivePods += 1
        podStarted.status = STATUS_POD["Running"] 
        serviceTargetForPod.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )
    
    @planned(cost=1)
    def StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podStarted.hasService == False 
        assert podStarted.hasDeployment == False #TODO add this for branching
        assert podStarted.hasDaemonset == False #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node        
        scheduler.queueLength -= 1
        node.amountOfActivePods += 1 
        scheduler.podQueue.remove(podStarted)
        podStarted.status = STATUS_POD["Running"] 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )

    @planned(cost=1)
    def StartPod_IF_Deployment_isNotNUll_Service_isNotNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        pods_deployment: Deployment,
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podStarted.hasService == True 
        assert podStarted.hasDeployment == True #TODO add this for branching
        assert podStarted.hasDaemonset == False #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in serviceTargetForPod.podList
        assert podStarted in pods_deployment.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        serviceTargetForPod.amountOfActivePods += 1
        serviceTargetForPod.amountOfPodsInQueue -= 1
        pods_deployment.amountOfActivePods += 1 
        podStarted.status = STATUS_POD["Running"] 
        serviceTargetForPod.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )
    
    @planned(cost=1)
    def StartPod_IF_Deployment_isNotNUll_Service_isNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        pods_deployment: Deployment,
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podStarted.hasService == False 
        assert podStarted.hasDeployment == True #TODO add this for branching
        assert podStarted.hasDaemonset == False #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in pods_deployment.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        pods_deployment.amountOfActivePods += 1 
        podStarted.status = STATUS_POD["Running"] 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )

    @planned(cost=1)
    def StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        pods_daemonset: DaemonSet,
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podStarted.hasService == False 
        assert podStarted.hasDeployment == False #TODO add this for branching
        assert podStarted.hasDaemonset == True #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in pods_daemonset.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        pods_daemonset.amountOfActivePods += 1 
        podStarted.status = STATUS_POD["Running"] 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )


    @planned(cost=1)
    def StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNotNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        pods_daemonset: DaemonSet,
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podStarted.hasService == True
        assert podStarted.hasDeployment == False
        assert podStarted.hasDaemonset == True

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in pods_daemonset.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        pods_daemonset.amountOfActivePods += 1
        podStarted.status = STATUS_POD["Running"]
        serviceTargetForPod.amountOfActivePods += 1
        serviceTargetForPod.amountOfPodsInQueue -= 1
        serviceTargetForPod.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )

        #todo: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
    
    @planned(cost=1)
    def SchedulerCleaned(self, 
        scheduler: "Scheduler",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == False
        assert  scheduler.queueLength == 0
        assert globalVar.block_policy_calculated == False
        scheduler.status = STATUS_SCHED["Clean"]
        globalVar.block_policy_calculated = True
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Finished processing pod queue",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=90)
    def Initiate_node_outage(self,
        node_with_outage: "Node",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == False
        # assert globalVar.amountOfNodesDisrupted < globalVar.limitOfAmountOfNodesDisrupted
        assert globalVar.is_node_disrupted == False # TODO: checking ONE node outage! Need fixing
        assert node_with_outage.searchable == True
        assert node_with_outage.status == STATUS_NODE["Active"]
        node_with_outage.status = STATUS_NODE["Killing"]
        globalVar.block_node_outage_in_progress = True
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Outage of Node initiated ",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def Initiate_node_outage_searched(self,
        node_with_outage: "Node",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == False
        # assert globalVar.amountOfNodesDisrupted < globalVar.limitOfAmountOfNodesDisrupted
        assert globalVar.is_node_disrupted == False # TODO: checking ONE node outage! Need fixing
        assert node_with_outage.searchable == True
        assert node_with_outage.status == STATUS_NODE["Active"]
        assert node_with_outage.isSearched == True
        node_with_outage.status = STATUS_NODE["Killing"]
        globalVar.block_node_outage_in_progress = True
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Outage of Node initiated ",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def Initiate_killing_of_Pod_because_of_node_outage(self,
        node_with_outage: "Node",
        pod_killed: "podkind.Pod",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == True
        assert pod_killed.status == STATUS_POD["Running"]
        assert pod_killed.atNode == node_with_outage
        assert node_with_outage.status == STATUS_NODE["Killing"]
        pod_killed.status = STATUS_POD["Killing"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing of pod initiated because of node outage",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def NodeOutageFinished(self,
        node: "Node",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == True
        assert node.amountOfActivePods == 0
        assert node.status == STATUS_NODE["Killing"]
        globalVar.amountOfNodesDisrupted += 1
        node.status = STATUS_NODE["Inactive"]
        globalVar.block_node_outage_in_progress = False
        globalVar.is_node_disrupted = True # TODO: checking ONE node outage! Need fixing
        # TODO make ability to calculate multiple nodes outage
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Node outage",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def ReplaceNullCpuRequestsWithZero(self,
        pod: "Pod"):
        # assert pod.status == STATUS_POD["Running"]
        assert pod.cpuRequest == -1
        pod.cpuRequest = 0
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="CPU request for Pod is not defined, further it is threated as Zero",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def ReplaceNullMemRequestsWithZero(self,
        pod: "Pod"):
        # assert pod.status == STATUS_POD["Running"]
        assert pod.memRequest == -1
        pod.memRequest = 0
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="MEM request for Pod is not defined, further it is threated as Zero",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=1)
    def manually_initiate_killing_of_pod(self,
        node_with_outage: "Node",
        pod_killed: "Pod",
        globalVar: GlobalVar
        ):
        assert pod_killed.status == STATUS_POD["Running"]
        pod_killed.status = STATUS_POD["Killing"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing of pod initiated because of node outage",
            parameters={},
            probability=1.0,
            affected=[]
        )