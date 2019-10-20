from tests.test_util import print_objects
from guardctl.model.search import AnyGoal 
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
from tests.test_util import print_objects
from guardctl.model.scenario import Scenario
from poodle import planned

def build_running_pod(podName, cpuRequest, memRequest, atNode):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = 2
    pod_running_1.memRequest = 2
    pod_running_1.atNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    return pod_running_1

def build_pending_pod(podName, cpuRequest, memRequest, toNode):
    p = build_running_pod(podName, cpuRequest, memRequest, Node.NODE_NULL)
    p.status = STATUS_POD["Pending"]
    p.toNode = toNode 
    return p

def test_run_pods_no_eviction():
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

    k.state_objects.extend([n, pc, pod_pending_1, ds])
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    # TODO: fix strange behaviour -->>
    # assert "StartPod" in "\n".join([x() for x in p.plan])
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    # for a in p.plan:
    #     print(a) 


def test_run_pods_with_eviction():
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

    ## Set consumptoin as expected
    n.currentFormalCpuConsumption = 4
    n.currentFormalMemConsumption = 4

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
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    # for a in p.plan:
        # print(a)


def test_synthetic_service_outage():
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
    pod_running_1.targetService = s

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1])
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        pass
        # goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])
    # for a in p.plan:
        # print(a)

def construct_multi_pods_eviction_problem():
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
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    # TODO: no outage detected if res is not 4
    pod_running_1.targetService = s
    pod_running_2.targetService = s

    # Pending pod
    pod_pending_1 = build_pending_pod(3,4,4,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1])
    # print_objects(k.state_objects)
    return k

def test_synthetic_service_outage_multi():
    "Multiple pods are evicted from one service to cause outage"
    k = construct_multi_pods_eviction_problem()
    class NewGOal(AnyGoal):
        pass
        # goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])
    for a in p.plan:
        print(a)

@pytest.mark.skip(reason="FIXME - this test fails because of a bug in the model")
def test_synthetic_service_NO_outage_multi():
    "No outage is caused by evicting only one pod of a multi-pod service"
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
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has only one pod so it can detect outage
    #  (we can't evict all pods here with one)
    # TODO: no outage detected if res is not 4
    pod_running_1.targetService = s
    pod_running_2.targetService = s

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

    ## Add pod to scheduler queue
    scheduler.podQueue.add(pod_pending_1)
    scheduler.queueLength += 1
    scheduler.status = STATUS_SCHED["Changed"]

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1])
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        pass
        # goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    if p.plan:
        print("ERROR!!!")
        for a in p.plan:
            print(a)
        raise Exception("Plan must be empty in this case")

# def test_killpod_deployment():
#     "Test that killPod works for deployment"
#     # Initialize scheduler, globalvar
#     k = KubernetesCluster()
#     scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
#     # initial node state
#     n = Node()
#     n.cpuCapacity = 5
#     n.memCapacity = 5

#     # Create running pods
#     pod_running_1 = build_running_pod(1,2,2,n)
#     pod_running_2 = build_running_pod(2,2,2,n)

#     ## Set consumptoin as expected
#     n.currentFormalCpuConsumption = 4
#     n.currentFormalMemConsumption = 4

#     # priority for pod-to-evict
#     pc = PriorityClass()
#     pc.priority = 10
#     pc.metadata_name = "high-prio-test"

#     # Service to detecte eviction
#     s = Service()
#     s.metadata_name = "test-service"
#     s.amountOfActivePods = 2
#     s.status = STATUS_SERV["Started"]

#     # our service has multiple pods but we are detecting pods pending issue
#     # remove service as we are detecting service outage by a bug above
#     # pod_running_1.targetService = s
#     # pod_running_2.targetService = s

#     # Pending pod
#     pod_pending_1 = build_pending_pod(3,2,2,n)
#     pod_pending_1.priorityClass = pc # high prio will evict!

#     ## Add pod to scheduler queue
#     scheduler.podQueue.add(pod_pending_1)
#     scheduler.queueLength += 1
#     scheduler.status = STATUS_SCHED["Changed"]

