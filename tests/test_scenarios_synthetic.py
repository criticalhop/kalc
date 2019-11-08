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

def prepare_test_0_run_pods_no_eviction():
    # print("0")
    # TODO: extract final status for loader unit tests from here
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    n.currentFormalCpuConsumption = 0
    n.currentFormalMemConsumption = 0

    # priority - as needed
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Pedning pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    # Create a "holding" controller - optional
    ds = DaemonSet()
    ds.podList.add(pod_pending_1)
    ds.amountOfActivePods = 0
    pod_pending_1.hasDaemonset = True
    k.state_objects.extend([n, pc, ds])
    create_objects = [pod_pending_1]
    k2 = reload_cluster_from_yaml(k,create_objects)
    k.state_objects.extend(create_objects)
    k._build_state()
    return k, k2

@pytest.mark.debug(reason="this test is for debug perspective")
def test_0_run_pods_no_eviction():
    k, k2 = prepare_test_0_run_pods_no_eviction()
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))

    class Task_Check_services(Check_services):
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    class Task_Check_deployments(Check_deployments):
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = Task_Check_services(k.state_objects)
    p.run(timeout=200)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    p = Task_Check_deployments(k.state_objects)
    p.run(timeout=200)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])

def test_0_run_pods_no_eviction_invload():
    k, k2 = prepare_test_0_run_pods_no_eviction()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))


    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    class NewGoal_k1(Check_services):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    class NewGoal_k2(Check_services):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)

    assert_conditions = ["StartPod"]
    not_assert_conditions = ["Evict"]
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def construct_scpace_for_test_1_run_pods_with_eviction():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]
    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1])
    k._build_state()
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    return k, k2

def test_1_run_pods_with_eviction_invload():
    k, k2 = construct_scpace_for_test_1_run_pods_with_eviction()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))


    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    class NewGoal_k1(Check_services):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    class NewGoal_k2(Check_services):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)

    assert_conditions = ["StartPod","Evict"]
    not_assert_conditions = ["NodeOutageFinished"]
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def construct_scpace_for_test_2_synthetic_service_outage():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False
    n.searchable = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)
    n.amountOfActivePods = 2

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 1
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    s.podList.add(pod_running_1)
    pod_running_1.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1,s])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    return k, k2

@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step1():
    # print("2-1")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    class NewGoal(OptimisticRun):
        # pass
        # goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
        goal = lambda self: pod_running_1.status == STATUS_POD["Killing"]
    p = NewGoal(k.state_objects)
    
    p.run(timeout=200)
    # for a in p.plan:
    #     print(a)
    # print_objects(k.state_objects)
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan])

@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step2():
    # print("2-2")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    # print_objects(k.state_objects)
    class NewGoal(OptimisticRun):
        # pass
        # goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
        goal = lambda self: pod_running_1.status == STATUS_POD["Pending"]
    p = NewGoal(k.state_objects)
    p.run(timeout=200)
    # for a in p.plan:
    #     print(a)
    # print_objects(k.state_objects)
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert "KillPod" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan])

@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step3():
    # print("2-3")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    # print_objects(k.state_objects)
    class NewGoal(OptimisticRun):
        # pass
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"] and\
                            pod_running_1.status == STATUS_POD["Pending"]
    p = NewGoal(k.state_objects)
    p.run(timeout=200)
    # for a in p.plan:
    #     print(a)
    # print_objects(k.state_objects)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan])

@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step4():
    # print("2-4")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))

    # print_objects(k.state_objects)
    class NewGoal(OptimisticRun):
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"] and\
                            pod_running_1.status == STATUS_POD["Pending"] and\
                            scheduler.queueLength  == 1
    p = NewGoal(k.state_objects)
    p.run(timeout=400)
    # for a in p.plan:
    #     print(a)
    # print_objects(k.state_objects)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan])

@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step5():
    # print("2-5")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # print_objects(k.state_objects)
    class NewGoal(OptimisticRun):
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"] and\
                            pod_running_1.status == STATUS_POD["Pending"] and\
                            scheduler.status == STATUS_SCHED["Clean"]
    p = NewGoal(k.state_objects)
    p.run(timeout=400)
    # for a in p.plan:
    #     print(a)
    # print_objects(k.state_objects)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan])
    # assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])

#TODO PASS wioth Scheduler_cant_place_pod cost=30000
@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step6_noNodeSelected():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False
    n.searchable = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)
    n.amountOfActivePods = 2

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 1
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    s.podList.add(pod_running_1)
    pod_running_1.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,Node.NODE_NULL)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1,s])
    "this test was needed when debugging invloads"
    # print("2-6")

    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    # print_objects(k.state_objects)
    class test_2_synthetic_service_outage_step6_noNodeSelected_Task_Check_services(Check_services):
        goal = lambda self: globalVar.is_service_disrupted == True
    p = test_2_synthetic_service_outage_step6_noNodeSelected_Task_Check_services(k.state_objects)
    p.run(timeout=200)
    # print_plan(p)
    assert "SelectNode" in "\n".join([repr(x) for x in p.plan]) # StartPod not necessarily happens
    assert "StartPod" in "\n".join([repr(x) for x in p.plan]) # StartPod not necessarily happens
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan]) 



@pytest.mark.debug(reason="if debug needed - uncomment me")
def test_2_synthetic_service_outage_step6():
    # print("2-6")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))

    # print_objects(k.state_objects)
    class Task_Check_services(Check_services):
        goal = lambda self: globalVar.is_service_disrupted == True
    class Task_Check_daemonsets(Check_daemonsets):
        goal = lambda self: globalVar.is_daemonset_disrupted == True
    p = Task_Check_services(k.state_objects)
    p.run(timeout=200)
    # print_plan(p)
    # assert "StartPod" in "\n".join([repr(x) for x in p.plan]) # StartPod not necessarily happens
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan]) 

