import pytest
import yaml
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.system.Scheduler import Scheduler
from kalc.misc.const import *
from kalc.model.search import K8ServiceInterruptSearch
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
from kalc.cli import run


TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"
TEST_DEPLOYMENT = "./tests/test-deployment/deployment.yaml"
TEST_DEPLOYMENT1 = "./tests/test-deployment/deployment1.yaml"
TEST_DEPLOYMENT2 = "./tests/test-deployment/deployment2.yaml"

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_simple_create_scale():
    k = KubernetesCluster()
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k.create_resource(open(TEST_DEPLOYMENT1).read())
    k.scale(5, "deployment/redis-master deployment/redis-master1")

    objects = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    for p in objects:
        if len(p.podList) != 5 :
            raise ValueError("Scale doesn't work")

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_simple_load_scale():
    k = KubernetesCluster()
    k.load_dir(TEST_DEPLOYMENT_DUMP)
    k.scale(5, "deployment/redis-master deployment/redis-master1")

    objects = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    for p in objects:
        if len(p.podList) != 5 :
            raise ValueError("Scale doesn't work")

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_simple_load_create_scale():
    k = KubernetesCluster()
    k.load_dir(TEST_DEPLOYMENT_DUMP)
    k.create_resource(open(TEST_DEPLOYMENT1).read())
    k.scale(5, "deployment/redis-master deployment/redis-master1")

    objects = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    for p in objects:
        if len(p.podList) != 5 :
            raise ValueError("Scale doesn't work")