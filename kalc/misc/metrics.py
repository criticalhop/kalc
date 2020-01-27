import kalc.model.kinds.Pod as mpod
import kalc.model.kinds.Node as mnode
import kalc.model.kinds.Deployment as mdeployment
from kalc.misc.const import *
from logzero import logger
import math

class Metric():
    mem_free: int
    cpu_free: int
    deployment_fault_tolerance_metric: float

    def __init__(self, object_space):
        self.deployments = list(filter(lambda x: isinstance(x, mdeployment.Deployment), object_space))
        self.pods = list(filter(lambda x: isinstance(x, mpod.Pod), object_space))
        self.nodes = list(filter(lambda x: isinstance(x,mnode.Node), object_space))
        # self.globalVar = next(filter(lambda x: isinstance(x, mGlobalVar.GlobalVar), object_space))
        # self.setUnusedRes()

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
        for deployment in self.deployments:
            pods_at_node = {}
            faultToleranceSquare = 0
            faultToleranceGeom = 1
            podAmount = float(len(deployment.podList._get_value()))
            # print(podAmount)
            for pod in deployment.podList._get_value():
                pods_at_node[str(pod.atNode._property_value.metadata_name)] = pods_at_node.get(str(pod.atNode._property_value.metadata_name), 0.0) + 1.0
            # print(pods_at_node)
            for nodeId in pods_at_node:
                print("pod on node ",nodeId, " ", pods_at_node[nodeId])
                faultToleranceSquare += (float(pods_at_node[nodeId]) / podAmount) ** 2
                faultToleranceGeom *= float(pods_at_node[nodeId]) / podAmount
            self.faultToleranceSquare[deployment._get_value()] = math.sqrt(faultToleranceSquare)
            self.faultToleranceGeom[deployment._get_value()] = math.pow(faultToleranceGeom, len(pods_at_node))
            deployment.metric = self.faultToleranceSquare[deployment._get_value()]
        self.deployment_fault_tolerance_metric = 0
        for d in self.deployments:
            self.deployment_fault_tolerance_metric = d.metric
        self.deployment_fault_tolerance_metric = self.deployment_fault_tolerance_metric / (len(self.deployments))

    def nodeOverSubscribe(self):
        node_oversubscribe_cpu = 0
        node_oversubscribe_mem = 0
        for node in self.nodes:
           node_oversubscribe_cpu += node.currentFormalCpuConsumption / node.cpuCapacity
           node_oversubscribe_mem += node.currentFormalMemConsumption / node.memCapacity
        self.node_oversubscribe_cpu = node_oversubscribe_cpu / (len(self.nodes))
        self.node_oversubscribe_mem = node_oversubscribe_mem / (len(self.nodes))