import pytest
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.misc.const import *

TEST_PODS = "./tests/kube-config/pods.yaml"
TEST_NODES = "./tests/kube-config/nodes.yaml"
TEST_DEPLOYMENTS = "./tests/kube-config/deployments.yaml"

def test_load_pods():
    k = KubernetesCluster()
    k.load(open(TEST_PODS).read())
    k._build_state()
    assert k.state_objects

def test_load_nodes():
    k = KubernetesCluster()
    k.load(open(TEST_NODES).read())
    k._build_state()
    assert k.state_objects

def test_load_nodes():
    k = KubernetesCluster()
    k.load(open(TEST_NODES).read())
    k.load(open(TEST_PODS).read())
    k.load(open(TEST_DEPLOYMENTS).read())
    k._build_state()
    assert k.state_objects

def test_load_pods_new():
    k = KubernetesCluster()
    k.load(open(TEST_PODS).read())
    k._build_state()
    # TODO: check if pod is fully loaded
    pod = k.state_objects[0]
    assert isinstance(pod, Pod)
    assert len(pod.metadata_labels._get_value()) > 0
    assert pod.status == STATUS_POD_PENDING
    assert pod.status == STATUS_POD_RUNNING

    assert k.state_objects