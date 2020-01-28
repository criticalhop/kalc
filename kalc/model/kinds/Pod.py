from poodle import planned
from kalc.misc.const import *
import kalc.model.kinds.Service as mservice
from kalc.model.system.base import ModularKind
import kalc.model.system.Scheduler as mscheduler
import kalc.model.kinds.Node as mnode
from kalc.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from kalc.model.system.Controller import Controller
from kalc.model.system.primitives import Label

from kalc.model.system.base import HasLimitsRequests, HasLabel
from kalc.misc.const import *
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem, getint, POODLE_MAXLIN
# import kalc.cli as cli
import sys
import random
from logzero import logger
from typing import Set


class Pod(ModularKind, HasLabel, HasLimitsRequests):
    # k8s attributes
    metadata_ownerReferences__name: str
    spec_priorityClassName: str
    spec_nodeSelector: Set[Label]
    metadata_name: str

    metadata_namespace: str
    # internal model attributes
    ownerReferences: Controller
    # TARGET_SERVICE_NULL = mservice.Service.SERVICE_NULL
    # targetService: "mservice.Service"
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
    not_on_same_node: Set["Pod"]
    searchable: bool
    

    nodesSelectorSet: bool
    nodeSelectorList: Set["mnode.Node"]
    affinity_set: bool
    antiaffinity_set: bool
    antiaffinity_preferred_set: bool
    
    affinity_met: bool   
    antiaffinity_met: bool
    antiaffinity_preferred_met: bool

    podsMatchedByAffinity: Set["Pod"]
    podsMatchedByAffinity_length: int
    podsMatchedByAntiaffinity: Set["Pod"]
    podsMatchedByAntiaffinity_length: int
    nodesThatCantAllocateThisPod: Set["Node"]
    nodesThatCantAllocateThisPod_length: int
    nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod: Set["Node"]
    calc_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod: Set["Node"]
    nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length: int
    podsMatchedByAntiaffinityPrefered: Set["Pod"]
    podsMatchedByAntiaffinityPrefered_length: int
    calc_affinity_pods_list: Set["Pod"]
    calc_affinity_pods_list_length: int
    calc_antiaffinity_pods_list: Set["Pod"]
    calc_antiaffinity_pods_list_length: int
    calc_cantmatch_antiaffinity: bool
    calc_cantmatch_affinity: bool

    calc_antiaffinity_preferred_pods_list: Set["Pod"]
    calc_antiaffinity_preferred_pods_list_length: int
    antiaffinity_pods_list: Set["Pod"]
    antiaffinity_preferred_pods_list: Set["Pod"]
    
    target_number_of_antiaffinity_pods: int
    target_number_of_antiaffinity_preferred_pods: int

    antiaffinity_labels: Set["Label"]
    antiaffinity_labels_length: int
    antiaffinity_preferred_labels: Set["Label"]
    antiaffinity_preferred_labels_length: int
    affinity_labels: Set["Label"]
    affinity_labels_length: int
    is_checked_as_source_for_labels: bool
    is_checked_as_target_for_labels: bool
    nodes_acceptable_by_antiaffinity: Set["Node"]
    nodes_acceptable_by_antiaffinity_length: int
    calc_checked_pods_from_point_of_this_pod: Set["Pod"]
    calc_checked_pods_from_point_of_this_pod_length: int
    calc_checked_pods_from_point_of_that_pod: Set["Pod"]
    calc_checked_pods_from_point_of_that_pod_length: int
    toNode_is_checked: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = 0
        self.spec_priorityClassName = "KUBECTL-VAL-NONE"
        self.priorityClass = zeroPriorityClass
        # self.targetService = mservice.Service.SERVICE_NULL
        self.toNode = mnode.Node.NODE_NULL
        self.atNode = mnode.Node.NODE_NULL
        self.cpuRequest = -1
        self.memRequest = -1
        self.status = STATUS_POD["Pending"]
        self.isNull = False
        self.searchable = False
        self.realInitialMemConsumption = 0
        self.realInitialCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentFormalCpuConsumption = 0
        # self.amountOfActiveRequests = 0 # For Requests
        self.hasService = False
        self.hasDaemonset = False
        self.hasDeployment = False
        self.metadata_name = "modelPod"+str(random.randint(100000000, 999999999))
        # self.metadata_name = "model-default-name"
        self.nodeSelectorSet = False
        self.antiaffinity_set = False
        self.calc_antiaffinity_pods_list_length = 0
        self.calc_antiaffinity_preferred_pods_list_length = 0
        self.target_number_of_antiaffinity_pods = 0
        self.antiaffinity_met = False
        self.podsToBeMatchedByAntiaffinity_length = 0
        self.podsToBeMatchedByAntiaffinity_Preferred_length = 0
        self.podsMatchedByAffinity_length = 0
        self.podsMatchedByAntiaffinity_length = 0
        self.podsMatchedByAntiaffinityPrefered_length = 0
        self.is_checked_as_source_for_labels = False
        self.is_checked_as_target_for_labels = False
        self.nodesThatCantAllocateThisPod_length = 0 
        self.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length = 0
        self.calc_cantmatch_antiaffinity = False
        self.calc_cantmatch_affinity = False
        self.nodes_acceptable_by_antiaffinity_length = 0
        self.calc_checked_pods_from_point_of_this_pod_length = 0
        self.calc_checked_pods_from_point_of_that_pod_length = 0
        self.spec_nodeName = ''
        self.toNode_is_checked = False



    def set_priority(self, object_space, controller):
        if str(controller.spec_template_spec_priorityClassName) != "Normal-zero":
            try:
                self.priorityClass = next(filter(lambda x: isinstance(x, PriorityClass) and \
                            str(x.metadata_name) == str(controller.spec_template_spec_priorityClassName), object_space))
            except StopIteration:
                logger.warning("Could not reference priority class %s %s" % (str(controller.spec_template_spec_priorityClassName), str(self.metadata_name)))

    def hook_after_load(self, object_space, _ignore_orphan=False):
        pods = list(filter(lambda x: isinstance(x, Pod), object_space))
        nodes = list(filter(lambda x: isinstance(x, mnode.Node) and self.spec_nodeName == x.metadata_name, object_space))
        found = False
        for node in nodes:
            if str(node.metadata_name) == str(self.spec_nodeName):
                self.atNode = node
                node.allocatedPodList.add(self)
                node.allocatedPodList_length += 1
                node.directedPodList.add(self)
                node.directedPodList_length += 1
                node.amountOfActivePods += 1
                assert getint(node.amountOfActivePods) < POODLE_MAXLIN, "Pods amount exceeded max %s > %s" % (getint(node.amountOfActivePods), POODLE_MAXLIN) 
                if self.cpuRequest > 0:
                    node.currentFormalCpuConsumption += self.cpuRequest
                    assert getint(node.currentFormalCpuConsumption) < POODLE_MAXLIN, "CPU request exceeded max: %s" % getint(node.currentFormalCpuConsumption)
                if self.memRequest > 0:
                    node.currentFormalMemConsumption += self.memRequest
                    assert getint(node.currentFormalMemConsumption) < POODLE_MAXLIN, "MEM request exceeded max: %s" % getint(node.currentFormalMemConsumption)
                found = True
            if not self.nodeSelectorSet: self.nodeSelectorList.add(node)
        if not found and self.toNode == mnode.Node.NODE_NULL and not _ignore_orphan:
            logger.warning("Orphan Pod loaded %s" % str(self.metadata_name))
        
        # link service <> pod
        
        services = filter(lambda x: isinstance(x, mservice.Service), object_space)
        for service in services:
            if len(service.spec_selector._get_value()) and \
                    set(service.spec_selector._get_value())\
                        .issubset(set(self.metadata_labels._get_value())):
                # print("ASSOCIATE SERVICE", str(self.metadata_name), str(service.metadata_name))
                service.podList.add(self)
                self.hasService = True
                if list(service.metadata_labels._get_value()):
                    if self.status._property_value == STATUS_POD["Running"]:
                        service.amountOfActivePods += 1
                        service.status = STATUS_SERV["Started"]
                        assert getint(service.amountOfActivePods) < POODLE_MAXLIN, "Service pods overflow"
                else:
                    pass
                    # cli.click.echo("    - WRN: no label for service %s" % str(service.metadata_name))
        if self.status._property_value == STATUS_POD["Pending"]:
            scheduler = next(filter(lambda x: isinstance(x, mscheduler.Scheduler), object_space))
            scheduler.queueLength += 1
            assert getint(scheduler.queueLength) < POODLE_MAXLIN, "Queue length overflow {0} < {1}".format(getint(scheduler.queueLength), POODLE_MAXLIN)
            scheduler.podQueue.add(self)
            scheduler.status = STATUS_SCHED["Changed"]

        nodes = list(filter(lambda x: isinstance(x, mnode.Node), object_space))
        for node in nodes:
            if list(node.metadata_labels) and \
                    set(self.spec_nodeSelector)\
                        .issubset(set(node.metadata_labels)):
                        self.nodeSelectorList.add(node)
                        self.nodeSelectorSet = True

        if str(self.spec_priorityClassName) != "KUBECTL-VAL-NONE":
            try:
                self.priorityClass = next(filter(lambda x: isinstance(x, PriorityClass)\
                    and str(x.metadata_name) == str(self.spec_priorityClassName), \
                        object_space))
            except StopIteration:
                raise Exception("Could not find priorityClass %s, maybe you \
                        did not dump PriorityClass?" % str(self.spec_priorityClassName))
    def hook_after_create(self, object_space):
        nodes = list(filter(lambda x: isinstance(x, mnode.Node), object_space))
        for node in nodes:
            if list(node.metadata_labels) and \
                    set(self.spec_nodeSelector)\
                        .issubset(set(node.metadata_labels)):
                        self.nodeSelectorList.add(node)
                        self.nodeSelectorSet = True
        for node in nodes:
            if not self.nodeSelectorSet: self.nodeSelectorList.add(node)
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
    def connect_pod_service_labels(self,
            pod: "Pod",
            service: "mservice.Service",
            label: Label):
        # TODO: full selector support
        # TODO: only if pod is running, service is started
        assert label in pod.metadata_labels
        assert label in service.spec_selector
        assert pod.status == STATUS_POD["Running"]
        # service.podList.add(pod)
        service.amountOfActivePods += 1
        service.status = STATUS_SERV["Started"]


    def __str__(self): return str(self.metadata_name)

