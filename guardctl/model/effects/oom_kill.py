from poodle import planned
from guardctl.model.object.k8s_classes import *
from poodle import arithmetic
from guardctl.misc.const import *
from guardctl.model.effects.abstract import Effect

class K8OOMkill(Effect):
    @planned(cost=100)
    def MarkPodAsOverwhelmingMemLimits(self, podTobeKilled: Pod,nodeOfPod: Node):
        assert podTobeKilled.memLimitsStatus == STATUS_LIM_MET
        assert nodeOfPod == podTobeKilled.atNode
        assert podTobeKilled.memLimit <  podTobeKilled.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits += 1
        podTobeKilled.memLimitsStatus = STATUS_LIM_OVERWHELMED
        
    @planned(cost=100)
    def MarkPodAsNonoverwhelmingMemLimits(self, podTobeReanimated: Pod,
        nodeOfPod: Node, globalVar1: GlobalVar):            
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimitsStatus == STATUS_LIM_OVERWHELMED
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimit >  podTobeReanimated.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits -= 1
        podTobeReanimated.memLimitsStatus = STATUS_LIM_MET
        
    @planned(cost=100)
    def MemoryErrorKillPodOverwhelmingLimits(self,
    nodeOfPod: Node,
    pod1TobeKilled: Pod
    ):
        assert pod1TobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert nodeOfPod.status == STATUS_NODE_ACTIVE
        assert pod1TobeKilled.memLimitsStatus == STATUS_LIM_OVERWHELMED

        pod1TobeKilled.status = STATUS_POD_KILLING


    @planned(cost=100)
    def MemoryErrorKillPodNotOverwhelmingLimits(self,
        nodeOfPod: Node,
        podTobeKilled: Pod):
        assert podTobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert nodeOfPod.status == STATUS_NODE_ACTIVE
        assert podTobeKilled.memLimitsStatus == STATUS_LIM_MET

        podTobeKilled.status = STATUS_POD_KILLING
    
    @planned(cost=100)
    def KillPod(self,
            podBeingKilled : Pod,
            nodeWithPod : Node,
            serviceOfPod: Service,
            globalVar1: GlobalVar,
            scheduler1: Scheduler,
            amountOfActivePodsPrev: int
            
         ):
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.targetService == serviceOfPod
        assert podBeingKilled.status == STATUS_POD_KILLING
        assert podBeingKilled.amountOfActiveRequests == 0
        assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentRealMemConsumption -= podBeingKilled.realInitialMemConsumption
        nodeWithPod.currentRealCpuConsumption -= podBeingKilled.realInitialCpuConsumption
        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -=  podBeingKilled.cpuRequest
        globalVar1.currentFormalMemConsumption -= podBeingKilled.memRequest
        globalVar1.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        podBeingKilled.status = STATUS_POD_FAILED
        scheduler1.podQueue.add(podBeingKilled)
        scheduler1.status = STATUS_SCHED_CHANGED
