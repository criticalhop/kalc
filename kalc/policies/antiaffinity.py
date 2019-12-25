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
    KIND = Pod

    @planned(cost=1)
    def mark_checked_pod_as_antiaffinity_checked_for_target_pod(self,
        checked_pod: Pod,
        target_pod: Pod,
        node_of_target_pod: Node,
        node_of_checked_pod: Node,
        globalVar: GlobalVar,
        scheduler: Scheduler):
        if checked_pod in target_pod.podsMatchedByAntiaffinity and \
            target_pod.antiaffinity_set == True and \
            checked_pod.atNode != target_pod.atNode and \
            checked_pod not in target_pod.calc_antiaffinity_pods_list and \
            globalVar.block_policy_calculated == True :
                target_pod.calc_antiaffinity_pods_list.add(checked_pod)
                target_pod.calc_antiaffinity_pods_list_length += 1
        target_pod.antiaffinity_set = True



    @planned(cost=1)
    def mark_antiaffinity_met(self,
        target_pod: Pod,
        globalVar: GlobalVar):
        assert globalVar.block_policy_calculated == True
        assert target_pod.calc_antiaffinity_pods_list_length == target_pod.target_number_of_antiaffinity_pods
        target_pod.antiaffinity_met = True
    
    def generate_goal(self):
        self.generated_goal_in = []
        self.generated_goal_eq = []
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_met, True])
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_preferred_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_preferred_met, True])

    def goal(self):
        for what, where in self.generated_goal_in:
            assert what in where
        for what1, what2 in self.generated_goal_eq:
            assert what1 == what2
    @planned(cost=1)
    def Add_node(self,
            node : Node):
        assert node.status == STATUS_NODE["New"]
        node.status = STATUS_NODE["Active"]