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
from tests.test_scenarios_synthetic import build_running_pod_with_d

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
    k._build_state()
    genClass = type("gen_test_{0}_{1}".format(node_capacity, pod_amount),(CheckNodeOutage))
    p = genClass(k.state_objects)
    return k, p

def test_gen_1():
    assert_brake = False
    for node_cap in range(24,50):
        for pod_amount in range(10,50):
            try:
                k, p = prepare_test(1,node_cap,pod_amount,1)
            except Exception as e:
                print("prepare break node cap ", node_cap, " pod amount " ,pod_amount, "exception is \n",e)
                break
            assert_conditions = ["MarkServiceOutageEvent", "Mark_node_outage_event"]
            not_assert_conditions = []
            try:
                assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions, "test_{0}_{1}".format(node_cap, pod_amount), 0)
            except Exception as e:
                print("check break node ", node_cap, " cap " ,pod_amount, "exception is \n",e)
                break
            if assert_brake:
                break
    assert False