def test_2_synthetic_service_outage_invload():
    # print("2-6")
    k, k2 =construct_scpace_for_test_2_synthetic_service_outage()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects))
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    node_1 = next(filter(lambda x: isinstance(x, Node), k.state_objects))
    node_1.searchable = False
    node_2 = next(filter(lambda x: isinstance(x, Node), k2.state_objects))
    node_2.searchable = False

    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    class NewGoal_k1(Check_services):
        goal = lambda self: globalVar_k1.is_service_disrupted == True
    p = NewGoal_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    class NewGoal_k2(Check_services):
        goal = lambda self: globalVar_k2.is_service_disrupted == True
    p2 = NewGoal_k2(k2.state_objects)

    assert_conditions = [
        # "StartPod",
        "Evict","MarkServiceOutageEvent"]
    not_assert_conditions = ["NodeOutageFinished"]
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def construct_multi_pods_eviction_problem():
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4
    n.amountOfActivePods = 2
    n.searchable = False

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    # TODO: no outage detected if res is not 4
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_2)

    pod_running_1.hasService = True
    pod_running_2.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,4,4,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1,s])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    # print_objects(k.state_objects)
    k._build_state()
    return k, k2, pod_pending_1

def test_3_synthetic_service_outage_multi_invload():
    # print("3")
    "Multiple pods are evicted from one service to cause outage"
    k, k2, pod_pending_1 = construct_multi_pods_eviction_problem()
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    node_k1 = next(filter(lambda x: isinstance(x, Node), k.state_objects))
    node_k2 = next(filter(lambda x: isinstance(x, Node), k2.state_objects))
    node_k1.searchable = False
    node_k2.searchable = False

    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    class NewGoal_k1(Check_services):
        goal = lambda self: globalVar_k1.is_service_disrupted == True
    p = NewGoal_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    class NewGoal_k2(Check_services):
        goal = lambda self: globalVar_k2.is_service_disrupted == True
    p2 = NewGoal_k2(k2.state_objects)

    assert_conditions = ["MarkServiceOutageEvent"]
    not_assert_conditions = []
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def prepare_test_4_synthetic_service_NO_outage_multi():
    # print("4")
    "No outage is caused by evicting only one pod of a multi-pod service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    # TODO: no outage detected if res is not 4
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_2)

    pod_running_1.hasService = True
    pod_running_2.hasService = True
    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]
    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1,s])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    return k,k2

def test_4_synthetic_service_NO_outage_multi():
    k, k2 = prepare_test_4_synthetic_service_NO_outage_multi()
   
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    class NewGoal_k1(Check_services):
        goal = lambda self: globalVar_k1.goal_achieved == True
    p = NewGoal_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    class NewGoal_k2(Check_services):
        goal = lambda self: globalVar_k2.goal_achieved == True
    p2 = NewGoal_k2(k2.state_objects)

    assert_conditions = ["SchedulerQueueClean"]
    not_assert_conditions = []
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

@pytest.mark.debug()
def test_synthetic_service_NO_outage_deployment_IS_outage_step_1():
    "Deployment (partial) outage must be registered in case where Deployment exists"
    # Initialize scheduler, globalvar
    # guardctl.misc.util.CPU_DIVISOR=40
    # guardctl.misc.util.MEM_DIVISOR=125
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    # TODO: no outage detected if res is not 4
    pod_running_1.targetService = s
    pod_running_2.targetService = s

    pod_running_1.hasService = True
    pod_running_2.hasService = True
    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    d = Deployment()
    d.spec_replicas = 2
    d.amountOfActivePods = 2
    pod_running_1.hasDeployment = True
    pod_running_2.hasDeployment = True
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)
    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1,s,d])
    # guardctl.misc.util.CPU_DIVISOR=40
    # guardctl.misc.util.MEM_DIVISOR=125
    yamlState = convert_space_to_yaml(k.state_objects, wrap_items=True)
    k2 = KubernetesCluster()
    load_yaml(yamlState,k2)
    k._build_state()
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
 
    class test_synthetic_service_NO_outage_deployment_IS_outage_k1(Check_deployments):
        goal = lambda self: pod_running_1.status == STATUS_POD["Pending"]
    p = test_synthetic_service_NO_outage_deployment_IS_outage_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))

    pods = filter(lambda x: isinstance(x, Pod), k2.state_objects)
    pod_k2 = next(filter(lambda x: x.metadata_name._get_value() == "pod1", pods))

    class test_synthetic_service_NO_outage_deployment_IS_outage_k2(Check_deployments):
        goal = lambda self: pod_k2.status == STATUS_POD["Pending"]

    p2 = test_synthetic_service_NO_outage_deployment_IS_outage_k2(k2.state_objects)

    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined"]
    not_assert_conditions = []
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
    
