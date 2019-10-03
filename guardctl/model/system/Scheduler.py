from poodle import Object, planned
from typing import Set
from guardctl.misc.const import *
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.Node import Node
import guardctl.model.kinds.Deployment as  mdeployment
from guardctl.model.system.primitives import StatusSched
from guardctl.model.scenario import ScenarioStep, describe
import sys


class Scheduler(Object):
    queueLength: int
    status: StatusSched
    podQueue: Set["mpod.Pod"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queueLength = 0

    @planned(cost=100)
    def SelectNode(self, 
        pod1: "mpod.Pod",
        SelectedNode: "Node" ):
        assert pod1.toNode == Node.NODE_NULL
        pod1.toNode = SelectedNode
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Selected node for pod placement",
            parameters={"pod": describe(pod1), "node": describe(SelectedNode)},
            probability=1.0,
            affected=[describe(pod1), describe(SelectedNode)]
        )


    @planned(cost=100)
    def StartPod_IF_service_notnull__deployment_notnull(self, 
        podStarted: "mpod.Pod",
        node1: "Node" ,
        scheduler1: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        deployment_of_pod: "mdeployment.Deployment"
        ):

        assert podStarted in scheduler1.podQueue
        assert podStarted.toNode == node1
        assert podStarted.targetService == serviceTargetForPod
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node1.currentFormalCpuConsumption + podStarted.cpuRequest <= node1.cpuCapacity 
        assert node1.currentFormalMemConsumption + podStarted.memRequest <= node1.memCapacity 
        assert podStarted in deployment_of_pod.podList
        deployment_of_pod.amountOfActivePods += 1
        
        node1.currentFormalCpuConsumption += podStarted.cpuRequest
        node1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node1        
        scheduler1.queueLength -= 1
        scheduler1.podQueue.remove(podStarted)
 
        serviceTargetForPod.amountOfActivePods += 1
        podStarted.status = STATUS_POD["Running"] 
        serviceTargetForPod.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node1)]
        )

    @planned(cost=100)
    def StartPod_IF_service_notnull__deployment_isnull(self, 
        podStarted: "mpod.Pod",
        node1: "Node" ,
        scheduler1: "Scheduler",
        serviceTargetForPod: "mservice.Service"
        # globalVar1: "GlobalVar"
        ):

        assert podStarted in scheduler1.podQueue
        assert podStarted.toNode == node1
        assert podStarted.targetService == serviceTargetForPod
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node1.currentFormalCpuConsumption + podStarted.cpuRequest < node1.cpuCapacity + 1
        assert node1.currentFormalMemConsumption + podStarted.memRequest < node1.memCapacity + 1
        assert podStarted.hasDeployment == False

        node1.currentFormalCpuConsumption += podStarted.cpuRequest
        node1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node1        
        scheduler1.queueLength -= 1
        scheduler1.podQueue.remove(podStarted)
 
        serviceTargetForPod.amountOfActivePods += 1
        podStarted.status = STATUS_POD["Running"] 
        serviceTargetForPod.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node1)]
        )

    @planned(cost=100)
    def StartPod_IF_service_isnull__deployment_isnull(self, 
        podStarted: "mpod.Pod",
        node1: "Node" ,
        scheduler1: "Scheduler"
        ):

        assert podStarted in scheduler1.podQueue
        assert podStarted.toNode == node1
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node1.currentFormalCpuConsumption + podStarted.cpuRequest < node1.cpuCapacity + 1
        assert node1.currentFormalMemConsumption + podStarted.memRequest < node1.memCapacity + 1
        assert podStarted.hasService == False
        assert podStarted.hasDeployment == False

        node1.currentFormalCpuConsumption += podStarted.cpuRequest
        node1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node1        
        scheduler1.queueLength -= 1
        scheduler1.podQueue.remove(podStarted)
 
        podStarted.status = STATUS_POD["Running"] 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node1)]
        )

    @planned(cost=100)
    def StartPod_IF_service_isnull__deployment_notnull(self, 
        podStarted: "mpod.Pod",
        node1: "Node" ,
        scheduler1: "Scheduler",
        deployment_of_pod: "mdeployment.Deployment"
        ):

        assert podStarted in scheduler1.podQueue
        assert podStarted.toNode == node1
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node1.currentFormalCpuConsumption + podStarted.cpuRequest < node1.cpuCapacity + 1
        assert node1.currentFormalMemConsumption + podStarted.memRequest < node1.memCapacity + 1
        assert podStarted in deployment_of_pod.podList
        assert podStarted.hasService == False
        assert podStarted.hasDeployment == True


        node1.currentFormalCpuConsumption += podStarted.cpuRequest
        node1.currentFormalMemConsumption += podStarted.memRequest
        # globalVar1.currentFormalCpuConsumption += podStarted.cpuRequest
        # globalVar1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node1        
        scheduler1.queueLength -= 1
        scheduler1.podQueue.remove(podStarted)
        deployment_of_pod.amountOfActivePods += 1
        podStarted.status = STATUS_POD["Running"] 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node1)]
        )

    @planned(cost=10000)
    def Scheduler_cant_allocate_pod(self, scheduler1: "Scheduler"):
        scheduler1.queueLength -= 1
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Can't place a pod",
            parameters={},
            probability=1.0,
            affected=[]
        )

        #todo: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
    
    @planned(cost=100)
    def ScheduleQueueProcessed(self, scheduler1: "Scheduler"):
        assert  scheduler1.queueLength == 0
        scheduler1.status = STATUS_SCHED["Clean"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Finished processing pod queue",
            parameters={},
            probability=1.0,
            affected=[]
        )