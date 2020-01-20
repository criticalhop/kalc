from tests.test_util import print_objects
from tests.libs_for_tests import prepare_yamllist_for_diff
from kalc.model.search import Check_services, Check_deployments, Check_daemonsets, OptimisticRun, CheckNodeOutage, Check_node_outage_and_service_restart
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
from kalc.model.search import K8ServiceInterruptSearch
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
from kalc.model.scenario import Scenario
from poodle import planned
import inspect
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from tests.debugging import DebuggingCheckNodeOutage

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

def prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(nodes_amount,node_capacity,pod2_amount,pod0_amount,pod2_2_amount,pod3_amount):
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
    pod_id = 1

   
    for i in range(nodes_amount):
        node_item = Node("node"+str(i))
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
            s.amountOfActivePods +=1

        for j in range(pod0_amount):
            pod_running_0 = build_running_pod_with_d(pod_id,0,0,node_item,None,None)
            pod_id += 1
            pods.append(pod_running_0)
            node_item.amountOfActivePods += 1

    for j in range(pod2_2_amount):
        pod_running_2 = build_running_pod_with_d(pod_id,2,2,nodes[0],None,None)
        pod_id += 1
        pod_running_2.hasService = True
        pods.append(pod_running_2)
        node_item.amountOfActivePods += 1
        s.podList.add(pod_running_2)
        s.amountOfActivePods +=1

    for j in range(pod3_amount):
        pod_running_2 = build_running_pod_with_d(pod_id,2,2,nodes[0],None,None)
        pod_id += 1
        pod_running_2.hasService = True
        pods.append(pod_running_2)
        node_item.amountOfActivePods += 1
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
    class NewGoal_k1(DebuggingCheckNodeOutage):
        pass
    p = NewGoal_k1(k.state_objects)
    print_objects(k.state_objects)
    return k, p

def test_12pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,30,11,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    class NewGoal_k1(DebuggingCheckNodeOutage):
        goal = lambda self: globalVar_k1.is_node_disrupted == True
    NewGoal_k1.__name__ = "test_12pods_1node" #inspect.stack()[1].function
    p = NewGoal_k1(k.state_objects)
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_13pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,28,12,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    class NewGoal_k1(DebuggingCheckNodeOutage):
        goal = lambda self: globalVar_k1.is_node_disrupted == True
    NewGoal_k1.__name__ = "test_13pods_1node" #inspect.stack()[1].function
    p = NewGoal_k1(k.state_objects)
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_14pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,30,13,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    class NewGoal_k1(DebuggingCheckNodeOutage):
        goal = lambda self: globalVar_k1.is_node_disrupted == True
    NewGoal_k1.__name__ = "test_14pods_1node" #inspect.stack()[1].function
    p = NewGoal_k1(k.state_objects)
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_15pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,30,14,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    class NewGoal_k1(DebuggingCheckNodeOutage):
        goal = lambda self: globalVar_k1.is_node_disrupted == True
    NewGoal_k1.__name__ = "test_15pods_1node" #inspect.stack()[1].function
    p = NewGoal_k1(k.state_objects)
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_16pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,17,12,0,3,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    class NewGoal_k1(DebuggingCheckNodeOutage):
        goal = lambda self: globalVar_k1.is_node_disrupted == True
    NewGoal_k1.__name__ = "test_16pods_1node" #inspect.stack()[1].function
    p = NewGoal_k1(k.state_objects)
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_25pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,17,10,0,4,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    class NewGoal_k1(DebuggingCheckNodeOutage):
        goal = lambda self: globalVar_k1.is_node_disrupted == True
    NewGoal_k1.__name__ = "test_12pods_1node" #inspect.stack()[1].function
    p = NewGoal_k1(k.state_objects)
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
