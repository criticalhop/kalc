from tests.test_util import print_objects
from tests.libs_for_tests import prepare_yamllist_for_diff
from guardctl.model.search import HypothesisysNode, OptimisticRun, HypothesisysNodeAndService
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.DaemonSet import DaemonSet
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.misc.const import *
import pytest
import inspect
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from guardctl.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from typing import Set

DEBUG_MODE = 2 # 0 - no debug,  1- debug with yaml load , 2 - debug without yaml load

def build_running_pod(podName, cpuRequest, memRequest, atNode):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = cpuRequest
    pod_running_1.memRequest = memRequest
    pod_running_1.atNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    pod_running_1.hasDeployment = False
    pod_running_1.hasService = False
    pod_running_1.hasDaemonset = False
    return pod_running_1

def build_running_pod_with_d(podName, cpuRequest, memRequest, atNode, d, ds):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = cpuRequest
    pod_running_1.memRequest = memRequest
    pod_running_1.atNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    pod_running_1.hasDeployment = False
    pod_running_1.hasService = False
    pod_running_1.hasDaemonset = False
    if d is not None:
        d.podList.add(pod_running_1)
        d.amountOfActivePods += 1
        pod_running_1.hasDeployment = True
    if ds is not None:
        ds.podList.add(pod_running_1)
        ds.amountOfActivePods += 1
        pod_running_1.hasDaemonset = True
    atNode.currentFormalCpuConsumption += cpuRequest
    atNode.currentFormalMemConsumption += memRequest
    return pod_running_1

 


def build_pending_pod(podName, cpuRequest, memRequest, toNode):
    p = build_running_pod(podName, cpuRequest, memRequest, Node.NODE_NULL)
    p.status = STATUS_POD["Pending"]
    p.toNode = toNode
    p.hasDeployment = False
    p.hasService = False
    p.hasDaemonset = False
    return p

def build_pending_pod_with_d(podName, cpuRequest, memRequest, toNode, d, ds):
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
    return p

class StateSet():
    scheduler: Scheduler
    globalVar: GlobalVar
    nodes: []
    pods: []
    services: []





def prepare_many_pods_without_yaml(nodes_amount,node_capacity,pod2_amount,pod0_amount,pod2_2_amount,pod3_amount):
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    
    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 0

    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    pod_id = 0
    for i in range(nodes_amount):
        node_item = Node("node"+str(i))
        node_item.metadata_name = "node"+str(i)
        node_item.cpuCapacity = node_capacity
        node_item.memCapacity = node_capacity
        node_item.isNull = False
        node_item.status = STATUS_NODE["Active"]
        nodes.append(node_item)
        
        for j in range(pod2_amount):
            pod_running_2 = build_running_pod_with_d(pod_id,2,2,node_item,None,None)
            pod_id += 1
            pod_running_2.hasService = True
            pods.append(pod_running_2)
            node_item.amountOfActivePods += 1
            s.podList.add(pod_running_2)
            s.amountOfActivePods += 1
            s.status = STATUS_SERV["Started"]

        for j in range(pod0_amount):
            pod_running_0 = build_running_pod_with_d(pod_id,0,0,node_item,None,None)
            pod_id += 1
            pods.append(pod_running_0)
            node_item.amountOfActivePods += 1

        for j in range(pod2_2_amount):
            pod_running_2 = build_running_pod_with_d(pod_id,2,2,node_item,None,None)
            pod_id += 1
            pod_running_2.hasService = True
            pods.append(pod_running_2)
            node_item.amountOfActivePods += 1
            s2.podList.add(pod_running_2)
            s2.amountOfActivePods += 1
            s2.status = STATUS_SERV["Started"]

    for j in range(pod3_amount):
        pod_running_2 = build_running_pod_with_d(pod_id,2,2,nodes[0],None,None)
        pod_id += 1
        pod_running_2.hasService = True
        pods.append(pod_running_2)
        nodes[0].amountOfActivePods += 1
        s2.podList.add(pod_running_2)
        s2.amountOfActivePods +=1
    
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class HypothesisysNodeAndService_k1(HypothesisysNodeAndService):
        pass
    p = HypothesisysNodeAndService_k1(k.state_objects)
    HypothesisysNodeAndService_k1.__name__ = inspect.stack()[0].function
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s,s2]
    test_case.services = services
    return k, p, test_case