def test_synthetic_service_NO_outage_deployment_IS_outage():
    "Deployment (partial) outage must be registered in case where Deployment exists"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    # TODO: no outage detected if res is not 4
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_2)

    pod_running_1.hasService = True
    pod_running_2.hasService = True
    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    d = Deployment()
    d.spec_replicas = 2
    d.amountOfActivePods = 2
    pod_running_1.hasDeployment = True
    pod_running_2.hasDeployment = True
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)
    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1,s,d])

    yamlState = convert_space_to_yaml(k.state_objects, wrap_items=True)
    k2 = KubernetesCluster()
    load_yaml(yamlState,k2)
    k._build_state()
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    class NewGoal_k1(Check_deployments):
        goal = lambda self: globalVar_k1.is_deployment_disrupted == True
    p = NewGoal_k1(k.state_objects)

    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    class NewGoal_k2(Check_deployments):
        goal = lambda self: globalVar_k2.is_deployment_disrupted == True
    p2 = NewGoal_k2(k2.state_objects)

    assert_conditions = ["MarkDeploymentOutageEvent"]
    not_assert_conditions = []
    
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_5_evict_and_killpod_deployment_without_service():
    # print("5")
    "Test that killPod works for deployment"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,d,None)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,d,None)
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]
    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, s, pod_pending_1, d])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_running_1_1.status == STATUS_POD["Pending"]
    p = NewGoal_k1(k.state_objects)

    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_running_1_2.status == STATUS_POD["Pending"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined",\
                        "KillPod_IF_Deployment_isNotNUll_Service_isNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_6_evict_and_killpod_without_deployment_without_service():
    # print("6")
    "Test that killPod works without either deployment or service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # create Deploymnent that we're going to detect failure of...
    # d = Deployment()
    # d.spec_replicas = 2

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,None)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,None,None)

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2


    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, s, pod_pending_1])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_running_1_1.status == STATUS_POD["Pending"]
    p = NewGoal_k1(k.state_objects)

    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_running_1_2.status == STATUS_POD["Pending"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined",\
                        "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)


# @pytest.mark.skip(reason="FIXME")
def test_7_evict_and_killpod_with_deployment_and_service():
    # print("7")
    "Test that killPod works for deployment with service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,d,None)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,d,None)
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    s.podList.add(pod_running_1)
    pod_running_1.hasService = True
    s.podList.add(pod_running_2)
    pod_running_2.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, s, pod_pending_1, d])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_running_1_1.status == STATUS_POD["Pending"]
    p = NewGoal_k1(k.state_objects)

    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_running_1_2.status == STATUS_POD["Pending"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined",\
                        "KillPod_IF_Deployment_isNotNUll_Service_isNotNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_8_evict_and_killpod_with_daemonset_without_service():
    # print("8")
    "Test that killPod works with daemonset"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # create Deploymnent that we're going to detect failure of...
    ds = DaemonSet()

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,ds)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,None,ds)
    n.amountOfActivePods = 2


    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    # s.amountOfActivePods = 2
    # s.status = STATUS_SERV["Started"]



    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, s, pod_pending_1,ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_running_1_1.status == STATUS_POD["Pending"]
    p = NewGoal_k1(k.state_objects)

    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_running_1_2.status == STATUS_POD["Pending"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined",\
                        "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
    
def test_9_evict_and_killpod_with_daemonset_with_service():
    # print("9")
    "Test that killPod works with daemonset and service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # create Deploymnent that we're going to detect failure of...
    ds = DaemonSet()

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,ds)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,None,ds)
    n.amountOfActivePods = 2

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    s.podList.add(pod_running_1)
    pod_running_1.hasService = True
    s.podList.add(pod_running_2)
    pod_running_2.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, s, pod_pending_1,ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_running_1_1.status == STATUS_POD["Pending"]
    p = NewGoal_k1(k.state_objects)

    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_running_1_2.status == STATUS_POD["Pending"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined",\
                        "KillPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNotNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_10_startpod_without_deployment_without_service():
    # print("10")
    "Test that StartPod works without daemonset/deployment and service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
 
    ds = DaemonSet()

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,ds)
    n.amountOfActivePods = 1

    # Service  
    s = Service()

    s.podList.add(pod_running_1)
    pod_running_1.hasService = True


    # Pending pod
    pod_pending_1 = build_pending_pod_with_d(3,2,2,n,None,None)

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pod_running_1, s, pod_pending_1,ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["SelectNode",\
                        "StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_11_startpod_without_deployment_with_service():
    # print("11")
    "Test that StartPod works without daemonset/deployment but with service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
 
    ds = DaemonSet()

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,ds)
    n.amountOfActivePods = 1
    # Pending pod
    pod_pending_1 = build_pending_pod_with_d(3,2,2,n,None,None)
    
    # Service  
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 0
    s.status = STATUS_SERV["Pending"]
 
    s.podList.add(pod_pending_1)
    pod_pending_1.hasService = True

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pod_running_1, s, pod_pending_1,ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["SelectNode",\
                        "StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_12_startpod_with_deployment_with_service():
    # print("12")
    "Test that StartPod works with deployment and service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
 
    d = Deployment()
    d.spec_replicas = 2

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,d,None)
    n.amountOfActivePods = 1
    # Pending pod
    pod_pending_1 = build_pending_pod_with_d(3,2,2,n,d,None)
    
    # Service  
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 0
    s.status = STATUS_SERV["Pending"]
 
    s.podList.add(pod_running_1)
    pod_running_1.hasService = True
    s.podList.add(pod_pending_1)
    pod_pending_1.hasService = True

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pod_running_1, s, pod_pending_1,d])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["SelectNode",\
                        "StartPod_IF_Deployment_isNotNUll_Service_isNotNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_13_startpod_with_daemonset_without_service():
    # print("13")
    "Test that StartPod works with daemonset and without service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
 
    d = DaemonSet()

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,d)
    n.amountOfActivePods = 1
    # Pending pod
    pod_pending_1 = build_pending_pod_with_d(3,2,2,n,None,d)
    
    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pod_running_1, pod_pending_1,d])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_14_startpod_with_daemonset_with_service():
    # print("14")
    "Test that StartPod works with daemonset and service"
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
 
    d = DaemonSet()

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,None,d)
    n.amountOfActivePods = 1
    # Pending pod
    pod_pending_1 = build_pending_pod_with_d(3,2,2,n,None,d)
    
    # Service  
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 0
    s.status = STATUS_SERV["Pending"]
 
    s.podList.add(pod_pending_1)
    pod_running_1.hasService = True
    s.podList.add(pod_pending_1)
    pod_pending_1.hasService = True

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pod_running_1, s, pod_pending_1,d])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_pending_1_1.status == STATUS_POD["Running"]
    p = NewGoal_k1(k.state_objects)

    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_pending_1_2.status == STATUS_POD["Running"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["StartPod_IF_Deployment_isNUll_Service_isNotNull_Daemonset_isNotNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

# @pytest.mark.skip(reason="FIXME")
def test_15_has_deployment_creates_daemonset__pods_evicted_pods_pending_synthetic():
    # print("15")
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,d,None)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,d,None)
    n.amountOfActivePods = 2


    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # Create Daemonset for prioritized pod 
    ds = DaemonSet()

    # Pending pod
    pod_pending_1 = build_pending_pod_with_d(3,2,2,n,None,ds)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1, d,s,ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    print_objects(k.state_objects)

    print_objects_from_yaml(k)
    print("----")
    print_objects(k2.state_objects)
    print_objects_from_yaml(k2)
    globalVar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects))
    # class NewGoal_step1_k1(Check_deployments):
    #     goal = lambda self: globalVar_k1.goal_achieved == True and\
    #          pod_pending_1_1.status == STATUS_POD["Running"]

    class NewGoal_k1(Check_deployments):
        pass

    p = NewGoal_k1(k.state_objects)
    globalVar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))
    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(Check_deployments):
        pass
    # class NewGoal_step1_k2(Check_deployments):
    #     goal = lambda self: globalVar_k2.goal_achieved == True  and\
    #          pod_pending_1_2.status == STATUS_POD["Running"]

    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict",
                        "MarkDeploymentOutageEvent"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_16_creates_deployment_but_insufficient_resource__pods_pending_synthetic():
    # print("16")
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))

    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)
    n.amountOfActivePods = 2

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)
    d.amountOfActivePods = 2
    d.spec_replicas = 2

    dnew = Deployment()
    dnew.podList.add(pod_pending_1)
    dnew.amountOfActivePods = 0
    dnew.spec_replicas = 1

    k.state_objects.extend([n, pod_running_1, pod_running_2, d])
    create_objects = [dnew]
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    # pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    
    class NewGoal_k1(Check_deployments):
        pass

    p = NewGoal_k1(k.state_objects)
    class NewGoal_k2(Check_deployments):
        pass

    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["MarkDeploymentOutageEvent"]
    not_assert_conditions = ["NodeOutageFinished"]

    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
    

