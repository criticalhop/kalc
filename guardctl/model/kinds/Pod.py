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
        self.targetService = mservice.Service.SERVICE_NULL
        self.toNode = mnode.Node.NODE_NULL
        self.atNode = mnode.Node.NODE_NULL

        self.status = STATUS_POD["Pending"]
        self.isNull = False
        self.realInitialMemConsumption = 0
        self.realInitialCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentFormalCpuConsumption = 0
        # self.amountOfActiveRequests = 0 # For Requests


    def set_priority(self, object_space, controller):
        if str(controller.spec_template_spec_priorityClassName) != "Normal-zero":
            try:
                self.priorityClass = next(filter(lambda x: isinstance(x, PriorityClass) and \
                            str(x.metadata_name) == str(controller.spec_template_spec_priorityClassName), object_space))
            except StopIteration:
                logger.warning("Could not reference priority class %s %s" % (str(controller.spec_template_spec_priorityClassName), str(self.metadata_name)))

    def hook_after_load(self, object_space, _ignore_orphan=False):
        nodes = list(filter(lambda x: isinstance(x, mnode.Node) and self.spec_nodeName == x.metadata_name, object_space))
        found = False
        for node in nodes:
            if str(node.metadata_name) == str(self.spec_nodeName):
                self.atNode = node
                node.amountOfActivePods += 1
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
did not dump PriorityClass?" % str(self.spec_priorityClassName._get_value()))

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

    def __str__(self): return str(self.metadata_name)


Pod.POD_NULL = Pod("NULL")
Pod.POD_NULL.isNull = True