# @pytest.mark.skip(reason="working. testing another case")    
def test_1_3pods_Service_outage():
    k, p, test_case = prepare_many_pods_without_yaml(2,4,1,0,0,1)
    assert_conditions = ["Remove_pod_from_the_cluster_IF_service_isnotnull_IF_is_last_for_service",\
                        "SchedulerCleaned"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
# @pytest.mark.skip(reason="working. testing another case")    
def test_2_3pods_NO_Service_outage():
    k, p, test_case = prepare_many_pods_without_yaml(2,6,1,0,0,1)
    assert_conditions = ["Remove_pod_from_the_cluster_IF_service_isnotnull_IF_is_last_for_service",\
                "SchedulerCleaned"]
    not_assert_conditions = ["Service_outage_hypothesis",\
                        "Remove_pod_from_the_queue"]
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
    print_objects(k.state_objects)

def test_3_3pods_NO_Service_outage():
    k, p, test_case = prepare_many_pods_without_yaml(2,7,1,0,0,1)
    assert_conditions = ["StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull",\
                "SchedulerCleaned"]
    not_assert_conditions = ["Service_outage_hypothesis",\
                        "Remove_pod_from_the_queue"]
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_4_3pods_NONO_Service_outage():
    k, p, test_case = prepare_many_pods_without_yaml(2,20,1,0,0,1)
    assert_conditions = ["StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull",\
                "SchedulerCleaned"]
    not_assert_conditions = ["Service_outage_hypothesis",\
                        "Remove_pod_from_the_queue"]
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_5_11pods():
    nodes_amount=2
    nodes_capacity=14
    pods_running_on_2_nodes_with_req_2_mem_2_cpu_s1 = 5
    pods_running_on_2_nodes_with_req_0_mem_0_cpu_s1 = 0
    pods_running_on_2_nodes_with_req_2_mem_2_cpu_s2 = 0
    pods_running_on_node0_with_req_2_mem_2_cpu_s2 = 1

    k, p, test_case = prepare_many_pods_without_yaml(nodes_amount,\
                                        nodes_capacity,pods_running_on_2_nodes_with_req_2_mem_2_cpu_s1,\
                                        pods_running_on_2_nodes_with_req_0_mem_0_cpu_s1,\
                                        pods_running_on_2_nodes_with_req_2_mem_2_cpu_s2,\
                                        pods_running_on_node0_with_req_2_mem_2_cpu_s2)
    assert_conditions = ["Service_outage_hypothesis",\
                        "Remove_pod_from_the_queue"]
    not_assert_conditions = []

    # ----  model test start ---- 
    # p.Initiate_node_outage(test_case.nodes[0], test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[0],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[1],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[2],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[3],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0], test_case.pods[4], test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0], test_case.pods[10], test_case.globalVar)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[0], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[1], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[2], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[3], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[4], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[10], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.NodeOutageFinished(test_case.nodes[0], test_case.globalVar)
    # p.SelectNode(test_case.pods[0], test_case.nodes[1], test_case.globalVar)
    # p.SelectNode(test_case.pods[1], test_case.nodes[1], test_case.globalVar)
    # p.StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.nodes[1], test_case.pods[0], test_case.scheduler, test_case.services[0])
    # p.StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.nodes[1], test_case.pods[1], test_case.scheduler, test_case.services[0])


    # ---- model test end ----- 

    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_6_11pods():
    nodes_amount=2
    nodes_capacity=14
    pods_running_on_2_nodes_with_req_2_mem_2_cpu_s1 = 5
    pods_running_on_2_nodes_with_req_0_mem_0_cpu_s1 = 0
    pods_running_on_2_nodes_with_req_2_mem_2_cpu_s2 = 0
    pods_running_on_node0_with_req_2_mem_2_cpu_s2 = 1

    k, p, test_case = prepare_many_pods_without_yaml(nodes_amount,\
                                        nodes_capacity,pods_running_on_2_nodes_with_req_2_mem_2_cpu_s1,\
                                        pods_running_on_2_nodes_with_req_0_mem_0_cpu_s1,\
                                        pods_running_on_2_nodes_with_req_2_mem_2_cpu_s2,\
                                        pods_running_on_node0_with_req_2_mem_2_cpu_s2)
    assert_conditions = ["Service_outage_hypothesis",\
                        "Remove_pod_from_the_queue"]
    not_assert_conditions = []

    # ----  model test start ---- 
    # p.Initiate_node_outage(test_case.nodes[0], test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[0],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[1],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[2],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0],test_case.pods[3],test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0], test_case.pods[4], test_case.globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(test_case.nodes[0], test_case.pods[10], test_case.globalVar)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[0], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[1], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[2], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[3], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[4], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.pods[10], test_case.nodes[0], test_case.services[0], test_case.scheduler)
    # p.NodeOutageFinished(test_case.nodes[0], test_case.globalVar)
    # p.SelectNode(test_case.pods[0], test_case.nodes[1], test_case.globalVar)
    # p.SelectNode(test_case.pods[1], test_case.nodes[1], test_case.globalVar)
    # p.StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.nodes[1], test_case.pods[0], test_case.scheduler, test_case.services[0])
    # p.StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(test_case.nodes[1], test_case.pods[1], test_case.scheduler, test_case.services[0])


    # ---- model test end ----- 

    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