def test_17_creates_service_and_deployment_insufficient_resource__service_outage():
    # print("17")
    # Initialize scheduler, globalVar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.searchable = False

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)
    n.amountOfActivePods = 2

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

    # priority for pod-to-evict
    # pc = PriorityClass()
    # pc.priority = 10
    # pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]
    s.searchable = True

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_1)
    pod_running_1.hasService = True
    pod_running_2.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    # pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)
    d.amountOfActivePods = 2
    d.spec_replicas = 2
    pod_running_1.hasDeployment = True
    pod_running_2.hasDeployment = True

    dnew = Deployment()
    dnew.podList.add(pod_pending_1)
    dnew.amountOfActivePods = 0
    dnew.spec_replicas = 1
    pod_pending_1.hasDeployment = True

    snew = Service()
    snew.metadata_name = "test-service-new"
    snew.amountOfActivePods = 0
    snew.status = STATUS_SERV["Pending"]
    snew.podList.add(pod_pending_1)
    pod_pending_1.hasService = True
    snew.searchable = True

    k.state_objects.extend([n, s, pod_running_1, pod_running_2, d])
    create_objects = [snew,dnew]
    k2 = reload_cluster_from_yaml(k,create_objects)
    k.state_objects.extend(create_objects)
    k.state_objects.extend([pod_pending_1])

    k._build_state()
    k2._build_state()
    n_k2 = next(filter(lambda x: isinstance(x, Node), k2.state_objects))
    n_k2.searchable = False
    k._build_state()
    class NewGoal_k1(Check_services):
        pass
    p = NewGoal_k1(k.state_objects)

    class NewGoal_k2(Check_services):
        pass
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["MarkServiceOutageEvent"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)


def test_17_creates_service_and_deployment_insufficient_resource__service_outage_invtest():
    # print("17")
    # Initialize scheduler, globalVar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)
    n.amountOfActivePods = 2

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

    # priority for pod-to-evict
    # pc = PriorityClass()
    # pc.priority = 10
    # pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]
    s.searchable = True

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_2)
    pod_running_1.hasService = True
    pod_running_2.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    # pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)
    d.amountOfActivePods = 2
    d.spec_replicas = 2
    pod_running_1.hasDeployment = True
    pod_running_2.hasDeployment = True

    dnew = Deployment()
    dnew.metadata_name = "new-deploymt"
    dnew.podList.add(pod_pending_1)
    dnew.amountOfActivePods = 0
    dnew.spec_replicas = 1
    pod_pending_1.hasDeployment = True

    snew = Service()
    snew.metadata_name = "test-service-new"
    snew.amountOfActivePods = 0
    snew.status = STATUS_SERV["Pending"]
    snew.podList.add(pod_pending_1)
    pod_pending_1.hasService = True
    snew.searchable = True

    k.state_objects.extend([n, s, pod_running_1, pod_running_2, d])
    yamlState = convert_space_to_yaml(k.state_objects, wrap_items=True)
    create_objects = [snew, dnew]
    yamlCreate = convert_space_to_yaml(create_objects, wrap_items=False, load_logic_support=False)
    k2 = KubernetesCluster()
    for y in yamlState:
        # print(y)
        k2.load(y)
    for y in yamlCreate:
        k2.load(y, mode=KubernetesCluster.CREATE_MODE)
    k2._build_state()
    k._build_state()
    globalVar = k2.state_objects[1]
    scheduler = k2.state_objects[0]
    # print_objects(k.state_objects)
    class NewGoal(Check_services):
        # pass
        goal = lambda self: globalVar.is_service_disrupted == True and \
                scheduler.status == STATUS_SCHED["Clean"]
    p = NewGoal(k2.state_objects)
    p.run(timeout=200)
    for a in p.plan:
        print(a)
    assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])
    assert not "NodeOutageFinished" in "\n".join([repr(x) for x in p.plan])


