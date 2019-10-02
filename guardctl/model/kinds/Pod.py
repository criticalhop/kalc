from poodle import planned
from logzero import logger
from guardctl.misc.const import *
from guardctl.model.kinds.Node import Node
import guardctl.model.kinds.Service as mlservice
import guardctl.model.system.Scheduler as mscheduler
import guardctl.model.kinds.Deployment as mdeployment
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
    TARGET_SERVICE_NULL = mlservice.Service.SERVICE_NULL
    targetService: mlservice.Service
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

    def hook_after_load(self, object_space, _ignore_orphan=False):
        pass

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

    def __str__(self): return str(self.metadata_name)

    
 

    @planned(cost=100)
    def KillPod_IF_service_notnull_deployment_notnull(self,
            podBeingKilled : "Pod",
            nodeWithPod : mnode.Node ,
            # serviceOfPod: mlservice.Service,

            amountOfActivePodsPrev: int,
            deployment_of_pod: mdeployment.Deployment
         ):
        assert podBeingKilled in deployment_of_pod.podList
        deployment_of_pod.amountOfActivePods -= 1






