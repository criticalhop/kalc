import random
from guardctl.model.system.Controller import Controller
from guardctl.model.system.base import HasLimitsRequests
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
import guardctl.model.kinds.Pod as mpod
from guardctl.model.system.primitives import Status
from guardctl.misc.const import STATUS_POD, STATUS_SCHED
from poodle import *
from typing import Set
from logzero import logger

class ReplicaSet(Controller, HasLimitsRequests):
    metadata_name: str
    metadata_namespace: str
    apiVersion: str
    metadata_ownerReferences__kind: str
    metadata_ownerReferences__name: str
    spec_replicas: int
   
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        #TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
        # self.metadata_name = "modelReplicaSet"+str(random.randint(100000000, 999999999))
        self.metadata_name = "model-default-name"
        self.hash = "superhash"
        self.spec_replicas = 0
        self.metadata_ownerReferences__kind = "NONE"
        self.metadata_ownerReferences__name = "NONE"


    def hook_after_create(self, object_space):
        pass

    def hook_after_load(self, object_space):
        pass