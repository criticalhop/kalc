import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.DaemonSet import DaemonSet
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8SearchEviction
from guardctl.misc.object_factory import labelFactory

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
    pass

def test_requests_for_pods_created():
    pass