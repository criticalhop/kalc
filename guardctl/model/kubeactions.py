import sys
from poodle import planned
from logzero import logger
from guardctl.model.system.base import HasLimitsRequests, HasLabel
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.system.primitives import TypeServ
from guardctl.model.system.Controller import Controller
from guardctl.model.system.primitives import Label
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.DaemonSet import DaemonSet
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from guardctl.model.scenario import ScenarioStep, describe
from guardctl.misc.const import *
from guardctl.misc.problem import ProblemTemplate
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem

class KubernetesModel(ProblemTemplate):
    def problem(self):
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        self.globalVar = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

    @planned(cost=100)
    def Mark_service_as_started(self,
                service1: Service,
                scheduler: "Scheduler"
            ):
        assert service1.amountOfActivePods > 0
        assert service1.isNull == False
        service1.status = STATUS_SERV["Started"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Mark service as started",
            parameters={},
            probability=1.0,
            affected=[describe(service1)]
        )
    @planned(cost=100)
    def Fill_priority_class_object(self,
            pod: "Pod",
            pclass: PriorityClass):
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
    @planned(cost=100)
    def SetDefaultMemRequestForPod(self,
        pod1: "Pod",
        memLimit: int
        ):
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

    @planned(cost=100)
    def SetDefaultCpuRequestForPod(self,
        pod1: "Pod",
        cpuLimit: int
        ):
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

    @planned(cost=100)
    def SetDefaultMemLimitForPod(self,
        pod1: "Pod",
        node: "Node" ,
        memCapacity: int
        ):
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

    @planned(cost=100)
    def SetDefaultCpuLimitForPod(self,
        pod1: "Pod",
        node: "Node" ,
        cpuCapacity: int
        ):
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

    @planned(cost=100)
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node: "Node" ,
        memCapacity: int
        ):
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

    @planned(cost=100)
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node: "Node" ,
        cpuCapacity: int):
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


    @planned(cost=100)
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_defined_byMEM(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "Node" ,
                scheduler: "Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
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
        assert podPending.memRequest > nodeForPodPending.memCapacity - nodeForPodPending.currentFormalCpuConsumption
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

    @planned(cost=100)
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_defined_byCPU(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "Node" ,
                scheduler: "Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
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
        assert podPending.cpuRequest > nodeForPodPending.cpuCapacity - nodeForPodPending.currentFormalMemConsumption
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
        
    @planned(cost=100)
    def Mark_Pod_As_Exceeding_Mem_Limits(self, podTobeKilled: "Pod",nodeOfPod: "Node" ):
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

    @planned(cost=100)
    def Mark_Pod_As_Not_Exceeding_Mem_Limits(self, podTobeReanimated: "Pod",
        nodeOfPod: "Node"
        #, globalVar1: GlobalVar
        ):
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

    @planned(cost=100)
    def MemoryErrorKillPodExceedingLimits(self,
        nodeOfPod: "Node" ,
        pod1TobeKilled: "Pod"
        ):
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

    @planned(cost=100)
    def MemoryErrorKillPodNotExceedingLimits(self,
        nodeOfPod: "Node" ,
        podTobeKilled: "Pod"):
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

    @planned(cost=100)
    def KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            serviceOfPod: "Service",
            scheduler: "Scheduler"
         ):
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
        nodeWithPod.amountOfActivePods -= 1 
        podBeingKilled.status = STATUS_POD["Pending"]
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

    @planned(cost=100)
    def KillPod_IF_Deployment_isNotNUll_Service_isNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            pods_deployment: Deployment,
            nodeWithPod : "Node" ,
            scheduler: "Scheduler"
         ):
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
        # scheduler.debug_var = True # TODO DELETEME
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=100)
    def KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            scheduler: "Scheduler"
         ):
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
        # scheduler.debug_var = True # TODO DELETEME
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=100)
    def KillPod_IF_Deployment_isNotNUll_Service_isNotNull_Daemonset_isNull(self,
            podBeingKilled : "Pod",
            serviceOfPod: "Service",
            pods_deployment: Deployment,
            nodeWithPod : "Node" ,
            scheduler: "Scheduler"
         ):
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
        podBeingKilled.status = STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"]
        scheduler.queueLength += 1
        # scheduler.debug_var = True # TODO DELETEME
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=100)
    def KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNotNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            serviceOfPod: "Service",
            pods_daemonset: DaemonSet,
            scheduler: "Scheduler"

         ):
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled in serviceOfPod.podList
        assert podBeingKilled.status ==  STATUS_POD["Killing"]
        assert podBeingKilled in pods_daemonset.podList
        # assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        assert podBeingKilled.hasService == True 
        assert podBeingKilled.hasDeployment == False #TODO add this for branching
        assert podBeingKilled.hasDaemonset == True #TODO add this for branching

        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        nodeWithPod.amountOfActivePods -= 1 
        pods_daemonset.amountOfActivePods -= 1
        podBeingKilled.status =  STATUS_POD["Pending"]
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

    @planned(cost=100)
    def KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull(self,
            podBeingKilled : "Pod",
            nodeWithPod : "Node" ,
            pods_daemonset: DaemonSet,
            scheduler: "Scheduler"
         ):
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.status ==  STATUS_POD["Killing"]
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
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    @planned(cost=100)
    def SelectNode(self, 
        pod1: "Pod",
        SelectedNode: "Node" ):
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

    @planned(cost=100)
    def StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service"
        ):
        assert podStarted.hasService == True 
        assert podStarted.hasDeployment == False #TODO add this for branching
        assert podStarted.hasDaemonset == False #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in serviceTargetForPod.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity + 0
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity + 0
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
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
    
    @planned(cost=100)
    def StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler"
        ):
        assert podStarted.hasService == False 
        assert podStarted.hasDeployment == False #TODO add this for branching
        assert podStarted.hasDaemonset == False #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity + 0
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity + 0
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

    @planned(cost=100)
    def StartPod_IF_Deployment_isNotNUll_Service_isNotNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        pods_deployment: Deployment
        ):
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
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity + 0
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity + 0
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        serviceTargetForPod.amountOfActivePods += 1
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
    
    @planned(cost=100)
    def StartPod_IF_Deployment_isNotNUll_Service_isNull_Daemonset_isNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        pods_deployment: Deployment
        ):
        assert podStarted.hasService == False 
        assert podStarted.hasDeployment == True #TODO add this for branching
        assert podStarted.hasDaemonset == False #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in pods_deployment.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity + 0
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity + 0
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

    @planned(cost=100)
    def StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        pods_daemonset: DaemonSet
        ):
        assert podStarted.hasService == False 
        assert podStarted.hasDeployment == False #TODO add this for branching
        assert podStarted.hasDaemonset == True #TODO add this for branching

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in pods_daemonset.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity + 0 
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity + 0
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


    @planned(cost=100)
    def StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNotNull(self, 
        podStarted: "Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        pods_daemonset: DaemonSet
        ):
        assert podStarted.hasService == True
        assert podStarted.hasDeployment == False
        assert podStarted.hasDaemonset == True

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert node.isNull == False
        assert podStarted in pods_daemonset.podList
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity + 0 
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity + 0
        assert node.status == STATUS_NODE["Active"]

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        pods_daemonset.amountOfActivePods += 1
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
    @planned(cost=10000)
    def Scheduler_cant_place_pod(self, scheduler: "Scheduler"):
        scheduler.queueLength -= 1
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Can't place a pod",
            parameters={},
            probability=1.0,
            affected=[]
        )

        #todo: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
    
    @planned(cost=100)
    def ScheduleQueueProcessed(self, scheduler: "Scheduler"):
        assert  scheduler.queueLength == 0
        scheduler.status = STATUS_SCHED["Clean"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Finished processing pod queue",
            parameters={},
            probability=1.0,
            affected=[]
        )

    @planned(cost=100000)
    def Initiate_node_outage(self,
        node_with_outage: "Node",
        globalVar: GlobalVar
        ):
        assert globalVar.amountOfNodesDisrupted < globalVar.limitOfAmountOfNodesDisrupted
        assert node_with_outage.searchable == True
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
        
    @planned(cost=100)
    def Initiate_killing_of_Pod_because_of_node_outage(self,
        node_with_outage: "Node",
        pod_killed: "podkind.Pod",
        globalVar: GlobalVar
        ):
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

    @planned(cost=100)
    def NodeOutageFinished(self,
        node: "Node",
        globalVar: GlobalVar
        ):
        assert node.amountOfActivePods == 0
        assert node.status == STATUS_NODE["Killing"]
        globalVar.amountOfNodesDisrupted += 1
        node.status = STATUS_NODE["Inactive"]
        globalVar.block_node_outage_in_progress = False
        # TODO make ability to calculate multiple nodes outage
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Node outage",
            parameters={},
            probability=1.0,
            affected=[]
        )
    @planned(cost=100)
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
    @planned(cost=100)
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
class Random_events(ProblemTemplate):
    pass