from kalc.misc.cli_optimize import optimize_cluster
import sys
sys.path.append('./tests/')
from test_util import print_objects
from libs_for_tests import prepare_yamllist_for_diff
from kalc.model.search import OptimisticRun, Optimize_directly
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
import pytest
import inspect
from kalc.model.search import *
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
from poodle import planned
from libs_for_tests import convert_space_to_yaml_dump,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
import kalc.misc.util
from typing import Set

DEBUG_MODE = 0 # 0 - no debug,  1- debug with yaml load , 2 - debug without yaml load
TEST_VU = "/home/vasily/CLIENT_DATA/test1"
TEST_DEMO = "./cluster_dump2"
TEST_CLUSTER_FOLDER = TEST_DEMO

def build_running_pod_with_d(podName, cpuRequest, memRequest, atNode, d, ds, s, pods):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = cpuRequest
    pod_running_1.memRequest = memRequest
    pod_running_1.cpuLimit = 1
    pod_running_1.memLimit = 1
    pod_running_1.atNode = atNode
    pod_running_1.toNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    pod_running_1.hasDeployment = False
    pod_running_1.hasService = False
    pod_running_1.hasDaemonset = False
    pod_running_1.searchable = True
    atNode.currentFormalCpuConsumption += cpuRequest
    atNode.currentFormalMemConsumption += memRequest
    atNode.amountOfActivePods += 1
    atNode.allocatedPodList.add(pod_running_1)
    atNode.allocatedPodList_length += 1
    atNode.directedPodList.add(pod_running_1)
    atNode.directedPodList_length += 1
    pod_running_1.toNode = Node.NODE_NULL

    
    pods.append(pod_running_1)
    if d is not None:
        d.podList.add(pod_running_1)
        d.amountOfActivePods += 1
        pod_running_1.hasDeployment = True
    if ds is not None:
        ds.podList.add(pod_running_1)
        ds.amountOfActivePods += 1
        pod_running_1.hasDaemonset = True
    if s is not None:
        pod_running_1.hasService = True
        s.podList.add(pod_running_1)
        s.amountOfActivePods += 1
        s.status = STATUS_SERV["Started"]
    return pod_running_1
 
def build_pending_pod_with_d(podName, cpuRequest, memRequest, toNode, d, ds, s):
    p = Pod()
    p.metadata_name = "pod"+str(podName)
    p.cpuRequest = cpuRequest
    p.memRequest = memRequest
    p.status = STATUS_POD["Pending"]
    p.hasDeployment = False
    p.hasService = False
    p.hasDaemonset = False
    if d is not None:
        d.podList.add(p)
        p.hasDeployment = True
    if ds is not None:
        ds.podList.add(p)
        p.hasDaemonset = True
        p.toNode = toNode
    if s is not None:
        p.hasService = True
        s.podList.add(p)
    return p

class StateSet():
    scheduler: Scheduler
    globalVar: GlobalVar
    nodes: []
    pods: []
    services: []
    deployments: []


def prepare_synthetic_data():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    globalVar.block_policy_calculated = False
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    services = []
    deployments = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.isSearched = True
    services.append(s1)

    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    services.append(s2)
    
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.searchable = True 
    d.spec_replicas = 6    
    d.NumberOfPodsOnSameNodeForDeployment = 4
    deployments.append(d)
    d2 = Deployment()
    d2.searchable = True
    d2.spec_replicas = 2    
    d2.NumberOfPodsOnSameNodeForDeployment = 2
    deployments.append(d2)
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 17
    node_item.memCapacity = 17
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(0,1,1,node_item,d,None,s1,pods)
    pod = build_running_pod_with_d(1,1,1,node_item,d,None,s1,pods)
    pod = build_running_pod_with_d(2,1,1,node_item,d,None,None,pods)
    pod = build_running_pod_with_d(3,1,1,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,1,1,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(5,1,1,node_item,None,None,s1,pods)


         
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(6,1,1,node_item,d2,None,s1,pods)
    pod = build_running_pod_with_d(7,1,1,node_item,d2,None,s1,pods)

    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(8,1,1,node_item,d,None,None,pods)

    node_item = Node()
    node_item.metadata_name = "node 4"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["New"]
    nodes.append(node_item)
    


    node_item = Node()
    node_item.metadata_name = "node 5"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["New"]
    nodes.append(node_item)
    


    node_item = Node()
    node_item.metadata_name = "node 6"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["New"]
    nodes.append(node_item)
    

    for node in nodes:
        globalVar.amountOfNodes += 1
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)

    pods[0].antiaffinity_set = True
    pods[0].podsMatchedByAntiaffinity.add(pods[1])
    pods[0].podsMatchedByAntiaffinity.add(pods[2])
    pods[0].podsMatchedByAntiaffinity.add(pods[8])
    pods[0].podsMatchedByAntiaffinity_length = 3
    pods[0].target_number_of_antiaffinity_pods = 3

    pods[1].antiaffinity_set = True
    pods[1].podsMatchedByAntiaffinity.add(pods[0])
    pods[1].podsMatchedByAntiaffinity.add(pods[2])
    pods[1].podsMatchedByAntiaffinity.add(pods[6])
    pods[1].podsMatchedByAntiaffinity_length = 3
    pods[1].target_number_of_antiaffinity_pods = 3

    pods[2].antiaffinity_set = True
    pods[2].podsMatchedByAntiaffinity.add(pods[1])
    pods[2].podsMatchedByAntiaffinity.add(pods[0])
    pods[2].podsMatchedByAntiaffinity.add(pods[8])
    pods[2].podsMatchedByAntiaffinity_length = 3
    pods[2].target_number_of_antiaffinity_pods = 3

    pods[8].antiaffinity_set = True
    pods[8].podsMatchedByAntiaffinity.add(pods[1])
    pods[8].podsMatchedByAntiaffinity.add(pods[2])
    pods[8].podsMatchedByAntiaffinity.add(pods[0])
    pods[8].podsMatchedByAntiaffinity_length = 3
    pods[8].target_number_of_antiaffinity_pods = 3

    pods[6].antiaffinity_set = True
    pods[6].podsMatchedByAntiaffinity.add(pods[7])
    pods[6].podsMatchedByAntiaffinity_length = 1
    pods[6].target_number_of_antiaffinity_pods = 1

    pods[7].antiaffinity_set = True
    pods[7].podsMatchedByAntiaffinity.add(pods[6])
    pods[7].podsMatchedByAntiaffinity_length = 1
    pods[7].target_number_of_antiaffinity_pods = 1
    
