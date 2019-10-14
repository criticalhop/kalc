import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
import guardctl.model.kinds.Pod as mpod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from tests.test_util import print_objects
from guardctl.model.scenario import Scenario
from poodle import planned


def test_start_pod_with_scheduler():
    k = KubernetesCluster()
    pods = []
    node = Node()
    node.memCapacity = 3
    node.cpuCapacity = 3
    for i in range(2):
        pod = mpod.Pod()
        pod.metadata_name = str(i)
        pod.memRequest = 2
        pod.cpuRequest = 2
        pods.append(pod)
    pods[0].status = STATUS_POD["Running"]
    pods[0].atNode = node
    k.state_objects.extend(pods)
    k.state_objects.append(node)

    k._build_state()
    

    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    scheduler.status = STATUS_SCHED["Changed"]
    scheduler.podQueue.add(pods[0])
    scheduler.queueLength += 1
    class TestRun(K8ServiceInterruptSearch):
        goal = lambda self: pods[1].status == STATUS_POD["Running"]
    p = TestRun(k.state_objects)
    p.run()
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)

