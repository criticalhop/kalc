from typing import Set
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.misc.const import *
from poodle import planned
from kalc.policy import policy_engine, BasePolicy

from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.kubernetes import KubernetesCluster
from kalc.misc.const import *


class BalancedClusterPolicy(BasePolicy):
    TYPE = "property"

    def register(self):
        GlobalVar.register_property(name="deploymentsWithAntiaffinityBalanced", type=bool, default=False)
        GlobalVar.register_property(name="add_node_enabled", type=bool, default=False)

    def set(self, val: bool):
        assert isinstance(val, bool), "Can only accept True or False"

        if val:
            # enable

            def hypothesis_do_rebalance_2_pods():
                # TODO: hypotheses can not work in parallel this way: will modify main object
                self.register_goal(self.target_object.deploymentsWithAntiaffinityBalanced, "==", True)

            def hypothesis_do_rebalance_allow_add_node():
                # TODO: hypotheses can not work in parallel this way: will modify main object
                self.target_object.add_node_enabled = True
                self.register_goal(self.target_object.deploymentsWithAntiaffinityBalanced, "==", True)
            
            self.register_hypothesis("2 pods rebalanced", hypothesis_do_rebalance_2_pods, order=1)
            self.register_hypothesis("Added node to help with pods rebalancing", hypothesis_do_rebalance_allow_add_node, order=10)
        else:
            # disable
            pass

    @planned(cost=1)
    def mark_checked_pod_as_antiaffinity_checked_for_target_pod(self,
        target_pod: Pod,
        antiaffinity_pod: Pod,
        globalVar: GlobalVar,
        scheduler: Scheduler,
        antiaffinity_pod_node: Node):
        if antiaffinity_pod.atNode != target_pod.atNode and \
                    target_pod.antiaffinity_set == True and \
                antiaffinity_pod not in target_pod.calc_antiaffinity_pods_list:
                target_pod.calc_antiaffinity_pods_list.add(antiaffinity_pod)
                target_pod.calc_antiaffinity_pods_list_length += 1
        assert antiaffinity_pod in target_pod.podsMatchedByAntiaffinity 
        assert antiaffinity_pod.atNode == antiaffinity_pod_node
        assert antiaffinity_pod_node.isNull == False
        # assert globalVar.block_policy_calculated == True
        globalVar.block_policy_calculated = True


    @planned(cost=1)
    def calculate_length_of_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod(self,
        target_pod: Pod,
        antiaffinity_pod: Pod,
        antiaffinity_pod_node: Node,
        debug_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length: int):
        assert antiaffinity_pod in target_pod.podsMatchedByAntiaffinity
        assert antiaffinity_pod in target_pod.calc_affinity_pods_list
        assert antiaffinity_pod_node == antiaffinity_pod.atNode
        if antiaffinity_pod_node not in target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod:
            assert debug_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length == target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length           
            target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod.add(antiaffinity_pod_node)
            target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length += 1


    @planned(cost=1)
    def mark_checked_pod_as_affinity_checked_for_target_pod(self,
        target_pod: Pod,
        checked_pod: Pod,
        globalVar: GlobalVar,
        scheduler: Scheduler):
        if checked_pod.atNode == target_pod.atNode and \
                    target_pod.affinity_set == True and \
                checked_pod not in target_pod.calc_affinity_pods_list:
                target_pod.calc_affinity_pods_list.add(checked_pod)
                target_pod.calc_affinity_pods_list_length += 1
        assert checked_pod in target_pod.podsMatchedByAffinity 
        # assert globalVar.block_policy_calculated == True 
        globalVar.block_policy_calculated = True


    @planned(cost=1)
    def mark_that_node_cant_allocate_pod_by_cpu(self,
        pod: Pod,
        node: Node,
        globalVar: GlobalVar):
        if not node in pod.nodesThatCantAllocateThisPod:
            assert pod.cpuRequest > node.cpuCapacity - node.currentFormalCpuConsumption
            pod.nodesThatCantAllocateThisPod.add(node)
            pod.nodesThatCantAllocateThisPod_length += 1
        # assert globalVar.block_policy_calculated == True
        globalVar.block_policy_calculated = True
        assert node.isNull == False


    @planned(cost=1)
    def mark_that_node_cant_allocate_pod_by_mem(self,
        pod: Pod,
        node: Node,
        globalVar: GlobalVar):
        assert node.isNull == False
        if not node in pod.nodesThatCantAllocateThisPod:
            assert pod.memRequest > node.memCapacity - node.currentFormalMemConsumption
            pod.nodesThatCantAllocateThisPod.add(node)
            pod.nodesThatCantAllocateThisPod_length += 1
        # assert globalVar.block_policy_calculated == True
        globalVar.block_policy_calculated = True

  
    @planned(cost=1)
    def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.calc_antiaffinity_pods_list_length == pod.podsMatchedByAntiaffinity_length
        assert pod.antiaffinity_set == True
        # assert globalVar.block_policy_calculated == True
        pod.antiaffinity_met = True
        globalVar.block_policy_calculated = True


    @planned(cost=1)
    def mark_affinity_met_because_all_affinity_pods_are_matched(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.calc_affinity_pods_list_length == pod.podsMatchedByAffinity_length
        assert pod.affinity_set == True
        # assert globalVar.block_policy_calculated == True
        pod.affinity_met = True
        globalVar.block_policy_calculated = True


    @planned(cost=1)
    def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched_and_those_that_cant_dont_suite(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.calc_antiaffinity_pods_list_length == pod.target_number_of_antiaffinity_pods
        assert pod.antiaffinity_set == True
        # assert globalVar.block_policy_calculated == True
        pod.antiaffinity_met = True
        globalVar.block_policy_calculated = True


    # @planned(cost=1)
    def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched_and_those_that_cant_dont_suite_below_the_limit_for_node_amount(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length + pod.nodesThatCantAllocateThisPod_length == globalVar.amountOfNodes_limit
        assert pod.antiaffinity_set == True
        pod.antiaffinity_met = True

    
    @planned(cost=1)
    def Set_antiaffinity_between_pods_of_deployment(self,
        pod1: Pod,
        pod2: Pod,
        deployment: Deployment,
        globalVar: GlobalVar):
        if pod1 not in pod2.podsMatchedByAffinity and pod2 not in pod1.podsMatchedByAffinity:
            assert pod1 in deployment.podList
            assert pod2 in deployment.podList
            assert deployment.NumberOfPodsOnSameNodeForDeployment == globalVar.maxNumberOfPodsOnSameNodeForDeployment
            pod1.antiaffinity_set = True
            pod1.podsMatchedByAffinity.add(pod2)
            pod1.podsMatchedByAffinity_length += 1
            pod2.antiaffinity_set = True
            pod2.podsMatchedByAffinity.add(pod1)
            pod2.podsMatchedByAffinity_length += 1

 
    @planned(cost=1)
    def Reduce_maxNumberOfPodsOnSameNodeForDeployment(self,
        globalVar: GlobalVar):
        globalVar.maxNumberOfPodsOnSameNodeForDeployment -= 1       
   

    @planned(cost=1)
    def Calculate_fulfilled_antiaffinity_pods_of_deployment(self,
        pod1: Pod,
        pod2: Pod,
        deployment: Deployment):
        assert pod1 in deployment.podList
        assert deployment.amountOfActivePods > 0
        assert pod1.podsMatchedByAffinity_length == deployment.amountOfActivePods
        deployment.amountOfPodsWithAntiaffinity += 1
    

    @planned(cost=1)
    def Calculate_fulfilled_antiaffinity_pods_of_deployment_with_limited_number_of_pods(self,
        pod1: Pod,
        pod2: Pod,
        deployment: Deployment,
        globalVar: GlobalVar):
        assert pod1 in deployment.podList
        assert globalVar.target_amountOfPodsWithAntiaffinity > 0
        assert pod1.podsMatchedByAffinity_length == globalVar.target_amountOfPodsWithAntiaffinity
        deployment.amountOfPodsWithAntiaffinity += 1


    @planned(cost=1)
    def mark_finalization_of_antiaffinity_setting_for_pods_of_deployment(self,
        deployment: Deployment,
        globalVar: GlobalVar):
        assert deployment.amountOfPodsWithAntiaffinity == deployment.amountOfActivePods
        globalVar.amountOfDeploymentsWithAntiaffinity += 1
    

    @planned(cost=1)
    def mark_finalization_of_antiaffinity_setting_for_pods_of_deployment(self,
        deployment: Deployment,
        globalVar: GlobalVar):
        assert globalVar.amountOfDeploymentsWithAntiaffinity == globalVar.target_amountOfDeploymentsWithAntiaffinity
        globalVar.deploymentsWithAntiaffinityBalanced = True


    @planned(cost=1)
    def Add_node(self,
            node : Node,
            globalVar: GlobalVar):
        assert globalVar.add_node_enabled == True
        assert node.status == STATUS_NODE["New"]
        node.status = STATUS_NODE["Active"]
        globalVar.amountOfNodes += 1
    
policy_engine.register(Service, "self_antiaffinity", BalancedClusterPolicy)

