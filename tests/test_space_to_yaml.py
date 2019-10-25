
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
from guardctl.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml


def build_running_pod(podName, cpuRequest, memRequest, atNode):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = cpuRequest
    pod_running_1.memRequest = memRequest
    pod_running_1.atNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    return pod_running_1

def test_convert_node_problem():
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
    n.amountOfActivePods = 2

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
    pod_running_1.targetService = s
    pod_running_2.targetService = s
    pod_running_1.hasService = True
    pod_running_2.hasService = True
    pod_running_1.priorityClass = pc
    pod_running_2.priorityClass = pc

    d = Deployment()
    d.spec_replicas = 2
    d.amountOfActivePods = 2
    pod_running_1.hasDeployment = True
    pod_running_2.hasDeployment = True
    d.podList.add(pod_running_1)
    d.podList.add(pod_running_2)

    k.state_objects.extend([n, pod_running_1, pod_running_2, s, d, pc])
    k2 = KubernetesCluster()
    for y in convert_space_to_yaml(k.state_objects, wrap_items=True):
        # print(y)
        k2.load(y)
    k2._build_state()

# TODO: test node outage exclusion