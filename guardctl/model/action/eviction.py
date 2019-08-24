from poodle import planned
from object.kubeObject import *
# kubernetes scheduler module

class K8prioritiyEviction:
    @planned
    def EvictAndReplaceLessPrioritizedPod(self,
                podPending: Pod,
                podToBeReplaced: Pod,
                node1: Node,
                scheduler1: Scheduler,
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass):
        assert podPending in scheduler1.podQueue
        assert podPending.status == self.constSymbol["statusPodPending"]    
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass 
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podToBeReplaced.status == self.constSymbol["statusPodActive"]
        podToBeReplaced.status = self.constSymbol['statusPodKilling']