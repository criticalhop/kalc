from tests.test_util import print_objects
from tests.libs_for_tests import prepare_yamllist_for_diff
from kalc.model.search import HypothesisysNode, OptimisticRun
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
from kalc.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from typing import Set

DEBUG_MODE = 2 # 0 - no debug,  1- debug with yaml load , 2 - debug without yaml load


def build_running_pod_with_d(podName, cpuRequest, memRequest, atNode, d, ds, s, pods):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = cpuRequest
    pod_running_1.memRequest = memRequest
    pod_running_1.atNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    pod_running_1.hasDeployment = False
    pod_running_1.hasService = False
    pod_running_1.hasDaemonset = False
    atNode.currentFormalCpuConsumption += cpuRequest
    atNode.currentFormalMemConsumption += memRequest
    atNode.amountOfActivePods += 1
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


def test_1():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    services = []
    services.append(s1)
    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 10
    node_item.memCapacity = 10
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 10
    node_item.memCapacity = 10
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,None,pods)

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
    for node in nodes:
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_implement_k1(Antiaffinity_implement):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True


    p = Antiaffinity_implement_k1(k.state_objects)
    Antiaffinity_implement_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_2():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    services = []
    services.append(s1)
    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)


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

    for node in nodes:
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
        
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_implement_with_add_node_k1(Antiaffinity_implement_with_add_node):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True    

    p = Antiaffinity_implement_with_add_node_k1(k.state_objects)
    Antiaffinity_implement_with_add_node_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node",\
                        "Add_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)


def test_3():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []

    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    s1.targetAmountOfPodsOnDifferentNodes = 3
    s1.isSearched = True
    services = []
    services.append(s1)
    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)


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

    for node in nodes:
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
        
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_prefered_k1(Antiaffinity_prefered):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True     

    p = Antiaffinity_prefered_k1(k.state_objects)
    Antiaffinity_prefered_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node",\
                        "Add_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)


def test_4():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    s1.targetAmountOfPodsOnDifferentNodes = 4
    s1.isSearched = True
    services = []
    services.append(s1)
    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)


    node_item = Node()
    node_item.metadata_name = "node 4"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    node_item = Node()
    node_item.metadata_name = "node 5"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    node_item = Node()
    node_item.metadata_name = "node 6"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["New"]
    nodes.append(node_item)

    for node in nodes:
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
        
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_prefered_k1(Antiaffinity_prefered):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True      

    p = Antiaffinity_prefered_k1(k.state_objects)
    Antiaffinity_prefered_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node",\
                        "Add_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_5():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    services = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    s1.targetAmountOfPodsOnDifferentNodes = 4
    s1.isSearched = True
    services.append(s1)

    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    services.append(s2)
    
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)


    node_item = Node()
    node_item.metadata_name = "node 4"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    node_item = Node()
    node_item.metadata_name = "node 5"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    node_item = Node()
    node_item.metadata_name = "node 6"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["New"]
    nodes.append(node_item)

    for node in nodes:
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
        
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_prefered_k1(Antiaffinity_prefered):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True

    p = Antiaffinity_prefered_k1(k.state_objects)
    Antiaffinity_prefered_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node",\
                        "Add_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

    
def test_6_3nodes_but_needed4nodes_possible_to_add_2_nodes_suggests_this():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    services = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    s1.targetAmountOfPodsOnDifferentNodes = 4
    s1.isSearched = True
    services.append(s1)

    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    services.append(s2)
    
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)


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
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
        
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_prefered_k1(Antiaffinity_prefered_with_add_node):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True

    p = Antiaffinity_prefered_k1(k.state_objects)
    Antiaffinity_prefered_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node",\
                        "Add_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_7_3nodes_and_needed3nodes_suggests_movement_of_pods():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    i = 0
    j = 0
    nodes = []
    pods = []
    services = []
    
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.antiaffinity = True
    s1.targetAmountOfPodsOnDifferentNodes = 3
    s1.isSearched = True
    services.append(s1)

    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 0
    services.append(s2)
    
    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2    
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(1,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(2,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(3,2,2,node_item,None,None,None,pods)
    pod = build_running_pod_with_d(4,2,2,node_item,None,None,None,pods)
 
    node_item = Node()
    node_item.metadata_name = "node 2"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(5,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(6,2,2,node_item,None,None,s1,pods)
    pod = build_running_pod_with_d(7,2,2,node_item,None,None,s2,pods)
    pod = build_running_pod_with_d(8,2,2,node_item,None,None,s2,pods)
    
    node_item = Node()
    node_item.metadata_name = "node 3"
    node_item.cpuCapacity = 4
    node_item.memCapacity = 4
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    pod = build_running_pod_with_d(9,2,2,node_item,None,None,None,pods)


    node_item = Node()
    node_item.metadata_name = "node 4"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    node_item = Node()
    node_item.metadata_name = "node 5"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)

    node_item = Node()
    node_item.metadata_name = "node 6"
    node_item.cpuCapacity = 8
    node_item.memCapacity = 8
    node_item.isNull = False
    node_item.status = STATUS_NODE["New"]
    nodes.append(node_item)

    for node in nodes:
        for pod in pods:
            if not pod.nodeSelectorSet: pod.nodeSelectorList.add(node)
        for node2 in nodes:
            if node != node2:
                node2.different_than.add(node)
        
    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    k.state_objects.extend([pc, s1, s2 ])
    create_objects = []
    k._build_state()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    class Antiaffinity_prefered_with_add_node_k1(Antiaffinity_prefered_with_add_node):
        def goal(self):
            assert services[0].antiaffinity_prefered_policy_met == True

    p = Antiaffinity_prefered_with_add_node_k1(k.state_objects)
    Antiaffinity_prefered_with_add_node_k1.__name__ = inspect.stack()[0].function
    assert_conditions = ["manually_initiate_killing_of_podt",\
                        "Not_at_same_node",\
                        "Add_node"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    test_case = StateSet()
    test_case.scheduler = scheduler
    test_case.globalVar = globalVar
    test_case.pods = pods
    test_case.nodes = nodes
    services = [s1,s2]
    test_case.services = services
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
