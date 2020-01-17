import pytest
import yaml
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.system.Scheduler import Scheduler
from kalc.misc.const import *
from kalc.model.search import K8ServiceInterruptSearch
from kalc.misc.object_factory import labelFactory

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

def test_load_requests():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    objects = filter(lambda x: isinstance(x, DaemonSet), k.state_objects)
    for p in objects:
        if p.metadata_name == "fluentd-elasticsearch":
            return
    raise ValueError("Could not find service loded")

def test_load_limits():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    objects = filter(lambda x: isinstance(x, DaemonSet), k.state_objects)
    for p in objects:
        if p.metadata_name == "fluentd-elasticsearch" and \
            p.cpuRequest > -1 and \
            p.memRequest > -1 and \
            p.memLimit > -1:
            return
    raise ValueError("Could not find service loded")

def test_limits_for_pods_created():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    objects = filter(lambda x: isinstance(x, Pod), k.state_objects)
    for p in objects:
        if str(p.metadata_name).startswith("fluentd-elasticsearch") and \
            p.cpuRequest > -1 and \
            p.memRequest > -1 and \
            p.memLimit > -1:
            return
    raise ValueError("Could not find service loded")

