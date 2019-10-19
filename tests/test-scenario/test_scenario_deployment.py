import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch, AnyServiceInterrupted, OptimisticRun
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario
import guardctl.model.kinds.Service as mservice
from tests.test_util import print_objects
import guardctl.model.kinds.Pod as mpod

#replicas 3 cpu: 100m memory: 500Mi
DEPLOYMENT_NEW = "./tests/test-scenario/deployment/deployment-new.yaml"
DEPLOYMENT_NEW_WO_PRIO = "./tests/test-scenario/deployment/deployment-new-wo-priority.yaml"

DUMP = "./tests/test-scenario/deployment/dump"
# cpu = 940m * 2  memory = 2701496Ki + 2701504Ki
NODE1 = "./tests/test-scenario/deployment/dump/node1.yaml"
NODE2 = "./tests/test-scenario/deployment/dump/node2.yaml"
# pod cpu = 100m * 7 memory = 500m * 5
PODS = "./tests/test-scenario/deployment/dump/pods.yaml"
# the same but one pon in pending TODO may me need to load from cluster
PODS_PENDING = "./tests/test-scenario/deployment/dump/pods_pending.yaml"
SERVICES = "./tests/test-scenario/deployment/dump/services.yaml"
REPLICASETS = "./tests/test-scenario/deployment/dump/replicasets.yaml"
PRIORITYCLASSES = "./tests/test-scenario/deployment/dump/priorityclass.yaml"
DEPLOYMENT = "./tests/test-scenario/deployment/dump/deployments.yaml"

# @pytest.mark.skip(reason="specific scenario is not selected")
def test_start_pod():
    k = KubernetesCluster()
    k.load(open(NODE1).read())
    k.load(open(NODE2).read())
    k.load(open(PODS).read())
    # k.load(open(PODS_PENDING).read())
    k.load(open(SERVICES).read())
    k.load(open(REPLICASETS).read())
    k.load(open(PRIORITYCLASSES).read())
    k.load(open(DEPLOYMENT).read())
    k.create_resource(open(DEPLOYMENT_NEW).read())
    k._build_state()
    class PodStart(K8ServiceInterruptSearch):
        goal = lambda self: self.goalFoo()
        
        def goalFoo(self):
            for pod in filter(lambda x: isinstance(x, mpod.Pod), k.state_objects):
                if pod.status != STATUS_POD["Running"]:
                    return False
            return True

    p = PodStart(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
    # print_objects(k.state_objects)
    p.run(timeout=6600, sessionName="test_start_pods")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    assert "StartPod" in p.plan.__str__() # test for transition from Pending to Running
    pods = filter(lambda x: isinstance(x, mpod.Pod), k.state_objects)
    nodes = filter(lambda x: isinstance(x, Node), k.state_objects)
    for pod in pods:
        assert pod.atNode in nodes._get_value()


class QueueLoadCheck(K8ServiceInterruptSearch):
    goal = lambda self: self.scheduler.status == STATUS_SCHED["Changed"]

#we have pod with Pendining status in dump we should get it in Running status
@pytest.mark.skip(reason="specific scenario is not selected")
def test_start_pod_from_dump():
    k = KubernetesCluster()
    k.load(open(NODE1).read())
    k.load(open(NODE2).read())
    k.load(open(PODS_PENDING).read())
    k.load(open(SERVICES).read())
    k.load(open(REPLICASETS).read())
    k.load(open(PRIORITYCLASSES).read())
    k.load(open(DEPLOYMENT).read())
    k._build_state()
    p = QueueLoadCheck(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
    # print_objects(k.state_objects)
    p.run(timeout=6600, sessionName="test_start_pod_from_dump")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    assert "StartPod" in p.plan.__str__() # test for transition from Pending to Running
    pods = filter(lambda x: isinstance(x, mpod.Pod), k.state_objects)
    nodes = filter(lambda x: isinstance(x, Node), k.state_objects)
    for pod in pods:
        assert pod.atNode in nodes._get_value() # check each pod than each have atNode

#we have pod with Running status in dump kubernites shoul kill pods with lower piority then created
@pytest.mark.skip(reason="specific scenario is not selected")
def test_killpod():
    k = KubernetesCluster()
    k.load(open(NODE1).read()) # trim resource, run only one Node
    k.load(open(PODS).read())
    k.load(open(SERVICES).read())
    k.load(open(REPLICASETS).read())
    k.load(open(PRIORITYCLASSES).read())
    k.load(open(DEPLOYMENT).read())

    k.create_resource(open(DEPLOYMENT_NEW).read())

    k._build_state()
    p = OptimisticRun(k.state_objects) # TODO check me, i'd like to run exiction test with killpod execution
    # print_objects(k.state_objects)
    p.run(timeout=6600, sessionName="test_start_pods")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    assert "StartPod" in p.plan.__str__() # test for transition from Pending to Running
    #get pods only in Running state to check atNode value
    runningPods = filter(lambda z: z.status != STATUS_POD["Running"], (filter(lambda x: isinstance(x, mpod.Pod), k.state_objects)))
    nodes = filter(lambda x: isinstance(x, Node), k.state_objects)
    for pod in runningPods:
        assert pod.atNode in nodes._get_value() # check each pod than each have atNode
    killingPods = filter(lambda z: z.status != STATUS_POD["Killing"], (filter(lambda x: isinstance(x, mpod.Pod), k.state_objects)))
    assert len(killingPods) > 0 # test that some pod Killed

#we have pod with Running status in dump we should get "pod cant start" because our new pods have the same priority as are ran pods
@pytest.mark.skip(reason="specific scenario is not selected")
def test_pod_cant_start():
    k = KubernetesCluster()
    k.load(open(NODE1).read()) # trim resource, run only one Node
    k.load(open(PODS).read())
    k.load(open(SERVICES).read())
    k.load(open(REPLICASETS).read())
    k.load(open(PRIORITYCLASSES).read())
    k.load(open(DEPLOYMENT).read())

    k.create_resource(open(DEPLOYMENT_NEW_WO_PRIO).read())

    k._build_state()
    p = OptimisticRun(k.state_objects) # TODO check me, i'd like to run exiction test with killpod execution
    # print_objects(k.state_objects)
    p.run(timeout=6600, sessionName="test_pod_cant_start")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    #get pods only in Running state to check atNode value
    #TODO check pod cant start
    # runningPods = filter(lambda z: z.status != STATUS_POD["Running"], (filter(lambda x: isinstance(x, mpod.Pod), k.state_objects)))
    # nodes = filter(lambda x: isinstance(x, Node), k.state_objects)
    # for pod in runningPods:
    #     assert pod.atNode in nodes._get_value() # check each pod than each have atNode
    # killingPods = filter(lambda z: z.status != STATUS_POD["Killing"], (filter(lambda x: isinstance(x, mpod.Pod), k.state_objects)))
    # assert len(killingPods) > 0 # test that some pod Killed