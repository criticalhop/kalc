from tests.test_util import print_objects
from tests.libs_for_tests import prepare_yamllist_for_diff
from guardctl.model.search import Check_services, Check_deployments, Check_daemonsets, OptimisticRun, CheckNodeOutage, Check_node_outage_and_service_restart
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
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from guardctl.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode

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


def prepare_test_29_many_pods_not_enough_capacity_for_service(nodes_amount,node_capacity,pod2_amount,pod0_amount,pod2_2_amount,pod3_amount):
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
            pod_running_2 = build_running_pod_with_d(pod_id,2,2,node_item,None,None)
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
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    class NewGoal_k1(CheckNodeOutage):
        pass
    p = NewGoal_k1(k.state_objects)
    class NewGoal_k2(CheckNodeOutage):
        pass
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    return k, k2, p , p2

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
            pod_running_2 = build_running_pod_with_d(pod_id,2,2,node_item,None,None)
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
    class NewGoal_k1(CheckNodeOutage):
        pass
    p = NewGoal_k1(k.state_objects)

    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    print_objects(k.state_objects)
    return k, p
def test_29():
    k, k2, p, p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,15,1,1,1,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_30():
        k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,19,2,2,1,1)
        assert_conditions = ["SchedulerQueueCleanHighCost",\
                            "Mark_node_outage_event"]
        not_assert_conditions = []
        assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_31():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,23,3,3,1,1)
            assert_conditions = ["SchedulerQueueCleanHighCost",\
                        "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_32():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,26,3,3,2,2)
            assert_conditions = ["MarkServiceOutageEvent",\
                    "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_33():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,32,4,4,4,4)
            assert_conditions = ["SchedulerQueueCleanHighCost",\
                "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_34():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,40,5,5,5,5)
            assert_conditions = ["SchedulerQueueCleanHighCost",\
                            "Mark_node_outage_event"]
            not_assert_conditions = []
            checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
    
def test_36():
    k, k2, p, p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,8,1,1,1,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_37():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,8,2,2,1,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_38():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,8,3,3,1,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_39():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,12,4,4,4,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_40():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,25,5,5,5,5)
    assert_conditions = ["MarkServiceOutageEvent",\
                    "Mark_node_outage_event"]
    not_assert_conditions = []
    checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,DEBUG_MODE)
  
def test_41():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,11,4,4,4,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_42():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,12,5,5,4,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_43():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,12,5,5,5,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_44():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,12,5,5,5,5)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_45():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,12,4,4,4,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_46():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,16,5,4,4,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_47():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,20,5,5,4,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_48():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,24,5,5,5,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_49():
    k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(1,10,5,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_50_7pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,15,3,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_51_11pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,19,5,0,0,1)
    assert_conditions = ["SchedulerQueueCleanHighCost",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_52_14pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,23,7,0,0,1)
    assert_conditions = ["SchedulerQueueCleanHighCost",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_53_17pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,26,8,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
            "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_54_25pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,32,12,0,0,1)
    assert_conditions = ["SchedulerQueueCleanHighCost",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_55_31pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,40,15,0,0,1)
    assert_conditions = ["SchedulerQueueCleanHighCost",\
                    "Mark_node_outage_event"]
    not_assert_conditions = []
    checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
    
def test_56_7pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,8,3,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_57_11pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,8,5,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_58_15pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,8,7,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_59_25pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,12,12,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_60_31pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,25,15,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                    "Mark_node_outage_event"]
    not_assert_conditions = []
    checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,DEBUG_MODE)
  
def test_61_28pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,11,12,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_62_32pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,12,14,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_63_34pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,12,15,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_64_35pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,12,15,0,0,5)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_65_28pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,12,12,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_66_30pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,16,13,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_67_32pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,20,14,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_68_34pods():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(2,24,15,0,0,4)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)



def test_69_7pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,8,3,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_70_11pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,8,5,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)

def test_71_15pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,8,7,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_72_25pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,12,12,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,"functional test", DEBUG_MODE)
def test_73_31pods_1node():
    k, p = prepare_test_29_many_pods_not_enough_capacity_for_service_without_yaml_loading(1,25,15,0,0,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                    "Mark_node_outage_event"]
    not_assert_conditions = []
    checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,DEBUG_MODE)
  