def test_17_2_creates_service_and_deployment_insufficient_resource__two_service_outage():
    # print("17")
    # Initialize scheduler, globalVar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5

    # Create running pods
    pod_running_1 = build_running_pod(1,2,2,n)
    pod_running_2 = build_running_pod(2,2,2,n)
    n.amountOfActivePods = 2

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]
    s.searchable = True

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_2)
    pod_running_1.hasService = True
    pod_running_2.hasService = True

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_2 = build_pending_pod(4,2,2,n)
    # pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.podQueue.add(pod_pending_2)
    scheduler.queueLength += 2
    scheduler.status = STATUS_SCHED["Changed"]

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)
    d.amountOfActivePods = 2
    d.spec_replicas = 2
    pod_running_1.hasDeployment = True
    pod_running_2.hasDeployment = True

    dnew = Deployment()
    dnew.podList.add(pod_pending_1)
    dnew.amountOfActivePods = 0
    dnew.spec_replicas = 1
    pod_pending_1.hasDeployment = True

    snew = Service()
    snew.metadata_name = "test-service-new"
    snew.amountOfActivePods = 0
    snew.status = STATUS_SERV["Pending"]
    snew.podList.add(pod_pending_1)
    pod_pending_1.hasService = True
    snew.searchable = True

    snew2 = Service()
    snew2.metadata_name = "test-service-new"
    snew2.amountOfActivePods = 0
    snew2.status = STATUS_SERV["Pending"]
    snew2.podList.add(pod_pending_2)
    pod_pending_2.hasService = True
    snew2.searchable = True

    k.state_objects.extend([n, s, snew, snew2, pod_running_1, pod_running_2, pod_pending_1, pod_pending_2, d, dnew])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_pending_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k.state_objects)) 
    class NewGoal_k1(Check_services):
        pass
    p = NewGoal_k1(k.state_objects)

    pod_pending_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Pending"], k2.state_objects))
    class NewGoal_k2(Check_services):
        pass
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["MarkDeploymentOutageEvent"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_19_has_deployment_creates_deployment__pods_evicted_pods_pending_test_snackable_branch():
    # print("19")
    k = KubernetesCluster()
    prios = {}
    pch = PriorityClass()
    k.state_objects.append(pch)
    pch.priority = 10
    pch.metadata_name = "high-prio-test"
    prios["high"] = pch
    pcl = PriorityClass()
    k.state_objects.append(pcl)
    pcl.priority = 1
    pcl.metadata_name = "low-prio-test"
    prios["low"] = pcl

    pods = []
    node = Node()
    k.state_objects.append(node)
    node.memCapacity = 3
    node.cpuCapacity = 3
    d_was = Deployment()
    k.state_objects.append(d_was)
    d_was.metadata_name = "d_was"
    d_was.priorityClass = prios["low"]
    d_was.spec_template_spec_priorityClassName = prios["low"].metadata_name
    d_was.amountOfActivePods = 2
    d_was.spec_replicas = 2
    for i in range(2):
        pod = Pod()
        k.state_objects.append(pod)
        pod.metadata_name = "pod_number_" + str(i)
        pod.memRequest = 1
        pod.cpuRequest = 1
        pod.status = STATUS_POD["Running"]
        pod.priorityClass = prios["low"]
        pod.spec_priorityClassName = prios["low"].metadata_name
        pod.hasDeployment = True
        pods.append(pod)
        node.amountOfActivePods += 1
        node.currentFormalMemConsumption += pod.memRequest
        node.currentFormalCpuConsumption += pod.cpuRequest
        d_was.podList.add(pod)

    d_new = Deployment()
    d_new.metadata_name = "d_new"
    d_new.spec_replicas = 2
    d_new.priorityClass = prios["high"]
    d_new.spec_template_spec_priorityClassName = prios["high"].metadata_name
    d_new.memRequest = 1
    d_new.cpuRequest = 1
    d_new.hook_after_create(k.state_objects)
    k.state_objects.append(d_new)


    pod_pending_count = 0
    pPod = []
    for pod in filter(lambda x: isinstance(x, Pod), k.state_objects):
        if "pod_number_" in pod.metadata_name._get_value():
            assert pod.status._get_value() == "Running", "pod_number_X pods should be Running before planning but have {0} status".format(pod.status._get_value())
        if pod.status._get_value() == "Pending":
            pod_pending_count += 1
            pPod.append(pod)
    assert pod_pending_count == 2, "should be 2 pod in pending have only {0}".format(pod_pending_count)

    class TestRun(K8ServiceInterruptSearch):
        goal = lambda self: self.scheduler.status == STATUS_SCHED["Clean"] and pPod[0].status == STATUS_POD["Running"]and pPod[1].status == STATUS_POD["Running"]

    p = TestRun(k.state_objects)
    # print_objects(k.state_objects)
    # p.run()
    # print("scenario \n{0}".format(p.plan))
    p.xrun()
    # print("---after calculation ----")
    # print_objects(k.state_objects)
    assert d_new.amountOfActivePods == 2
    assert d_was.amountOfActivePods == 1
    assert node.amountOfActivePods == 3

    for pod in filter(lambda x: isinstance(x, Pod), k.state_objects):
        if "d_new" in pod.metadata_name._get_value():
            assert pod.status._get_value() == "Running", "{1} pods should be Running after planning but have {0} status".format(pod.status._get_value(),pod.metadata_name._get_value() )

@pytest.mark.skip(reason="This test case is broken see #109")
def test_20_scheduller_counter_bug():
    # print("20")
    k = KubernetesCluster()
    prios = {}
    pch = PriorityClass()
    k.state_objects.append(pch)
    pch.priority = 10
    pch.metadata_name = "high-prio-test"
    prios["high"] = pch
    pcl = PriorityClass()
    k.state_objects.append(pcl)
    pcl.priority = 1
    pcl.metadata_name = "low-prio-test"
    prios["low"] = pcl

    pods = []
    node = Node()
    k.state_objects.append(node)
    node.memCapacity = 3
    node.cpuCapacity = 3
    d_was = Deployment()
    k.state_objects.append(d_was)
    d_was.metadata_name = "d_was"
    d_was.priorityClass = prios["low"]
    d_was.spec_template_spec_priorityClassName = prios["low"].metadata_name
    d_was.amountOfActivePods = 2
    d_was.spec_replicas = 2
    for i in range(2):
        pod = Pod()
        k.state_objects.append(pod)
        pod.metadata_name = "pod_number_" + str(i)
        pod.memRequest = 1
        pod.cpuRequest = 1
        pod.status = STATUS_POD["Running"]
        pod.priorityClass = prios["low"]
        pod.spec_priorityClassName = prios["low"].metadata_name
        pod.hasDeployment = True
        pods.append(pod)
        node.amountOfActivePods += 1
        node.currentFormalMemConsumption += pod.memRequest
        node.currentFormalCpuConsumption += pod.cpuRequest
        d_was.podList.add(pod)

    d_new = Deployment()
    d_new.metadata_name = "d_new"
    d_new.spec_replicas = 2
    d_new.priorityClass = prios["high"]
    d_new.spec_template_spec_priorityClassName = prios["high"].metadata_name
    d_new.memRequest = 1
    d_new.cpuRequest = 1
    d_new.hook_after_create(k.state_objects)
    k.state_objects.append(d_new)

    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    pPod = []

    for pod in filter(lambda x: isinstance(x, Pod), k.state_objects):
        if pod.status._get_value() == "Pending":
            pPod.append(pod)

    class TestRun(K8ServiceInterruptSearch):
        goal = lambda self: self.scheduler.status == STATUS_SCHED["Clean"] and pPod[0].status == STATUS_POD["Running"]and pPod[1].status == STATUS_POD["Running"]

    p = TestRun(k.state_objects)
    p.xrun()
    assert scheduler.queueLength._get_value() == 0
    assert len(scheduler.podQueue._get_value()) == 0

def test_21_has_daemonset_creates_deployment__pods_evicted_daemonset_outage_synthetic():
    # print("21")
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n1 = Node("node 1")
    n1.cpuCapacity = 3
    n1.memCapacity = 3

    n2 = Node("node 2")
    n2.cpuCapacity = 3
    n2.memCapacity = 3


    #Create Daemonset
    ds = DaemonSet()
    ds.searchable = True

    # Create running pods as Daemonset
    pod_running_1 = build_running_pod_with_d(1,2,2,n1,None,ds)
    pod_running_2 = build_running_pod_with_d(2,2,2,n2,None,ds)
    n1.amountOfActivePods = 1
    n2.amountOfActivePods = 1

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
 

    # Pending pod with deployment
    d = Deployment()
    d.spec_replicas = 1
    d.priorityClass = pc

    pod_pending_1 = build_pending_pod_with_d(3,2,2,n1,d,None)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n1, n2, pc, pod_running_1, pod_running_2, pod_pending_1, d,ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    class NewGoal_k1(Check_daemonsets):
        pass
    p = NewGoal_k1(k.state_objects)

    class NewGoal_k2(Check_daemonsets):
        pass
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["MarkDaemonsetOutageEvent"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)


def prepare_test_22_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic():
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n1 = Node()
    n1.metadata_name = "node 1"
    n1.cpuCapacity = 3
    n1.memCapacity = 3
    n1.isNull == False

    n2 = Node("node 2")
    n2.metadata_name = "node 2"
    n2.cpuCapacity = 3
    n2.memCapacity = 3
    n2.isNull == False


    #Create Daemonset
    ds = DaemonSet()
    ds.searchable = True

    # Create running pods as Daemonset
    pod_running_1 = build_running_pod_with_d(1,2,2,n1,None,ds)
    pod_running_2 = build_running_pod_with_d(2,2,2,n2,None,ds)
    n1.amountOfActivePods = 1
    n2.amountOfActivePods = 1

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]
    s.podList.add(pod_running_1)
    s.podList.add(pod_running_2)

    # Pending pod with deployment
    d = Deployment()
    d.spec_replicas = 1
    d.priorityClass = pc

    pod_pending_1 = build_pending_pod_with_d(3,2,2,n1,None,None)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n1,  pc, pod_running_1, pod_running_2, pod_pending_1, d, ds])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    return k, k2

