from guardctl.model.system.Controller import Controller
from guardctl.model.system.base import HasLimitsRequests
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.ReplicaSet import ReplicaSet
from guardctl.model.system.primitives import Status, StatusDepl
from guardctl.misc.const import STATUS_POD, STATUS_SCHED, STATUS_DEPL
from poodle import *
from typing import Set
from logzero import logger

class Deployment(Controller, HasLimitsRequests):
    spec_replicas: int
    metadata_name: str
    metadata_namespace: str
    apiVersion: str
    lastPod: "mpod.Pod"
    amountOfActivePods: int
    status: StatusDepl
    podList: Set["mpod.Pod"]
    spec_template_spec_priorityClassName: str
    hash: str
    searchable: bool

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        #TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
        self.hash = "superhash"
        self.status = STATUS_DEPL["Interrupted"]


    def hook_after_create(self, object_space):
        
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), object_space))
        deployments = filter(lambda x: isinstance(x, Deployment), object_space)
        for deploymentController in deployments:
            if str(deploymentController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): deployments.{0} \"{1}\" already exists".format(str(self.apiVersion).split("/")[0], self.metadata_name)
                logger.error(message)
                raise AssertionError(message)

        for replicaNum in range(self.spec_replicas._get_value()):
            new_pod = mpod.Pod()
            hash1 = self.hash
            hash2 = str(replicaNum)
            new_pod.metadata_name = "{0}-Deployment-{1}-{2}".format(str(self.metadata_name),hash1,hash2)
            new_pod.cpuRequest = self.cpuRequest
            new_pod.memRequest = self.memRequest
            new_pod.cpuLimit = self.cpuLimit
            new_pod.memLimit = self.memLimit
            new_pod.status = STATUS_POD["Pending"]
            new_pod.hook_after_load(object_space, _ignore_orphan=True) # for service<>pod link
            try:
                new_pod.priorityClass = \
                    next(filter(\
                        lambda x: \
                            isinstance(x, PriorityClass) and \
                            str(x.metadata_name) == str(self.spec_template_spec_priorityClassName),\
                        object_space))
            except StopIteration:
                logger.warning("Could not reference priority class")
            self.podList.add(new_pod)
            object_space.append(new_pod)
            scheduler.podQueue.add(new_pod)
            scheduler.queueLength += 1
            scheduler.status = STATUS_SCHED["Changed"]

    def hook_after_load(self, object_space):
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), object_space))
        deployments = filter(lambda x: isinstance(x, Deployment), object_space)
        for deploymentController in deployments:
            if str(deploymentController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): deployments.{0} \"{1}\" already exists".format(str(self.apiVersion).split("/")[0], self.metadata_name)
                logger.error(message)
                raise AssertionError(message)
        pods = filter(lambda x: isinstance(x, mpod.Pod), object_space)
        replicasets = filter(lambda x: isinstance(x, ReplicaSet), object_space)
        #look for ReplicaSet with corresonding owner reference
        for replicaset in replicasets:
            # print("replicaset {0} deployment {1}".format(replicaset.metadata_ownerReferences__name, self.metadata_name) )
            br=False
            if replicaset.metadata_ownerReferences__name == self.metadata_name:
                for pod_template_hash in list(replicaset.metadata_labels._get_value()):
                    if str(pod_template_hash).split(":")[0] == "pod-template-hash":
                        # print("hash {0}".format(pod_template_hash))
                        self.hash = str(pod_template_hash).split(":")[1]
                        # print("hash is {0}".format(self.hash))
                        br = True
                        break
            if br: break

        for pod in pods:
            br = False
            # look for right pod-template-hash
            for pod_template_hash in list(pod.metadata_labels._get_value()):
                if str(pod_template_hash).split(":")[0] == "pod-template-hash" and str(pod_template_hash).split(":")[1] == self.hash :
                    try:
                        pod.priorityClass = \
                            next(filter(\
                                lambda x: \
                                    isinstance(x, PriorityClass) and \
                                    str(x.metadata_name) == str(self.spec_template_spec_priorityClassName),\
                                object_space))
                    except StopIteration:
                        logger.warning("Could not reference priority class")
                    self.podList.add(pod)
                    scheduler.podQueue.add(pod)
                    scheduler.queueLength += 1
                    scheduler.status = STATUS_SCHED["Changed"]

    def check_pod(self, new_pod, object_space):
        for pod in filter(lambda x: isinstance(x, mpod.Pod), object_space):
            pod1 = [x for x in list(pod.metadata_labels._get_value()) if str(x).split(":")[0] != "pod-template-hash"]
            pod2 = [x for x in list(new_pod.metadata_labels._get_value()) if str(x).split(":")[0] != "pod-template-hash"]
            if set(pod1) == set(pod2):
                logger.warning("Pods have the same label")