from poodle import planned
from logzero import logger
from guardctl.misc.const import *
from guardctl.model.kinds.Node import Node
import guardctl.model.kinds.Service as mservice
import guardctl.model.system.Scheduler as mscheduler
import guardctl.model.kinds.Node as mnode
from guardctl.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from guardctl.model.system.Controller import Controller
from guardctl.model.system.primitives import Label

from guardctl.model.system.base import HasLimitsRequests, HasLabel
from guardctl.model.system.globals import GlobalVar
from guardctl.misc.const import *
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from guardctl.model.scenario import ScenarioStep, describe
import sys


class Pod(HasLabel, HasLimitsRequests):
    # k8s attributes
    metadata_ownerReferences__name: str
    spec_priorityClassName: str
    metadata_name: str

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
    status: StatusPod
    isNull: bool
    # amountOfActiveRequests: int # For requests
    hasDeployment: bool
    hasService: bool
    hasDaemonset: bool


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = 0
        self.spec_priorityClassName = "KUBECTL-VAL-NONE"
        self.priorityClass = zeroPriorityClass
        # self.targetService = self.TARGET_SERVICE_NULL
        self.toNode = mnode.Node.NODE_NULL
        self.atNode = mnode.Node.NODE_NULL
        self.status = STATUS_POD["Pending"]
        self.isNull = True
        self.realInitialMemConsumption = 0
        self.realInitialCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentFormalCpuConsumption = 0
        # self.amountOfActiveRequests = 0 # For Requests


    def set_priority(self, object_space, controller):
        try:
            self.priorityClass = next(filter(lambda x: isinstance(x, PriorityClass) and \
                        str(x.metadata_name) == str(controller.spec_template_spec_priorityClassName), object_space))
        except StopIteration:
            logger.warning("Could not reference priority class")

    def hook_after_load(self, object_space, _ignore_orphan=False):
        nodes = list(filter(lambda x: isinstance(x, mnode.Node) and self.spec_nodeName == x.metadata_name, object_space))
        found = False
        for node in nodes:
            if str(node.metadata_name) == str(self.spec_nodeName):
                self.atNode = node
                if self.cpuRequest > 0:
                    node.currentFormalCpuConsumption += self.cpuRequest
                if self.memRequest > 0:
                    node.currentFormalMemConsumption += self.memRequest
                found = True
        if not found and self.toNode == Node.NODE_NULL and not _ignore_orphan:
            logger.warning("Orphan Pod loaded %s" % str(self.metadata_name))
        
        # link service <> pod
        services = filter(lambda x: isinstance(x, mservice.Service), object_space)
        for service in services:
            if len(service.spec_selector._get_value()) and \
                    set(service.spec_selector._get_value())\
                        .issubset(set(self.metadata_labels._get_value())):
                self.targetService = service
                if self.status == STATUS_POD["Running"]:
                    self.connect_pod_service_labels(self, service, \
                        list(service.metadata_labels._get_value())[0])

        if str(self.spec_priorityClassName) != "KUBECTL-VAL-NONE":
            try:
                self.priorityClass = next(filter(lambda x: isinstance(x, PriorityClass)\
                    and str(x.metadata_name) == str(self.spec_priorityClassName), \
                        object_space))
            except StopIteration:
                raise Exception("Could not find priorityClass %s, maybe you \
did not dump PriorityClass?" % str(self.spec_priorityClassName))

    @property
    def spec_containers__resources_requests_cpu(self):
        pass
    @spec_containers__resources_requests_cpu.setter
    def spec_containers__resources_requests_cpu(self, res):
        if self.cpuRequest == -1: self.cpuRequest = 0
        self.cpuRequest += cpuConvertToAbstractProblem(res)

    @property
    def spec_containers__resources_requests_memory(self):
        pass
    @spec_containers__resources_requests_memory.setter
    def spec_containers__resources_requests_memory(self, res):
        if self.memRequest == -1: self.memRequest = 0
        self.memRequest += memConvertToAbstractProblem(res)

    @property
    def status_phase(self):
        pass
    @status_phase.setter
    def status_phase(self, res):
        self.status = STATUS_POD[res]

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
        node1: "mnode.Node" ,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert node1 == pod1.atNode
            assert memCapacity == node1.memCapacity
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
        node1: "mnode.Node" ,
        cpuCapacity: int
        ):
            assert pod1.cpuLimit == -1
            assert node1 == pod1.atNode
            assert cpuCapacity == node1.cpuCapacity

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
        node1: "mnode.Node" ,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert memCapacity == node1.memCapacity
            pod1.toNode = node1
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
        node1: "mnode.Node" ,
        cpuCapacity: int):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
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
    def SetDefaultCpuLimitPerLimitRange(self,
        pod1: "Pod",
        node1: "mnode.Node" ,
        cpuCapacity: int,
        ):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
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
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                node1: "mnode.Node" , # unused
                scheduler1: "mscheduler.Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
        assert podPending in scheduler1.podQueue
        assert podPending.toNode == Node.NODE_NULL
        assert podPending.status == STATUS_POD["Pending"]
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass
        # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
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
    def Evict_and_replace_less_prioritized_pod_when_target_node_is_defined(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "mnode.Node" , # unused
                scheduler1: "mscheduler.Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass
                ):
        assert podPending in scheduler1.podQueue
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

    # We did this in Python function, so commented out as this code is incomplete
    # @planned
    def connect_pod_service_labels(self,
            pod: "Pod",
            service: "mservice.Service",
            label: Label):
        # TODO: full selector support
        # TODO: only if pod is running, service is started
        assert pod.targetService == pod.TARGET_SERVICE_NULL
        assert label in pod.metadata_labels
        assert label in service.spec_selector
        assert pod.status == STATUS_POD["Running"]
        pod.targetService = service
        service.amountOfActivePods += 1
        service.status = STATUS_SERV["Started"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="no description provided",
            parameters={},
            probability=1.0,
            affected=[describe(pod)]
        )

    # @planned
    # def fill_priority_class_object(self,
    #         pod: "Pod",
    #         pclass: PriorityClass):
    #     assert pod.spec_priorityClassName == pclass.metadata_name
    #     pod.priorityClass = pclass

    #     return ScenarioStep(
    #         name=sys._getframe().f_code.co_name,
    #         subsystem=self.__class__.__name__,
    #         description="no description provided",
    #         parameters={},
    #         probability=1.0,
    #         affected=[describe(pod)]
    #     )

    @planned(cost=100)
    def Mark_Pod_As_Exceeding_Mem_Limits(self, podTobeKilled: "Pod",nodeOfPod: "mnode.Node" ):
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
        nodeOfPod: "mnode.Node"
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
    nodeOfPod: "mnode.Node" ,
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
        nodeOfPod: "mnode.Node" ,
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
    def KillPod(self,
            podBeingKilled : "Pod",
            nodeWithPod : "mnode.Node" ,
            serviceOfPod: "mservice.Service",
            # globalVar1: "GlobalVar",
            scheduler1: "mscheduler.Scheduler",
            amountOfActivePodsPrev: int

         ):
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.targetService == serviceOfPod
        assert podBeingKilled.status ==  STATUS_POD["Killing"]
        # assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentRealMemConsumption -= podBeingKilled.realInitialMemConsumption
        nodeWithPod.currentRealCpuConsumption -= podBeingKilled.realInitialCpuConsumption
        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -=  podBeingKilled.cpuRequest
        # globalVar1.currentFormalMemConsumption -= podBeingKilled.memRequest
        # globalVar1.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        podBeingKilled.status =  STATUS_POD["Pending"]
        scheduler1.podQueue.add(podBeingKilled)
        scheduler1.status = STATUS_SCHED["Changed"]

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Killing pod",
            parameters={"podBeingKilled": describe(podBeingKilled)},
            probability=1.0,
            affected=[describe(podBeingKilled)]
        )

    # Scheduler effects



Pod.POD_NULL = Pod("NULL")
Pod.POD_NULL.isNull = True

