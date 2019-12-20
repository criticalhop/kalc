from typing import Set
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.misc.const import *
from poodle import planned

from kalc.policy import policy_engine, BasePolicy

class PreferredSelfAntiAffinityPolicy(BasePolicy):
    TYPE = "property"
    KIND = Service

    def register(self):
        Service.register_property(name="antiaffinity", type=bool, default=False)
        Service.register_property(name="antiaffinity_prefered_policy_met", type=bool, default=False)
        Service.register_property(name="targetAmountOfPodsOnDifferentNodes", type=int, default=-1)
        Pod.register_property(name="not_on_same_node", type=Set[Pod], default=None)

    def set(self, val: bool):
        assert isinstance(val, bool), "Can only accept True or False"

        # TODO 1: do we have anti affinity already?
           # 1.1: anti affinity policy satisfied already
           # 1.2: anti affinity is implemented in settings
        # TODO 2: add anti affinity if it is not there
        # TODO 3: check that it will not break cluster
        # TODO 4: find solution to fix cluster if #3 fails

        if val:
            # enable
            pods_count = len(list(self.target_object.podList))

            assert pods_count <= 5, "We currently support up to 5 pods"

            def hypothesis_existing_match_group():
                # TODO: 

            def hypothesis_new_match_group():
                # TODO: hypotheses can not work in parallel this way: will modify main object

                # TODO: create a new group before start
                self.target_object.antiaffinity = True
                self.target_object.targetAmountOfPodsOnDifferentNodes = pods_count
                self.register_goal(self.target_object.antiaffinity_prefered_policy_met, "==", True)
            
            self.register_hypothesis("All pods required done", hypothesis_1)
        else:
            # disable
            pass

    @planned
    def add_pods_to_antiaffinity_group(self, 
            pod: Pod,
            pod_other: Pod):
        pod.anti_affinite_with.add(pod_other)
        # TODO we need a restart after this to check that it didn't break things

    @planned(cost=1)
    def mark_antiaffinity_prefered_policy_enabled(self,
        service: Service,
        globalVar: GlobalVar):
        assert service.amountOfPodsOnDifferentNodes == service.targetAmountOfPodsOnDifferentNodes
        assert service.antiaffinity == True
        service.antiaffinity_prefered_policy_met = True

    @planned(cost=1)
    def mark_antiaffinity_prefered_policy_met(self,
        service: Service,
        globalVar: GlobalVar):
        assert service.amountOfPodsOnDifferentNodes == service.targetAmountOfPodsOnDifferentNodes
        assert service.antiaffinity == True
        service.antiaffinity_prefered_policy_met = True

    @planned(cost=1)
    def mark_2_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            service: Service,
            scheduler: Scheduler):
        assert node_of_pod2 == pod2.atNode
        assert pod1.atNode in node_of_pod2.different_than
        assert pod1 in service.podList
        assert pod2 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        pod1.not_on_same_node.add(pod2)
        service.amountOfPodsOnDifferentNodes = 2

    @planned(cost=1)
    def mark_3_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            pod3: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            node_of_pod3: Node,
            service: Service,
            scheduler: Scheduler):
        
        assert node_of_pod1 == pod1.atNode
        assert node_of_pod2 == pod2.atNode
        assert node_of_pod3 == pod3.atNode
        assert node_of_pod1 in node_of_pod2.different_than
        assert node_of_pod1 in node_of_pod3.different_than
        assert node_of_pod2 in node_of_pod3.different_than
        assert pod1 in service.podList
        assert pod2 in service.podList
        assert pod3 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        service.amountOfPodsOnDifferentNodes = 3

    @planned(cost=1)
    def mark_4_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            pod3: Pod,
            pod4: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            node_of_pod3: Node,
            node_of_pod4: Node,
            service: Service,
            scheduler: Scheduler):
        
        assert node_of_pod1 == pod1.atNode
        assert node_of_pod2 == pod2.atNode
        assert node_of_pod3 == pod3.atNode
        assert node_of_pod4 == pod4.atNode
        assert node_of_pod1 in node_of_pod2.different_than
        assert node_of_pod1 in node_of_pod3.different_than
        assert node_of_pod1 in node_of_pod4.different_than
        assert node_of_pod2 in node_of_pod3.different_than
        assert node_of_pod2 in node_of_pod4.different_than
        assert node_of_pod3 in node_of_pod4.different_than
        assert pod1 in service.podList
        assert pod2 in service.podList
        assert pod3 in service.podList
        assert pod4 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        service.amountOfPodsOnDifferentNodes = 4

    @planned(cost=1)
    def mark_5_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            pod3: Pod,
            pod4: Pod,
            pod5: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            node_of_pod3: Node,
            node_of_pod4: Node,
            node_of_pod5: Node,
            service: Service,
            scheduler: Scheduler):
        
        assert node_of_pod1 == pod1.atNode
        assert node_of_pod2 == pod2.atNode
        assert node_of_pod3 == pod3.atNode
        assert node_of_pod4 == pod4.atNode
        assert node_of_pod5 == pod5.atNode
        assert node_of_pod1 in node_of_pod2.different_than
        assert node_of_pod1 in node_of_pod3.different_than
        assert node_of_pod1 in node_of_pod4.different_than
        assert node_of_pod1 in node_of_pod5.different_than
        assert node_of_pod2 in node_of_pod3.different_than
        assert node_of_pod2 in node_of_pod4.different_than
        assert node_of_pod2 in node_of_pod5.different_than
        assert node_of_pod3 in node_of_pod4.different_than
        assert node_of_pod3 in node_of_pod5.different_than
        assert node_of_pod4 in node_of_pod5.different_than

        assert pod1 in service.podList
        assert pod2 in service.podList
        assert pod3 in service.podList
        assert pod4 in service.podList
        assert pod5 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        service.amountOfPodsOnDifferentNodes = 5

policy_engine.register(Service, "self_antiaffinity", PreferredSelfAntiAffinityPolicy)

