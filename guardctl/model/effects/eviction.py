from poodle import planned
from guardctl.model.object.k8s_classes import *
from guardctl.misc.const import *
from guardctl.model.effects.abstract import Effect

class K8prioritiyEviction(Effect):
    @planned(cost=100)
    def EvictAndReplaceLessPrioritizedPod(self,
                podPending: Pod,
                podToBeReplaced: Pod,
                node1: Node,
                scheduler1: Scheduler,
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass,
                preemptionPolicyOfPendingPod: Type,
                preemptionPolicyOfPodToBeReplaced: Type,
                statustest: Status,
                podtypetest: Type
                ):
        assert podPending in scheduler1.podQueue
        assert podPending.status == STATUS_POD_PENDING 
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass 
        assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podToBeReplaced.status == STATUS_POD_ACTIVE
        podToBeReplaced.status = STATUS_POD_KILLING