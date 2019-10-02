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
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
import guardctl.misc.util as util

TEST_CLUSTER_FOLDER = "./tests/test-daemonset/dump"
TEST_DAEMONSET_APPLY = "./tests/test-daemonset/daemonset_apply.yaml"

def test_load():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    objects = filter(lambda x: isinstance(x, DaemonSet), k.state_objects)
    for p in objects:
        if p.metadata_name == "fluentd-elasticsearch":
            assert p.cpuRequest._get_value() == util.cpuConvertToAbstractProblem("400m")
            assert p.memRequest._get_value() == util.memConvertToAbstractProblem("400Mi")
            assert p.memLimit._get_value() == util.memConvertToAbstractProblem("400Mi")
            return
    raise ValueError("Could not find service loded")

def test_load_create():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.apply_resource(open(TEST_DAEMONSET_APPLY).read())
    k._build_state()
    objects = filter(lambda x: isinstance(x, DaemonSet), k.state_objects)
    for p in objects:
        if p.metadata_name == "fluentd-elasticsearch":
            assert len(util.objDeduplicatorByName(p.podList._get_value())) == 2
            assert p.cpuRequest._get_value() == util.cpuConvertToAbstractProblem("10m")
            assert p.memRequest._get_value() == util.memConvertToAbstractProblem("10Mi")
            assert p.memLimit._get_value() == util.memConvertToAbstractProblem("10Mi")
            return
    raise ValueError("Could not find service loded")
