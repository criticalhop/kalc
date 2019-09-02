from poodle import Object, planned
from typing import Set
from guardctl.misc.const import *
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.Node import Node
from guardctl.model.system.primitives import StatusSched, String


class Scheduler(Object):
    queueLength: int
    status: String
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

    @planned(cost=100)
    def StartPod(self, 
        podStarted: "mpod.Pod",
        node1: "Node" ,
        scheduler1: "Scheduler",
        serviceTargetForPod: "mservice.Service",
        globalVar1: "GlobalVar"
        ):

        assert podStarted in scheduler1.podQueue
        assert podStarted.toNode == node1
        assert podStarted.targetService == serviceTargetForPod
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node1.currentFormalCpuConsumption + podStarted.cpuRequest < node1.cpuCapacity + 1
        assert node1.currentFormalMemConsumption + podStarted.memRequest < node1.memCapacity + 1

        node1.currentFormalCpuConsumption += podStarted.cpuRequest
        node1.currentFormalMemConsumption += podStarted.memRequest
        globalVar1.currentFormalCpuConsumption += podStarted.cpuRequest
        globalVar1.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node1        
        scheduler1.queueLength -= 1
        scheduler1.podQueue.remove(podStarted)
 
        serviceTargetForPod.amountOfActivePods += 1
        podStarted.status_phase = STATUS_POD_RUNNING 
        serviceTargetForPod.status = STATUS_SERV_STARTED
           
    @planned(cost=1000)
    def ScheduleQueueProcessed1(self, scheduler1: "Scheduler"):
        scheduler1.queueLength -= 1

        #to-do: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
    
    @planned(cost=100)
    def ScheduleQueueProcessed(self, scheduler1: "Scheduler"):
        assert  scheduler1.queueLength == 0
        scheduler1.status = STATUS_SCHED_CLEAN