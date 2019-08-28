import pytest
from guardctl.model.kubernetes import KubernetesCluster

TEST_PODS = "./tests/kube-config/pods.yaml"
TEST_NODES = "./tests/kube-config/nodes.yaml"
TEST_DEPLOYMENTS = "./tests/kube-config/deployments.yaml"

@pytest.mark.skip(reason="no way of currently testing this")
def test_load_pods():
    k = KubernetesCluster()
    k.load_state(open(TEST_PODS).read())
    k.build_state()
    assert k.state_objects

@pytest.mark.skip(reason="no way of currently testing this")
def test_load_nodes():
    k = KubernetesCluster()
    k.load_state(open(TEST_NODES).read())
    k.build_state()
    assert k.state_objects

@pytest.mark.skip(reason="no way of currently testing this")
def test_load_nodes():
    k = KubernetesCluster()
    k.load_state(open(TEST_NODES).read())
    k.load_state(open(TEST_PODS).read())
    k.load_state(open(TEST_DEPLOYMENTS).read())
    k.build_state()
    assert k.state_objects
