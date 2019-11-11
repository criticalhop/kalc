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
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml
from tests.test_scenarios_synthetic import prepare_test_29_many_pods_not_enough_capacity_for_service, build_running_pod_with_d

DEBUG_MODE = 1

def prepare_test(nodes_amount,node_capacity,pod_amount,pod_w_service_amount):
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
        
        for j in range(pod_amount):
            pod_running_2 = build_running_pod_with_d(pod_id,1,1,node_item,None,None)
            pod_id += 1
            pod_running_2.hasService = True
            pods.append(pod_running_2)
            node_item.amountOfActivePods += 1
            s.podList.add(pod_running_2)
            s.amountOfActivePods +=1

    for j in range(pod_w_service_amount):
        pod_running_2 = build_running_pod_with_d(pod_id,1,1,nodes[0],None,None)
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

def test_gen_1():
    for node in range(24,24):
        for cap in range(10,20):
            try:
                k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(1,node,cap,0,0,1)
            except Exception as e:
                print("prepare break node ", node, " cap " ,cap, "exception is \n",e)
                break
            assert_conditions = ["MarkServiceOutageEvent", "Mark_node_outage_event"]
            not_assert_conditions = []
            try:
                assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
            except Exception as e:
                print("check break node ", node, " cap " ,cap, "exception is \n",e)
                break
    assert True