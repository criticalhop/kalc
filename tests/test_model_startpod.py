from tests.test_util import print_objects
from tests.libs_for_tests import prepare_yamllist_for_diff
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
from kalc.model.search import K8ServiceInterruptSearch
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
pass
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

@pytest.mark.skip(reason="FIXME")
def test_1_1pod_2nodes_Service_outage():
       # Initialize scheduler, globalvar
    k = KubernetesCluster()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
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
    pod_id = 1
    node_1 = Node("node 1")
    node_1.cpuCapacity = 4
    node_1.memCapacity = 4
    node_1.isNull = False
    node_1.status = STATUS_NODE["Active"]

    node_2 = Node("node 2")
    node_2.cpuCapacity = 4
    node_2.memCapacity = 4
    node_2.isNull = False
    node_2.status = STATUS_NODE["Active"]
    pod_running_1 = build_running_pod_with_d(pod_id,2,2,node_1,None,None)
    pod_running_1.hasService = True
    node_1.amountOfActivePods += 1
    s.podList.add(pod_running_1)
    s.amountOfActivePods += 1
    s.status = STATUS_SERV["Started"]

    # k.state_objects += [node_1,node_2,pod_running_1, s]
    k.state_objects += [node_1,node_2,pod_running_1, s, STATUS_POD["Pending"], STATUS_POD["Killing"], STATUS_POD["Running"]]
    create_objects = []
    k._build_state()

    class HypothesisysNode_k1(HypothesisysNode):
        pass

    p = HypothesisysNode_k1(k.state_objects)
    HypothesisysNode_k1.__name__ = inspect.stack()[0].function
    not_assert_conditions = []
    print_objects(k.state_objects)
    p.Initiate_node_outage(node_1,globalVar)
    # p.Initiate_killing_of_Pod_because_of_node_outage(node_1,pod_running_1,globalVar)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(pod_running_1,node_1,s,scheduler)
    # p.NodeOutageFinished(node_1,globalVar)
    # p.Mark_node_outage_event(node_1,globalVar)
    # p.SelectNode(pod_running_1,node_2,globalVar)
    # p.StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(pod_running_1,node_2,scheduler,s,globalVar)
    # p.SchedulerCleaneduler,globalVar)
    print("                       >> changed state <<  ")
    print_objects(k.state_objects)

    p.run()
    print ("                      >> after <<         ")
    print_objects(k.state_objects)
    print_plan(p)

# @pytest.mark.skip(reason="too early to test")  
@pytest.mark.skip(reason="FIXME")
def test_2_3pods_2nodes_Service_outage():
       # Initialize scheduler, globalvar
    k = KubernetesCluster()
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
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
    pod_id = 1
    node_1 = Node("node 1")
    node_1.cpuCapacity = 7
    node_1.memCapacity = 7
    node_1.isNull = False
    node_1.status = STATUS_NODE["Active"]

    node_2 = Node("node 2")
    node_2.cpuCapacity = 7
    node_2.memCapacity = 7
    node_2.isNull = False
    node_2.status = STATUS_NODE["Active"]

    pod_running_1 = build_running_pod_with_d(1,2,2,node_1,None,None)
    pod_running_1.hasService = True
    node_1.amountOfActivePods += 1
    s.podList.add(pod_running_1)
    s.amountOfActivePods += 1

    pod_running_2 = build_running_pod_with_d(2,2,2,node_2,None,None)
    pod_running_2.hasService = True
    node_2.amountOfActivePods += 1
    s.podList.add(pod_running_2)
    s.amountOfActivePods += 1

    pod_running_3 = build_running_pod_with_d(3,2,2,node_1,None,None)
    pod_running_3.hasService = True
    node_1.amountOfActivePods += 1
    s2.podList.add(pod_running_3)
    s2.amountOfActivePods += 1
   
    k.state_objects += [node_1,node_2,pod_running_1, s, STATUS_POD["Pending"], STATUS_POD["Killing"], STATUS_POD["Running"], Node.NODE_NULL]
    create_objects = []
    k._build_state()

    class test_2_3pods_2nodes_Service_outage(HypothesisysNode):
        pass

    p = test_2_3pods_2nodes_Service_outage(k.state_objects)
    not_assert_conditions = []
    print_objects(k.state_objects)
    p.Initiate_node_outage(node_2,globalVar)
    p.Initiate_killing_of_Pod_because_of_node_outage(node_2,pod_running_2,globalVar)
    # p.KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(pod_running_2,node_2,s,scheduler)
    # p.NodeOutageFinished(node_2,globalVar)
    # p.Mark_node_outage_event(node_1,globalVar)
    # p.SelectNode(pod_running_1,node_2,globalVar)
    # p.StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull(pod_running_1,node_2,scheduler,s,globalVar)
    # p.SchedulerCleaneduler,globalVar)
    print("                       >> changed state <<  ")
    print_objects(k.state_objects)

    p.run()
    print ("                      >> after <<         ")
    print_objects(k.state_objects)
    print_plan(p)