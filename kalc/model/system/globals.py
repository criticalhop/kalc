from poodle import Object
from kalc.model.system.primitives import Type, Status
from kalc.model.system.base import ModularKind
import kalc.model.kinds.Deployment as mdeployment
import kalc.model.kinds.Node as mnode
from typing import Set

class GlobalVar(ModularKind):
    is_deployment_disrupted: bool
    is_deployment_distuption_searchable: bool
    is_service_disrupted: bool
    is_service_disruption_searchable: bool
    is_node_disrupted: bool
    amountOfNodesDisrupted: int
    limitOfAmountOfNodesDisrupted: int
    amountOfNodes: int
    amountOfNodes_limit: int
    DeploymentsWithAntiaffinity_length: int
    target_DeploymentsWithAntiaffinity_length: int
    amountOfPodsWithAntiaffinity: int
    target_amountOfPodsWithAntiaffinity: int

    target_amount_of_recomendations: int
    target_amount_of_recomendations_reached: bool


    is_node_disruption_searchable: bool
    is_daemonset_disrupted: bool
    is_daemonset_distuption_searchable: bool
    goal_achieved: bool
    block_node_outage_in_progress: bool
    block_policy_calculated : bool
    nodeSelectorsEnabled: bool
    deploymentsWithAntiaffinityBalanced: bool
    maxNumberOfPodsOnSameNodeForDeployment: int
    DeploymentsWithAntiaffinity: Set["mdeployment.Deployment"]
    DeploymentsWithAntiaffinity_length: int
    NodesDrained: Set["mnode.Node"]
    NodesDrained_length: int
    calc_NodesDrained: Set["mnode.Node"]
    calc_NodesDrained_length: int

    target_NodesDrained_length: int
    target_NodesDrained_length_reached: bool
    found_amount_of_recomendations: int
    pod_movement_is_in_progress_flag: bool
    # toNodes_are_checked: bool
    # current_pod: "Pod"
    # pods_toNode_cleared: bool
    # pods_toNode_checked: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_service_disrupted = False
        self.is_deployment_disrupted = False
        self.is_daemonset_disrupted = False
        self.is_node_disrupted = False
        self.goal_achieved = False
        self.is_deployment_distuption_searchable = True
        self.is_service_disruption_searchable = True
        self.is_node_disruption_searchable = True
        self.is_daemonset_distuption_searchable = True
        self.amountOfNodesDisrupted = 0
        self.block_node_outage_in_progress = False
        self.block_policy_calculated = False
        self.antiaffinity_prefered_policy_met = False
        self.nodeSelectorsEnabled = False
        self.amountOfNodes = 0
        self.amountOfNodes_limit = 0
        self.DeploymentsWithAntiaffinity_length = 0
        self.target_DeploymentsWithAntiaffinity_length = 1
        self.amountOfPodsWithAntiaffinity = 0
        self.target_amountOfPodsWithAntiaffinity = 5
        self.deploymentsWithAntiaffinityBalanced = False
        self.maxNumberOfPodsOnSameNodeForDeployment = 10
        self.NodesDrained_length = 0
        self.target_NodesDrained_length = 0
        self.target_NodesDrained_length_reached = False
        self.target_amount_of_recomendations = 0
        self.target_amount_of_recomendations_reached = False
        self.found_amount_of_recomendations = 0
        self.pod_movement_is_in_progress_flag = False
        # self.toNodes_are_checked = False
        # self.pods_toNode_cleared = False
        # self.pods_toNode_checked = False
        self.calc_NodesDrained_length = 0
        
    def __str__(self): return str(self._get_value())