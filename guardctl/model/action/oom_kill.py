from poodle import planned
from guardctl.model.object.k8s_classes import *
from poodle import arithmetic

class K8OOMkill:
    @planned(cost=100)
    def MarkPodAsOverwhelmingMemLimits(self, podTobeKilled: Pod,nodeOfPod: Node):
        assert podTobeKilled.memLimitsStatus == self.constSymbol["statusLimMet"]
        assert nodeOfPod == podTobeKilled.atNode
        assert podTobeKilled.memLimit <  podTobeKilled.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits += 1
        podTobeKilled.memLimitsStatus = self.constSymbol["statusLimOverwhelmed"]
        
    @planned(cost=100)
    def MarkPodAsNonoverwhelmingMemLimits(self, podTobeReanimated: Pod,
        nodeOfPod: Node, globalVar1: GlobalVar):            
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimitsStatus == self.constSymbol["statusLimOverwhelmed"]
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimit >  podTobeReanimated.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits -= 1
        podTobeReanimated.memLimitsStatus = self.constSymbol["statusLimMet"]
        
    @planned(cost=100)
    def MemoryErrorKillPodOverwhelmingLimits(self,
    nodeOfPod: Node,
    pod1TobeKilled: Pod
    ):
        assert pod1TobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert nodeOfPod.status == self.constSymbol['statusNodeActive']
        assert pod1TobeKilled.memLimitsStatus == self.constSymbol["statusLimOverwhelmed"]

        pod1TobeKilled.status = self.constSymbol['statusPodKilling']


    @planned(cost=100)
    def MemoryErrorKillPodNotOverwhelmingLimits(self,
        nodeOfPod: Node,
        podTobeKilled: Pod):
        assert podTobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert nodeOfPod.status == self.constSymbol['statusNodeActive']
        assert podTobeKilled.memLimitsStatus == self.constSymbol["statusLimMet"]

        podTobeKilled.status = self.constSymbol['statusPodKilling']
    
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
        assert podBeingKilled.status == self.constSymbol['statusPodKilling']
        assert podBeingKilled.amountOfActiveRequests == 0
        assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

        nodeWithPod.currentRealMemConsumption -= podBeingKilled.realInitialMemConsumption
        nodeWithPod.currentRealCpuConsumption -= podBeingKilled.realInitialCpuConsumption
        nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
        nodeWithPod.currentFormalCpuConsumption -=  podBeingKilled.cpuRequest
        globalVar1.currentFormalMemConsumption -= podBeingKilled.memRequest
        globalVar1.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        serviceOfPod.amountOfActivePods -= 1
        podBeingKilled.status = self.constSymbol['statusPodFailed']
        scheduler1.podQueue.add(podBeingKilled)
        scheduler1.status = self.constSymbol["statusSchedChanged"]
