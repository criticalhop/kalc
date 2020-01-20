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
import kalc.misc.util as util

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
