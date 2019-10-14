import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch, AnyDeploymentInterrupted, NodeInterupted
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario
import guardctl.model.kinds.Service as mservice
from tests.test_util import print_objects


TEST_CLUSTER_FOLDER = "./tests/dataset_small_1/cluster_dump"
TEST_DEPLOYMENT = "./tests/dataset_small_1/deployment.yaml"

EXCLUDED_SERV = {
    # "redis-master" : TypeServ("redis-master"),
    # "redis-master-evict" : TypeServ("redis-master-evict"),
    # "default-http-backend" : TypeServ("default-http-backend"),
    # "redis-slave" : TypeServ("redis-slave"),
    "heapster": TypeServ("heapster")
    # -d ./tests/daemonset_eviction_with_deployment/cluster_dump/ -f ./tests/daemonset_eviction_with_deployment/daemonset_create.yaml -e Service:redis-master,Service:redis-master-evict,Service:default-http-backend,Service:redis-slave
}

def mark_excluded_service(object_space):
    services = filter(lambda x: isinstance(x, mservice.Service), object_space)
    for service in services:
        if service.metadata_name in list(EXCLUDED_SERV):
           service.searchable = False

# class AnyDeploymentInterrupted(K8ServiceInterruptSearch):

#     goal = lambda self: self.globalVar.is_deployment_disrupted == True and \
#             self.scheduler.status == STATUS_SCHED["Clean"]

ALL_STATE = None

import logzero
logzero.logfile("./test.log", disableStderrLogger=False)


def test_anydeployment_interrupted_fromfiles():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k._build_state()
    mark_excluded_service(k.state_objects)
    print("------Objects before solver processing------")
    print_objects(k.state_objects)
    p = NodeInterupted(k.state_objects)
    p.run(timeout=660, sessionName="test_anydeployment_interrupted_fromfiles")
    if not p.plan:
        raise Exception("Could not solve %s" % p.__class__.__name__)
    print("------Objects after solver processing------")
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)
