import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch, OptimisticRun
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario
import guardctl.model.kinds.Service as mservice
from tests.test_util import print_objects
from poodle import schedule

TEST_DEPLOYMENT_1 = "./tests/entity_dumps/dump_one_deployment.yaml"
TEST_POD_1 = "./tests/entity_dumps/dump_one_pod_pending.yaml"
TEST_NODE_2 = "./tests/entity_dumps/dump_two_nodes.yaml"


ALL_STATE = None

import logzero
logzero.logfile("./test.log", disableStderrLogger=False)


def test_start_pod():
    k = KubernetesCluster()
    k.load(open(TEST_POD_1).read())
    k.load(open(TEST_NODE_2).read())
    k.create_resource(open(TEST_DEPLOYMENT_1).read())
    k._build_state()
    # pod = Scheduler.StartPod_IF_service_isnull__deployment_isnull(next(filter(lambda x: isinstance(x, Scheduler) , k.state_objects),
    #     podStarted =  next(filter(lambda x: isinstance(x, Pod) and x.status == STATUS_POD["Pending"] , k.state_objects)),
    #     node1 =  next(filter(lambda x: isinstance(x, Node), k.state_objects)),
    #     scheduler1 =  next(filter(lambda x: isinstance(x, Scheduler) , k.state_objects))
    # )
    scheduler = next(filter(lambda x: isinstance(x, Scheduler) , k.state_objects))
    pod_pending = next(filter(lambda x: isinstance(x, Pod) and x.status == STATUS_POD["Pending"], k.state_objects))

    schedule(
        methods=[scheduler.StartPod_IF_service_isnull__deployment_isnull],
        space=k.state_objects,
        goal=lambda: pod_pending.status == STATUS_POD["Running"])

    # p = OptimisticRun(k.state_objects)
    print_objects(k.state_objects)
    # p.run(timeout=360, sessionName="test_anyservice_interrupted_fromfiles")
    # if not p.plan:
    #     raise Exception("Could not solve %s" % p.__class__.__name__)
    # print(Scenario(p.plan).asyaml())