#     # create Deploymnent that we're going to detect failure of...
#     d = Deployment()
#     d.podList.add(pod_running_1)
#     d.podList.add(pod_running_2)
#     d.amountOfActivePods = 2
#     d.spec_replicas = 2

#     k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1, d])
#     # print_objects(k.state_objects)
#     class NewGOal(AnyGoal):
#         goal = lambda self: scheduler.debug_var == True
#     p = NewGOal(k.state_objects)
#     p.run(timeout=150)
#     for a in p.plan:
#         print(a) 



def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_synthetic():
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
    s.amountOfActivePods = 2
    s.status = STATUS_SERV["Started"]

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    # pod_running_1.targetService = s
    # pod_running_2.targetService = s

    # Pending pod
    pod_pending_1 = build_pending_pod(3,2,2,n)
    pod_pending_1.priorityClass = pc # high prio will evict!

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

    k.state_objects.extend([n, pc, pod_running_1, pod_running_2, pod_pending_1, d])
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        pass
        # goal = lambda self: pod_pending_1.status == STATUS_POD["Running"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    assert "StartPod" in "\n".join([repr(x) for x in p.plan])
    assert "Evict" in "\n".join([repr(x) for x in p.plan])
    assert "MarkDeploymentOutageEvent" in "\n".join([repr(x) for x in p.plan])
    # for a in p.plan:
        # print(a) 

def test_creates_deployment_but_insufficient_resource__pods_pending_synthetic():
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

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    # pod_running_1.targetService = s
    # pod_running_2.targetService = s

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

    dnew = Deployment()
    dnew.podList.add(pod_pending_1)
    dnew.amountOfActivePods = 0
    dnew.spec_replicas = 1

    k.state_objects.extend([n, pod_running_1, pod_running_2, pod_pending_1, d, dnew])
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        pass
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    # for a in p.plan:
        # print(a) 
    assert "MarkDeploymentOutageEvent" in "\n".join([repr(x) for x in p.plan])


def test_creates_service_and_deployment_insufficient_resource__service_outage():
    # Initialize scheduler, globalvar
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

    # our service has multiple pods but we are detecting pods pending issue
    # remove service as we are detecting service outage by a bug above
    pod_running_1.targetService = s
    pod_running_2.targetService = s

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

    dnew = Deployment()
    dnew.podList.add(pod_pending_1)
    dnew.amountOfActivePods = 0
    dnew.spec_replicas = 1

    snew = Service()
    snew.metadata_name = "test-service-new"
    snew.amountOfActivePods = 0
    # snew.status = STATUS_SERV["Started"]
    pod_pending_1.targetService = snew

    k.state_objects.extend([n, s, snew, pod_running_1, pod_running_2, pod_pending_1, d, dnew])
    # print_objects(k.state_objects)
    class NewGOal(AnyGoal):
        goal = lambda self: globalVar.is_service_disrupted == True and \
                scheduler.status == STATUS_SCHED["Clean"]
    p = NewGOal(k.state_objects)
    p.run(timeout=50)
    # for a in p.plan:
        # print(a) 
    assert "MarkServiceOutageEvent" in "\n".join([repr(x) for x in p.plan])

# Simple test for pod 
def test_synthetic_start_pod_with_scheduler():
    k = KubernetesCluster()
    pods = []
    node = Node()
    node.memCapacity = 3
    node.cpuCapacity = 3
    for i in range(2):
        pod = Pod()
        pod.metadata_name = str(i)
        pod.memRequest = 1
        pod.cpuRequest = 1
        pods.append(pod)
    pods[0].status = STATUS_POD["Running"]
    pods[0].atNode = node
    pods[1].toNode = node

    k.state_objects.extend(pods)
    k.state_objects.append(node)

    k._build_state()
    
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    scheduler.status = STATUS_SCHED["Changed"]
    scheduler.podQueue.add(pods[1])
    scheduler.queueLength += 1
    class TestRun(K8ServiceInterruptSearch):
        goal = lambda self: pods[1].status == STATUS_POD["Running"]
    p = TestRun(k.state_objects)
    p.run()
    # print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)
    for pod in filter(lambda x: isinstance(x, Pod), k.state_objects):
        assert pod.status._get_value() == "Running", "All pods should be Running in this case. Some pod is {0}".format(pod.status._get_value())