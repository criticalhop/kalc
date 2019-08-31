import pytest
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.misc.const import *

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

def test_eviction_fromfiles():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k.run()