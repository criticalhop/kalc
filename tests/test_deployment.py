import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DEPLOYMENT = "./tests/kube-config/deployment.yaml"
TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"

@pytest.mark.skip(reason="covered by above")
def test_load_twise_exeption():
    k = KubernetesCluster()
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k.create_resource(open(TEST_DEPLOYMENT).read())
    try:
        k._build_state()
    except AssertionError as e:
         print(str(e))
         assert str(e) == "Error from server (AlreadyExists): deployments.apps \"redis-master\" already exists"
    objects = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    for p in objects:
        if p.metadata_name == "redis-master":
            return
    raise ValueError("Could not find service loded")

@pytest.mark.skip(reason="covered by above")
def test_load_limits():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k._build_state()
    objects = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    for p in objects:
         if p.metadata_name == "redis-master" and \
            p.cpuRequest > -1 and \
            p.memRequest > -1 and \
            p.memLimit > -1:
            return
    raise ValueError("Could not find service loded")

@pytest.mark.skip(reason="covered by above")
def test_limits_for_pods_created():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k._build_state()
    objects = filter(lambda x: isinstance(x, Pod), k.state_objects)
    for p in objects:
        if str(p.metadata_name).startswith("redis-master") and \
            p.cpuRequest > -1 and \
            p.memRequest > -1 and \
            p.memLimit > -1:
            return
    raise ValueError("Could not find service loded")

def test_load_deployment():
    k = KubernetesCluster()
    k.load_dir(TEST_DEPLOYMENT_DUMP)
    k._build_state()