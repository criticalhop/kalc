import pytest
from guardctl.model.kubernetes import KubernetesCluster

TEST_PODS = "./tests/kube-config/pods.yaml"

def test_load_pods():
    k = KubernetesCluster()
    k.load_conf(open(TEST_PODS).read())


