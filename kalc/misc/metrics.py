import kalc.model.kinds.Pod as mpod
import kalc.model.kinds.Node as mnode
import kalc.model.kinds.Deployment as mdeployment
from logzero import logger
import math

class Metric():

    def __init__(self, object_space):
        self.deployments = filter(lambda x: isinstance(x, mdeployment.Deployment), object_space)
        self.pods = filter(lambda x: isinstance(x, mpod.Pod), object_space)
        self.nodes = filter(lambda x: isinstance(x,mnode.Node), object_space)
        # self.globalVar = next(filter(lambda x: isinstance(x, mGlobalVar.GlobalVar), object_space))
        # self.setUnusedRes()

    def setUnusedRes(self):
        self.cpuUsed = 0
        self.cpuTotal = 0
        self.memUsed = 0 
        self.memTotal = 0
        for node in self.nodes:
            self.cpuTotal += node.cpuCapacity
            self.memTotal += node.memCapacity
        for pod in self.pods:
            self.cpuUsed += pod.currentRealCpuConsumption
            self.memUsed += pod.currentRealMemConsumption
        self.memFree = self.cpuTotal - self.cpuUsed
        self.cpuFree = self.cpuTotal - self.cpuUsed 

    def faultTolerance(self):
        self.faultToleranceSquare = {}

        self.faultToleranceGeom = {}
        pods_at_node = {}
        for deployment in self.deployments:
            faultToleranceSquare = 0
            faultToleranceGeom = 1
            podAmount = float(len(deployment.podList._get_value()))
            print(podAmount)
            for pod in deployment.podList._get_value():
                pods_at_node[pod.atNode] = pods_at_node.get(pod.atNode, 0.0) + 1.0
            print(pods_at_node)
            for nodeId in pods_at_node:
                # print("pod on node ", pods_at_node[nodeId])
                faultToleranceSquare += (float(pods_at_node[nodeId]) / podAmount) ** 2
                faultToleranceGeom *= float(pods_at_node[nodeId]) / podAmount
            self.faultToleranceSquare[deployment] = math.sqrt(faultToleranceSquare)
            self.faultToleranceGeom[deployment] = math.pow(faultToleranceGeom, len(pods_at_node))
            deployment.metric = self.faultToleranceSquare[id(deployment)]
        self.deployment_metric = 0
        for d in self.deployments:
            self.deployment_metric = d.metric
        self.deployment_metric = self.deployment_metric / (len(self.deployments))

    def faultTolerance(self):
        node_oversubscribe_cpu = 0
        node_oversubscribe_mem = 0
        for node in self.nodes:
           node_oversubscribe_cpu += node.currentFormalCpuConsumption / node.cpuCapacity
           node_oversubscribe_mem += node.currentFormalMemConsumption / node.memCapacity
        self.node_oversubscribe_cpu = node_oversubscribe_cpu / (len(self.nodes))
        self.node_oversubscribe_mem = node_oversubscribe_mem / (len(self.nodes))