# @pytest.mark.debug(reason="if debug needed - uncomment me")
# def test_22_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic_step1():
#     # print("22")
#     # Initialize scheduler, globalvar
#     k, k2 =prepare_test_22_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic()
#     class NewGoal(OptimisticRun):
#         # pass
#         # goal = lambda self: globalvar.is_daemonset_disrupted == True
#         goal = lambda self: pod_running_1.status == STATUS_POD["Killing"]
#     p = NewGoal(k.state_objects)
#     p.run(timeout=200)
#     # for a in p.plan:
#     #     print(a) 
#     assert "Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined" in "\n".join([repr(x) for x in p.plan])
#     # assert "MarkDeploymentOutageEvent" in "\n".join([repr(x) for x in p.plan])

# @pytest.mark.debug(reason="if debug needed - uncomment me")
# def test_23_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic_step2():
#     # print("23")
#     # Initialize scheduler, globalvar
#     k, k2 = prepare_test_22_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic()
#     # print_objects(k.state_objects)
#     class NewGoal(OptimisticRun):
#         # pass
#         # goal = lambda self: globalvar.is_daemonset_disrupted == True
#         goal = lambda self: pod_running_1.status == STATUS_POD["Pending"]
#     p = NewGoal(k.state_objects)
#     p.run(timeout=200)
#     # print("---after calculation ----")
#     # print_objects(k.state_objects)
#     # for a in p.plan:
#     #     print(a) 
#     assert "Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined" in "\n".join([repr(x) for x in p.plan])
#     assert "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
  
