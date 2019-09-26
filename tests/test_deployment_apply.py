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
TEST_DEPLOYMENT = "./tests/test-deployment/deployment.yaml"
TEST_DEPLOYMENT_repl10 = "./tests/test-deployment/deployment_repl10.yaml"
TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"

def test_create_n_apply():
    k = KubernetesCluster()
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k.apply_resource(open(TEST_DEPLOYMENT_repl10).read())
    k._build_state()
    for p in filter(lambda x: isinstance(x, Deployment), k.state_objects):
        if p.metadata_name == "redis-master":
            if len(p.podList._property_value) != 10:
                raise ValueError("Wrong pods amount - {0} (10)".format(len(p.podList._property_value)))
            return
    raise ValueError("Could not find service loded")

@pytest.mark.skip(reason="speed up")
def test_load_n_apply():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.apply_resource(open(TEST_DEPLOYMENT_repl10).read())
    k._build_state()
    for p in filter(lambda x: isinstance(x, Deployment), k.state_objects):
        if p.metadata_name == "redis-master":
            if len(p.podList._property_value) != 10:
                raise ValueError("Wrong pods amount - {0} (10)".format(len(p.podList._property_value)))
            return
    raise ValueError("Could not find service loded")