#     nodes[2].isSearched = True
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    k.state_objects.extend(deployments)
    create_objects = []
    k._build_state()

    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar.target_DeploymentsWithAntiaffinity_length = 1
    globalVar.maxNumberOfPodsOnSameNodeForDeployment = 10
    globalVar.target_amountOfPodsWithAntiaffinity = 3
    # globalVar.target_NodesDrained_length = 1
    globalVar.target_amount_of_recomendations = 1
    
    class Antiaffinity_check_k1(Optimize_directly):
        pass

    p = Antiaffinity_check_k1(k.state_objects)
    Antiaffinity_check_k1.__name__ = inspect.stack()[0].function
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    test_case.deployments = deployments
    print_objects(k.state_objects)
    return k, p, test_case


def test_synthetic_rebalance_3_pods():
    k, p, test_case = prepare_synthetic_data()

    assert_conditions = ["move_pod_recomendation_reason_antiaffinity",\
                     "reached_reqested_amount_of_recomendations"]
    not_assert_conditions = []
    
    # p.clear_node_of_pod(test_case.pods[0])
    # p.SelectNode(test_case.pods[0],test_case.nodes[1],test_case.globalVar)
    
    # p.check_toNode_for_pod_move_for_this_pod(test_case.pods[0],test_case.pods[1])
    # p.check_toNode_for_pod_move_for_this_pod(test_case.pods[0],test_case.pods[2])
    # p.check_toNode_for_pod_move_for_this_pod(test_case.pods[0],test_case.pods[8])

    # p.check_toNode_for_pod_move_for_other_pod_with_antiaffinity(test_case.pods[0],test_case.pods[6])
    # p.check_toNode_for_pod_move_for_other_pod_with_antiaffinity(test_case.pods[0],test_case.pods[7])

    # p.check_node_for_pod_move_finished(test_case.pods[0],test_case.nodes[1])

    # p.move_pod_recomendation_reason_antiaffinity(test_case.pods[0],test_case.pods[1],test_case.nodes[0],test_case.nodes[1],test_case.scheduler, test_case.globalVar,test_case.deployments[0])
    # p.clear_node_of_pod(test_case.pods[7])
    # p.SelectNode(test_case.pods[7],test_case.nodes[2],test_case.globalVar)
    # p.check_toNode_for_pod_move_for_this_pod(test_case.pods[7],test_case.pods[6])
    # p.check_toNode_for_pod_move_for_other_pod_with_antiaffinity(test_case.pods[7],test_case.pods[8])
    # p.check_node_for_pod_move_finished(test_case.pods[7],test_case.nodes[2])
    # p.move_pod_recomendation_reason_antiaffinity(test_case.pods[7],test_case.pods[6],test_case.nodes[1],test_case.nodes[2],test_case.scheduler, test_case.globalVar,test_case.deployments[1])


    # p.reached_reqested_amount_of_recomendations(test_case.globalVar)
    

    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
    brake = False
    if p.plan:
        for a in assert_conditions:
            if not a in "\n".join([repr(x) for x in p.plan]):
                brake = True
        for a in not_assert_conditions:
            if a in "\n".join([repr(x) for x in p.plan]):
                brake = True
    if not p.plan:
        brake = True
    assert brake == False
    # if p.plan:
    #     for a in p.plan:
    #         print(a)
    # else:
    #     print('No solution')

######################
#### next test works , but for test one need to have folder with yamls of demo cluster  in variable TEST_CLUSTER_FOLDER ####
#####################
# def test_cluster_dump_rebalance_2_pods():
#     k = KubernetesCluster()
#     k.load_dir(TEST_CLUSTER_FOLDER)
#     k._build_state()
#     globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
#     globalVar.target_amount_of_recomendations = 2
#     class NewGoal(Optimize_directly):
#         pass
#     p = NewGoal(k.state_objects)
#     # print_objects(k.state_objects)
#     p.run(timeout=9000)
#     assert_conditions = ["move_pod_recomendation_reason_antiaffinity",\
#                      "check_node_for_pod_move_finished"]
#     not_assert_conditions = []
#     brake = False
#     if p.plan:
#         for a in assert_conditions:
#             if not a in "\n".join([repr(x) for x in p.plan]):
#                 brake = True
#         for a in not_assert_conditions:
#             if a in "\n".join([repr(x) for x in p.plan]):
#                 brake = True
#     if not p.plan:
#         brake = True
#     assert brake == False
