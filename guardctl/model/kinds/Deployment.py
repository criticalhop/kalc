from guardctl.model.system.Controller import Controller
from guardctl.model.system.base import HasLimitsRequests
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.ReplicaSet import ReplicaSet
from guardctl.model.system.primitives import Status
from guardctl.misc.const import STATUS_POD, STATUS_SCHED
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
    status: Status
    podList: Set["mpod.Pod"]
    spec_template_spec_priorityClassName: str
    hash: str

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        #TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
        self.hash = "superhash"


    def hook_after_create(self, object_space):
        
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), object_space))
        deployments = filter(lambda x: isinstance(x, Deployment), object_space)
        for deploymentController in deployments:
            if str(deploymentController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): deployments.{0} \"{1}\" already exists".format(str(self.apiVersion).split("/")[0], self.metadata_name)
                logger.error(message)
                raise AssertionError(message)
        self.create_pods(self.spec_replicas._get_value())

    def create_pods(self, replicas):
        for replicaNum in range(replicas):
            new_pod = mpod.Pod()
            hash1 = self.hash
            hash2 = str(replicaNum)
            new_pod.metadata_name = "{0}-Deployment-{1}-{2}".format(str(self.metadata_name),hash1,hash2)
            new_pod.metadata_labels = self.metadata_labels
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
            self.check_pod(new_pod, object_space)
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
            br=False
            if replicaset.metadata_ownerReferences__name == self.metadata_name:
                for pod_template_hash in list(replicaset.metadata_labels._get_value()):
                    if str(pod_template_hash).split(":")[0] == "pod-template-hash":
                        self.hash = str(pod_template_hash).split(":")[1]
                        br = True
                        break
            if br: break

        for pod in pods:
            br = False
            # look for right pod-template-hash
            for pod_template_hash in list(pod.metadata_labels._get_value()):
                if str(pod_template_hash).split(":")[0] == "pod-template-hash" and str(pod_template_hash).split(":")[1] == self.hash :
                    self.podList.add(pod)
                    self.check_pod(pod, object_space)

    def hook_scale_before_create(self, object_space, new_replicas):
        self.spec_replicas = new_replicas

    #Call me only atfter loading this Controller
    def hook_scale_after_load(self, object_space, new_replicas):
        diff_replicas = new_replicas - self.spec_replicas
        if diff_replicas == 0:
            logger.warning("Nothing to scale. You try to scale deployment {0} for the same replicas value {1}".format(self.metadata_name, self.spec_replicas))
        if diff_replicas < 0:
            #remove pods
            for counter in range(diff_replicas):
                pod = self.podList.pop(-1)
                object_space.remove(pod)
        if diff_replicas > 0:
            create_pods(diff_replicas)

    def check_pod(self, new_pod, object_space):
        for pod in filter(lambda x: isinstance(x, mpod.Pod), object_space):
            pod1 = [x for x in list(pod.metadata_labels._get_value()) if str(x).split(":")[0] != "pod-template-hash"]
            pod2 = [x for x in list(new_pod.metadata_labels._get_value()) if str(x).split(":")[0] != "pod-template-hash"]
            if set(pod1) == set(pod2):
                logger.warning("Pods have the same label")