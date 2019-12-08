import random
from kalc.model.system.Controller import Controller
from kalc.model.system.base import HasLimitsRequests
from kalc.model.kinds.Node import Node
from kalc.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from kalc.model.system.Scheduler import Scheduler
import kalc.model.kinds.Pod as mpod
from kalc.model.system.primitives import StatusDaemonSet
from kalc.misc.const import *
from poodle import *
from typing import Set
from logzero import logger
import kalc.misc.util as util

#TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
class DaemonSet(Controller, HasLimitsRequests):
    metadata_name: str
    metadata_uid: str
    amountOfActivePods: int
    status: StatusDaemonSet
    podList: Set["mpod.Pod"]
    spec_template_spec_priorityClassName: str

    searchable: bool


    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.metadata_name = "modelDaemonSet"+str(random.randint(100000000, 999999999))
        # self.metadata_name = "model-default-name"
        self.amountOfActivePods = 0
        self.searchable = True
        self.spec_template_spec_priorityClassName = "Normal-zero"
        self.priorityClass = zeroPriorityClass
        self.status = STATUS_DAEMONSET_PENDING
        self.metadata_uid = "undefined"
        #TODO make support for DAEMONSET start status while loading

    def hook_after_create(self, object_space):
        # TODO throw error if name already exist
        # Error from server (AlreadyExists): error when creating "./tests/daemonset_eviction/daemonset_create.yaml": daemonsets.apps "fluentd-elasticsearch" already exists
        nodes = filter(lambda x: isinstance(x, Node), object_space)
        i = 0
        for node in nodes:
            i += 1
            new_pod = mpod.Pod()
            new_pod.metadata_name = str(self.metadata_name) + '-DaemonSet_CR-' + str(i)
            new_pod.toNode = node
            new_pod.cpuRequest = self.cpuRequest
            new_pod.memRequest = self.memRequest
            new_pod.cpuLimit = self.cpuLimit
            new_pod.memLimit = self.memLimit
            new_pod.status = STATUS_POD["Pending"]
            new_pod.hook_after_load(object_space, _ignore_orphan=True) # for service<>pod link, add to sched
            new_pod.set_priority(object_space, self)
            new_pod.hasDaemonset = True
            self.podList.add(new_pod)
            object_space.append(new_pod)
            self.amountOfActivePods += 1

    def hook_after_load(self, object_space):
        daemonSets = filter(lambda x: isinstance(x, DaemonSet), object_space)
        for daemonSetController in daemonSets:
            if daemonSetController != self and str(daemonSetController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): DaemonSet with name {0}".format(self.metadata_name)
                logger.error(message)
                raise AssertionError(message)
        pods = filter(lambda x: isinstance(x, mpod.Pod), object_space)
        nodes = filter(lambda x: isinstance(x, Node), object_space)

        for pod in pods:
            if str(pod.metadata_ownerReferences__name) == str(self.metadata_name):
                self.podList.add(pod)
                self.amountOfActivePods += 1
                pod.hasDaemonset = True
                for node in nodes:
                    if node.metadata_name._get_value() == pod.spec_nodeName._get_value():
                        pod.toNode = node
                # self.check_pod(pod, object_space)

    def hook_after_apply(self, object_space):
        daemonSets = filter(lambda x: isinstance(x, DaemonSet), object_space)
        old_daemonSet = self
        for daemonSetController in daemonSets:
            if daemonSetController != self and str(daemonSetController.metadata_name) == str(self.metadata_name):
                old_daemonSet = daemonSetController
                break
        # if old DEployment not found
        if old_daemonSet == self:
            self.hook_after_create(object_space)
        else:
            self.podList = old_daemonSet.podList # copy pods instead of creating
            #scale memory and cpu
            for pod in util.objDeduplicatorByName(self.podList._get_value()):
                pod.cpuRequest = self.cpuRequest
                pod.memRequest = self.memRequest
                pod.cpuLimit = self.cpuLimit
                pod.memLimit = self.memLimit
                pod.set_priority(object_space, self)
            object_space.remove(old_daemonSet) # delete old Deployment


