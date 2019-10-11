from poodle import Object, planned
from typing import Set
from guardctl.misc.const import *
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.Node import Node
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
    def StartPod(self, 
        podStarted: "mpod.Pod",
        node: "Node" ,
        scheduler: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        # globalVar1: "GlobalVar"
        ):

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert podStarted.targetService == serviceTargetForPod
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest < node.cpuCapacity + 1
        assert node.currentFormalMemConsumption + podStarted.memRequest < node.memCapacity + 1

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        # globalVar1.currentFormalCpuConsumption += podStarted.cpuRequest
        # globalVar1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node        
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
 
        serviceTargetForPod.amountOfActivePods += 1
        podStarted.status = STATUS_POD["Running"] 
        serviceTargetForPod.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )
    
    @planned(cost=100)
    def StartPod_IF_hasService_isNull(self, 
        podStarted: "mpod.Pod",
        node: "Node" ,
        scheduler: "Scheduler"
        ):

        assert podStarted in scheduler.podQueue
        assert podStarted.toNode == node
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest < node.cpuCapacity + 1
        assert node.currentFormalMemConsumption + podStarted.memRequest < node.memCapacity + 1

        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node        
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
 
        podStarted.status = STATUS_POD["Running"] 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Starting pod",
            parameters={"podStarted": describe(podStarted)},
            probability=1.0,
            affected=[describe(podStarted), describe(node)]
        )


    @planned(cost=1000000)
    def ScheduleQueueProcessed1(self, scheduler: "Scheduler"):
        scheduler.queueLength -= 1
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
    def ScheduleQueueProcessed(self, scheduler: "Scheduler"):
        assert  scheduler.queueLength == 0
        scheduler.status = STATUS_SCHED["Clean"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Finished processing pod queue",
            parameters={},
            probability=1.0,
            affected=[]
        )