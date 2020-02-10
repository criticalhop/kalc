import kalc.model.kinds.Pod as mpod
import kalc.model.kinds.Node as mnode
import kalc.model.kinds.Deployment as mdeployment
from kalc.misc.const import *
from logzero import logger
import math
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
class Metric():
    mem_free: int
    cpu_free: int
    deployment_fault_tolerance_metric: float

    def __init__(self, object_space):
        self.deployments = list(filter(lambda x: isinstance(
            x, mdeployment.Deployment), object_space))
        self.pods = list(
            filter(lambda x: isinstance(x, mpod.Pod), object_space))
        self.nodes = list(
            filter(lambda x: isinstance(x, mnode.Node), object_space))
        self.moved_pod_set = set([])
        self.drained_node_set = set([])
        self.touched_node_set = set([])
        self.run_time = 0
        # self.globalVar = next(filter(lambda x: isinstance(x, mGlobalVar.GlobalVar), object_space))
        # self.setUnusedRes()

    def progressive_sum(self, n):
        return n*(n+1)/2

    # todo repair
    def setUnusedRes(self):
        self.cpu_used = 0
        self.cpu_total = 0
        self.mem_used = 0
        self.mem_total = 0
        for node in self.nodes:
            if not node.status == STATUS_NODE["Active"]:
                continue
            self.cpu_total = self.cpu_total + node.cpuCapacity._get_value()
            self.mem_total = self.mem_total + node.memCapacity._get_value()
        for pod in self.pods:
            if not pod.status == STATUS_POD["Pending"]:
                continue
            self.cpu_used = self.cpu_used + pod.currentFormalCpuConsumption
            self.mem_used = self.mem_used + pod.currentFormalMemConsumption
        self.mem_free = self.cpu_total - self.cpu_used
        self.cpu_free = self.cpu_total - self.cpu_used

    def fault_tolerance(self):
        self.faultToleranceSquare = {}

        self.faultToleranceGeom = {}
        self.progressive_pod_sum = 0

        for deployment in self.deployments:
            pods_at_node = {}
            faultToleranceSquare = 0
            faultToleranceGeom = 1
            faultToleranceSquareHalfProgressive = 0
            podAmount = float(len(deployment.podList._get_value()))
            # print(podAmount)
            for pod in deployment.podList._get_value():
                pods_at_node[str(pod.atNode._property_value.metadata_name)] = pods_at_node.get(
                    str(pod.atNode._property_value.metadata_name), 0.0) + 1.0
            # print(pods_at_node)
            for nodeId in pods_at_node:
                # print("pod on node ", nodeId, " ", pods_at_node[nodeId])
                faultToleranceSquare += (
                    float(pods_at_node[nodeId]) / podAmount) ** 2
                faultToleranceSquareHalfProgressive += (float(pods_at_node[nodeId]) / podAmount +
                                                        float(pods_at_node[nodeId]) / podAmount) ** 2
                for i in range(int(pods_at_node[nodeId])):
                    self.progressive_pod_sum += i + 1
                faultToleranceGeom *= float(pods_at_node[nodeId]) / podAmount
            self.faultToleranceSquare[deployment._get_value()] = math.sqrt( # pylint: disable=no-member
                faultToleranceSquare)
            self.faultToleranceGeom[deployment._get_value()] = math.pow( # pylint: disable=no-member
                faultToleranceGeom, len(pods_at_node))
            deployment.metric = self.faultToleranceSquare[deployment._get_value(
            )]
        self.deployment_fault_tolerance_metric = 0
        self.deployment_fault_tolerance_metric_bad = 0  # the worst case
        for d in self.deployments:
            self.deployment_fault_tolerance_metric += d.metric
            if self.deployment_fault_tolerance_metric_bad < d.metric:
                self.deployment_fault_tolerance_metric_bad = d.metric
        self.deployment_fault_tolerance_metric = self.deployment_fault_tolerance_metric / \
            (len(self.deployments))

    def nodeOverSubscribe(self):
        self.node_oversubscribe_cpu = 0
        self.node_oversubscribe_mem = 0
        node_oversubscribe_cpu = 0
        node_oversubscribe_mem = 0
        node_oversubscribe = 0
        self.mem_used = 0
        self.cpu_used = 0
        self.mem_total = 0
        self.cpu_total = 0
        self.RMSD = 0 #root-mean-square deviation(RMSD)
        self.RMSD_cpu = 0
        self.RMSD_mem = 0
        self.MD = 0  # maximum deviation

        # Mean node over subscribe per resouces
        for node in self.nodes:
            if str(node.status._get_value()) == str(STATUS_NODE["Inactive"]):
                continue
            node.oversubscribe_cpu = node.currentFormalCpuConsumption._get_value() / \
                node.cpuCapacity._get_value()
            node.oversubscribe_mem = node.currentFormalMemConsumption._get_value() / \
                node.memCapacity._get_value()
            node.oversubscribe = (
                node.oversubscribe_cpu + node.oversubscribe_mem) / 2
            node_oversubscribe += node.oversubscribe
            node_oversubscribe_mem += node.oversubscribe_mem
            node_oversubscribe_cpu += node.oversubscribe_cpu

            self.mem_used += node.currentFormalMemConsumption._get_value()
            self.cpu_used += node.currentFormalCpuConsumption._get_value()
            self.mem_total += node.memCapacity._get_value()
            self.cpu_total += node.cpuCapacity._get_value()

        self.node_oversubscribe_cpu = node_oversubscribe_cpu / \
            (len(self.nodes))
        self.node_oversubscribe_mem = node_oversubscribe_mem / \
            (len(self.nodes))
        self.node_oversubscribe = node_oversubscribe / (len(self.nodes))

        # root-mean-square deviation(RMSD)
        for node in self.nodes:
            if str(node.status._get_value()) == str(STATUS_NODE["Inactive"]):
                continue
            self.RMSD_cpu += (self.node_oversubscribe_cpu - node.oversubscribe_cpu) ** 2
            self.RMSD_mem += (self.node_oversubscribe_mem - node.oversubscribe_mem) ** 2
            if self.MD < abs(self.node_oversubscribe_cpu - node.oversubscribe_cpu):
                self.MD = abs(self.node_oversubscribe_cpu -
                              node.oversubscribe_cpu)
            if self.MD < abs(self.node_oversubscribe_mem - node.oversubscribe_mem):
                self.MD = abs(self.node_oversubscribe_mem -
                              node.oversubscribe_mem)

        self.RMSD_cpu = self.RMSD_cpu / (len(self.nodes))
        self.RMSD_mem = self.RMSD_mem / (len(self.nodes))
        self.RMSD = (self.RMSD_cpu + self.RMSD_mem) / 2
        
        self.mem_free = self.mem_total - self.mem_used
        self.cpu_free = self.cpu_total - self.cpu_used

        self.mem_utilization = float(self.mem_used) / float(self.mem_total)
        self.cpu_utilization = float(self.cpu_used) / float(self.cpu_total)
        self.node_utilization = (self.mem_utilization + self.cpu_utilization) / 2.0

    def total_metric(self):
        self.metric = (self.RMSD + self.MD + self.node_oversubscribe + self.deployment_fault_tolerance_metric + self.deployment_fault_tolerance_metric_bad)/5

    def calc(self):
        # self.setUnusedRes()
        self.fault_tolerance()
        self.nodeOverSubscribe()
        self.total_metric()

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
            node_amount_of_pods_list.append(amount_of_deployment_pod_on_node)
        if len(node_amount_of_pods_list) == 0:
            deploymentController.NumberOfPodsOnSameNodeForDeployment = 1
        else:
            deploymentController.NumberOfPodsOnSameNodeForDeployment = max(node_amount_of_pods_list)
        deploymentController_max_node_amount_of_pods_list.append(deploymentController.NumberOfPodsOnSameNodeForDeployment)
    if len(deploymentController_max_node_amount_of_pods_list) == 0:
        globalVar.maxNumberOfPodsOnSameNodeForDeployment = 1
    else:
        globalVar.maxNumberOfPodsOnSameNodeForDeployment = max(deploymentController_max_node_amount_of_pods_list)