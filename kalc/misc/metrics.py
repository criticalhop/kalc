from kalc.model.system.base import ModularKind
from kalc.model.system.Controller import Controller
from kalc.model.system.base import HasLimitsRequests
from kalc.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from kalc.model.system.Scheduler import Scheduler
import kalc.model.kinds.Pod as mpod
import kalc.model.system.globals as mGlobalVar
from kalc.model.kinds.ReplicaSet import ReplicaSet
from kalc.model.system.primitives import Status, Label
from kalc.misc.const import STATUS_POD, STATUS_SCHED, StatusDeployment
import kalc.model.kinds.Node as mnode
import kalc.model.kinds.Deployment as mdeployment
from poodle import *
from typing import Set
from logzero import logger
import kalc.misc.util as util
import random
import yaml, copy, jsonpatch, difflib

def calculate_maxNumberOfPodsOnSameNode_metrics(self, object_space):
    deployments = filter(lambda x: isinstance(x, mdeployment.Deployment), object_space)
    pods = filter(lambda x: isinstance(x, mpod.Pod), object_space)
    nodes = filter(lambda x: isinstance(x,mnode.Node), object_space)
    globalVar = next(filter(lambda x: isinstance(x, mGlobalVar.GlobalVar), object_space))
    deploymentController_max_node_amount_of_pods_list = []
    for deploymentController in deployments:
        node_amount_of_pods_list = []
        for node in nodes:
            amount_of_deployment_pod_on_node = 0
            for pod in node.allocatedPodList:
                if pod in deploymentController.podList:
                    amount_of_deployment_pod_on_node += 1
            for pod in node.allocatedPodList:
                if pod in deploymentController.podList:
                    pod.amount_of_deployment_pod_on_node = amount_of_deployment_pod_on_node
            node_amount_of_pods_list.append(amount_of_deployment_pod_on_node)
        if len(node_amount_of_pods_list) == 0:
            pass
        else:
            deploymentController.NumberOfPodsOnSameNodeForDeployment = max(node_amount_of_pods_list)
        deploymentController_max_node_amount_of_pods_list.append(deploymentController.NumberOfPodsOnSameNodeForDeployment)
    if len(deploymentController_max_node_amount_of_pods_list) == 0:
        pass
    else:
        globalVar.maxNumberOfPodsOnSameNodeForDeployment = max(deploymentController_max_node_amount_of_pods_list)
    for pod in pods:
        pod.calc_currently_processed_amount_of_deployment_pod_on_node = globalVar.maxNumberOfPodsOnSameNodeForDeployment