def test_24_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic_step3():
    # print("24")
    # Initialize scheduler, globalvar
    k, k2 = prepare_test_22_has_daemonset_with_service_creates_deployment__pods_evicted_daemonset_outage_synthetic()
    globalvar_k1 = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    globalvar_k2 = next(filter(lambda x: isinstance(x, GlobalVar), k2.state_objects))

    class NewGoal_k1(Check_daemonsets):
        goal = lambda self: globalvar_k1.is_daemonset_disrupted == True
    p = NewGoal_k1(k.state_objects)

    class NewGoal_k2(Check_daemonsets):
        goal = lambda self: globalvar_k1.is_daemonset_disrupted == True
    p2 = NewGoal_k2(k2.state_objects)
    
    assert_conditions = ["MarkDaemonsetOutageEvent"]
    not_assert_conditions = []
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def prepare_test_has_service_only_on_node_that_gets_disrupted():
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
    # initial node state
    n1 = Node()
    n1.metadata_name = "node 1"
    n1.cpuCapacity = 6
    n1.memCapacity = 6
    n1.isNull == False

    n2 = Node("node 2")
    n2.metadata_name = "node 2"
    n2.cpuCapacity = 6
    n2.memCapacity = 6
    n2.isNull == False

    # Create running pods as Daemonset
    pod_running_1 = build_running_pod_with_d(1,2,2,n1,None,None)
    pod_running_2 = build_running_pod_with_d(2,2,2,n1,None,None)
    pod_running_3 = build_running_pod_with_d(3,2,2,n1,None,None)
    pod_running_4 = build_running_pod_with_d(4,2,2,n2,None,None)
    pod_running_5 = build_running_pod_with_d(5,2,2,n2,None,None)
    pod_running_6 = build_running_pod_with_d(6,2,2,n2,None,None)
    n1.amountOfActivePods = 3
    n2.amountOfActivePods = 3

    # # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service1"
    s1.amountOfActivePods = 2
    s1.status = STATUS_SERV["Started"]
    
    s2 = Service()
    s2.metadata_name = "test-service2"
    s2.amountOfActivePods = 4
    s2.status = STATUS_SERV["Started"]

    s1.podList.add(pod_running_1)
    s1.podList.add(pod_running_2)
    s2.podList.add(pod_running_3)
    s2.podList.add(pod_running_4)
    s2.podList.add(pod_running_5)
    s2.podList.add(pod_running_6)
    # s2.podList.add(pod_running_7)
    
    pod_running_1.hasService = True
    pod_running_2.hasService = True
    pod_running_3.hasService = True
    pod_running_4.hasService = True
    pod_running_5.hasService = True
    pod_running_6.hasService = True

    ## We have clean scheduler queue
    scheduler.status = STATUS_SCHED["Clean"]

    k.state_objects.extend([n1,  n2, s1, s2, pod_running_1, pod_running_2, pod_running_3, pod_running_4, pod_running_5, pod_running_6])
    return k,n1,pod_running_1

# @pytest.mark.skip(reason="if debug needed - uncomment me")
# def test_25_node_outage_with_service_eviction_step0():
#     # print("25")
#     # Initialize scheduler, globalvar
#     k,n1,pod_running_1=construct_space_1322_has_service_only_on_node_that_gets_disrupted()
#     globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
#     class test_25_node_outage_with_service_eviction_step1(Check_services):
#         goal = lambda self: self.pod_running_1.status == STATUS_POD["Killing"]
#     p = test_25_node_outage_with_service_eviction_step1(k.state_objects)
#     p.run(timeout=200)
#     # print_objects(k.state_objects)
#     # for a in p.plan:
#     #     print(a) 
#     assert "Initiate_node_outage" in "\n".join([repr(x) for x in p.plan])
#     # assert "Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined" in "\n".join([repr(x) for x in p.plan])
#     # assert "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
#     # assert "MarkDaemonsetOutageEvent" in "\n".join([repr(x) for x in p.plan])

# # @pytest.mark.skip(reason="if debug needed - uncomment me")
# def test_25_node_outage_with_service_eviction_step1():
#     # print("25")
#     # Initialize scheduler, globalvar
#     k,n1=construct_space_1322_has_service_only_on_node_that_gets_disrupted()
#     globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
#     class test_25_node_outage_with_service_eviction_step1(Check_services):
#         goal = lambda self: n1.status == STATUS_NODE["Inactive"]
#     p = test_25_node_outage_with_service_eviction_step1(k.state_objects)
#     p.run(timeout=200)
#     # print_objects(k.state_objects)
#     # for a in p.plan:
#     #     print(a) 
#     assert "Initiate_node_outage" in "\n".join([repr(x) for x in p.plan])
#     # assert "Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined" in "\n".join([repr(x) for x in p.plan])
#     # assert "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
#     # assert "MarkDaemonsetOutageEvent" in "\n".join([repr(x) for x in p.plan])
    
