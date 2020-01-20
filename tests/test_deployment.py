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
import guardctl.misc.util as util

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DEPLOYMENT = "./tests/test-deployment/deployment.yaml"
TEST_DEPLOYMENT1 = "./tests/test-deployment/deployment1.yaml"

TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"

TEST_TARGET_DUMP = "./tests/daemonset_eviction_with_deployment/cluster_dump"
TEST_TARGET_CREATE = "./tests/daemonset_eviction_with_deployment/daemonset_create.yaml" #TODO rename file to deployment_create.yaml

def test_pod_target_attached():
    k = KubernetesCluster()
    k.load_dir(TEST_TARGET_DUMP)
    k.create_resource(open(TEST_TARGET_CREATE).read())
    k._build_state()
    deployments = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    for deployment in deployments:
        if deployment.metadata_name._get_value() == "redis-master-create":
            for pod in util.objDeduplicatorByName(deployment.podList._get_value()):
                assert pod.targetService._get_value() != None
    

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

def test_load_load_create_exeption():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
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

def test_load_twise_warning():
    k = KubernetesCluster()
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k.create_resource(open(TEST_DEPLOYMENT1).read())