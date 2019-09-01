import pytest
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8SearchEviction
from guardctl.misc.object_factory import stringFactory, labelFactory
from  tests.problem.goals import *


TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"



def test_eviction_synthetic():
    p = TestServiceInterrupted()
    p.run()
    print(p.plan)
    if not p.plan: 
        print("Could not solve %s" % p.__class__.__name__)
    if p.plan:
        assert p.plan