# @pytest.mark.skip(reason="if debug needed - uncomment me")
# def test_26_node_outage_with_service_eviction_step2():
#     # print("26")
#     # Initialize scheduler, globalvar
#     k,n1=construct_space_1322_has_service_only_on_node_that_gets_disrupted()
#     globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
#     class Check_services(Check_services):
#         goal = lambda self: globalvar.is_node_disrupted == True
#     p = Check_services(k.state_objects)
#     p.run(timeout=200)
#     # print_objects(k.state_objects)
#     # for a in p.plan:
#     #     print(a) 
#     # assert "StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
#     # assert "Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined" in "\n".join([repr(x) for x in p.plan])
#     # assert "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
#     # assert "MarkDaemonsetOutageEvent" in "\n".join([repr(x) for x in p.plan])

# @pytest.mark.debug(reason="if debug needed - uncomment me")
# def test_27_node_outage_with_service_eviction_step3():
#     # print("27")
#     # Initialize scheduler, globalvar
#     k,n1=construct_space_1322_has_service_only_on_node_that_gets_disrupted()
#     globalvar = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects))
#     class Check_services_with_node_eviction(Check_services):
#         goal = lambda self: globalvar.is_node_disrupted == True and globalvar.is_service_disrupted == True
#     p = Check_services_with_node_eviction(k.state_objects)
#     p.run(timeout=200)
#     # print_objects(k.state_objects)
#     # for a in p.plan:
#     #     print(a) 
#     # assert "StartPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
#     # assert "Evict_and_replace_less_prioritized_pod_when_target_node_is_not_defined" in "\n".join([repr(x) for x in p.plan])
#     # assert "KillPod_IF_Deployment_isNUll_Service_isNull_Daemonset_isNotNull" in "\n".join([repr(x) for x in p.plan])
#     # assert "MarkDaemonsetOutageEvent" in "\n".join([repr(x) for x in p.plan])

def test_28_from_test_5_evict_and_killpod_deployment_without_service_with_null_mem_request():
    # print("28")
    # Initialize scheduler, globalvar
    k = KubernetesCluster()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    # initial node state
    n = Node()
    n.cpuCapacity = 5
    n.memCapacity = 5
    n.isNull = False

    # create Deploymnent that we're going to detect failure of...
    d = Deployment()
    d.spec_replicas = 2

    # Create running pods
    pod_running_1 = build_running_pod_with_d(1,2,2,n,d,None)
    pod_running_2 = build_running_pod_with_d(2,2,2,n,d,None)
    n.amountOfActivePods = 2
    pod_running_1.memRequest = 0
    pod_running_2.memRequest = 0

    # priority for pod-to-evict
    pc = PriorityClass()
    pc.priority = 10
    pc.metadata_name = "high-prio-test"

    # Service to detecte eviction
    s = Service()
    s.metadata_name = "test-service"

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]
    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, s, pod_pending_1, d])
    create_objects = []
    k2 = reload_cluster_from_yaml(k,create_objects)
    k._build_state()
    pod_running_1_1 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k.state_objects)) 
    class NewGoal_k1(OptimisticRun):
        goal = lambda self: pod_running_1_1.status == STATUS_POD["Pending"]
    p = NewGoal_k1(k.state_objects)

    pod_running_1_2 = next(filter(lambda x: isinstance(x, Pod) and x.status._property_value == STATUS_POD["Running"], k2.state_objects))
    class NewGoal_k2(OptimisticRun):
        goal = lambda self: pod_running_1_2.status == STATUS_POD["Pending"]
    p2 = NewGoal_k2(k2.state_objects)
    assert_conditions = ["Evict_and_replace_less_prioritized_pod_when_target_node_is_defined",\
                        "KillPod_IF_Deployment_isNotNUll_Service_isNull_Daemonset_isNull"]
    not_assert_conditions = ["NodeOutageFinished"]
    checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

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
        pod_running_2 = build_running_pod_with_d(pod_id,2,2,nodes[1],None,None)
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


def test_29():
    k, k2, p, p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,15,1,1,1,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_30():
        k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,19,2,2,1,1)
        assert_conditions = ["SchedulerQueueCleanHighCost",\
                            "Mark_node_outage_event"]
        not_assert_conditions = []
        assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_31():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,23,3,3,1,1)
            assert_conditions = ["SchedulerQueueCleanHighCost",\
                        "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
def test_32():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,26,3,3,2,2)
            assert_conditions = ["MarkServiceOutageEvent",\
                    "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
def test_33():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,32,4,4,4,4)
            assert_conditions = ["SchedulerQueueCleanHighCost",\
                "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
def test_34():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,40,5,5,5,5)
            assert_conditions = ["SchedulerQueueCleanHighCost",\
                            "Mark_node_outage_event"]
            not_assert_conditions = []
            checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
    
def test_36():
    k, k2, p, p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,8,1,1,1,1)
    assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
    not_assert_conditions = []
    assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_37():
        k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,8,2,2,1,1)
        assert_conditions = ["MarkServiceOutageEvent",\
                            "Mark_node_outage_event"]
        not_assert_conditions = []
        assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)

def test_38():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,8,3,3,1,1)
            assert_conditions = ["MarkServiceOutageEvent",\
                        "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
def test_39():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,10,3,3,2,2)
            assert_conditions = ["MarkServiceOutageEvent",\
                    "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
def test_39():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,12,4,4,4,4)
            assert_conditions = ["MarkServiceOutageEvent",\
                "Mark_node_outage_event"]
            not_assert_conditions = []
            assert_brake = checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
def test_40():
            k, k2,p ,p2 = prepare_test_29_many_pods_not_enough_capacity_for_service(2,25,5,5,5,5)
            assert_conditions = ["MarkServiceOutageEvent",\
                            "Mark_node_outage_event"]
            not_assert_conditions = []
            checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,DEBUG_MODE)
  
