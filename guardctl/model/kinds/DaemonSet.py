from guardctl.model.system.Controller import Controller
from guardctl.model.system.base import HasLimitsRequests
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
import guardctl.model.kinds.Pod as mpod
from guardctl.model.system.primitives import Status
from guardctl.misc.const import *
from poodle import *
from typing import Set
from logzero import logger
import guardctl.misc.util as util

#TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
class DaemonSet(Controller, HasLimitsRequests):
    metadata_name: str
    lastPod: "mpod.Pod"
    amountOfActivePods: int
    status: Status
    podList: Set["mpod.Pod"]
    spec_template_spec_priorityClassName: str


    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

    def hook_after_create(self, object_space):
        # TODO throw error if name already exist
        # Error from server (AlreadyExists): error when creating "./tests/daemonset_eviction/daemonset_create.yaml": daemonsets.apps "fluentd-elasticsearch" already exists
        nodes = filter(lambda x: isinstance(x, Node), object_space)
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), object_space))
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
            new_pod.hook_after_load(object_space, _ignore_orphan=True) # for service<>pod link
            new_pod.set_priority(object_space, self)
            self.podList.add(new_pod)
            object_space.append(new_pod)
            scheduler.podQueue.add(new_pod)
            scheduler.queueLength += 1
            scheduler.status = STATUS_SCHED["Changed"]

    def hook_after_load(self, object_space):
        daemonSets = filter(lambda x: isinstance(x, DaemonSet), object_space)
        for daemonSetController in daemonSets:
            if daemonSetController != self and str(daemonSetController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): daemonSetController.{0} \"{1}\" already exists".format(str(self.apiVersion).split("/")[0], self.metadata_name)
                logger.error(message)
                raise AssertionError(message)
        pods = filter(lambda x: isinstance(x, mpod.Pod), object_space)
        
        for pod in pods:
            if pod.metadata_ownerReferences__name == self.metadata_name:
                self.podList.add(pod)
                nodes = filter(lambda x: isinstance(x, Node), object_space)
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


