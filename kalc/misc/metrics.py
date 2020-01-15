from kalc.model.kinds.Pod import 
from kalc.model.kinds.Node import
from kalc.model.kinds.Deployment import Deployment
from logzero import logger
import math

class Metric():
    maxNumberOfPodsOnSameNodeForDeployment: int
    meanPercentageOnTheSameNode: int

    def __init__(self, object_space):
        self.deployments = filter(lambda x: isinstance(x, mdeployment.Deployment), object_space)
        self.pods = filter(lambda x: isinstance(x, mpod.Pod), object_space)
        self.nodes = filter(lambda x: isinstance(x,mnode.Node), object_space)
        self.globalVar = next(filter(lambda x: isinstance(x, mGlobalVar.GlobalVar), object_space))
        self.setUnusedRes()

    def setUnusedRes(self):
        self.cpuUsed = 0
        self.cpuTotal = 0
        self.memUsed = 0 
        self.memTotal = 0
        for node in self.nodes:
            self.cpuTotal += node.cpuCapacity
            self.memTotal += node.memCapacity
        for pod in self.pods:
            self.cpuUsed += podcurrentRealCpuConsumption
            self.memUsed += podcurrentRealCpuConsumption
        self.memFree = self.cpuTotal - self.cpuUsed
        self.cpuFree = self.cpuTotal - self.cpuUsed 

    def faultTolerance(self):
        self.faultTolerance = {}
        faultTolerance = 0
        nodes = {}
        for deployment in self.deployments:
            for pod in deployment.pod_list:
                nodes[id(pod.atNode)] = nodes.get(id(pod.atNode), 0.0) + 1.0
            for node in nodes:
                faultToleranceSquare += (float(node) / float(len(deployment.pod_list))) ** 2
                faultToleranceGeom += float(node) / float(len(deployment.pod_list))
            self.faultToleranceSquare = math.sqrt(faultTolerance)
            self.faultToleranceGeom = math.pow(faultToleranceGeom, len(node))


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