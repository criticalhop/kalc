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
import kalc.misc.util as util

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DEPLOYMENT = "./tests/test-deployment/deployment.yaml"
TEST_DEPLOYMENT_repl10 = "./tests/test-deployment/deployment_repl10.yaml"
TEST_DEPLOYMENT_repl2 = "./tests/test-deployment/deployment_repl2.yaml"
TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"

def test_create_n_apply():
    k = KubernetesCluster()
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k.apply_resource(open(TEST_DEPLOYMENT_repl10).read())
    k._build_state()
    for p in filter(lambda x: isinstance(x, Deployment), k.state_objects):
        if p.metadata_name == "redis-master":
            if len(util.objDeduplicatorByName(p.podList._get_value())) != 10:
                raise ValueError("Wrong pods amount - {0} (10)".format(len(util.objDeduplicatorByName(p.podList._get_value()))))
            return
    raise ValueError("Could not find service loded")

def test_create_n_apply_less():
    k = KubernetesCluster()
    k.create_resource(open(TEST_DEPLOYMENT).read())
    k.apply_resource(open(TEST_DEPLOYMENT_repl2).read())
    k._build_state()
    for p in filter(lambda x: isinstance(x, Deployment), k.state_objects):
        if p.metadata_name == "redis-master":
            if len(util.objDeduplicatorByName(p.podList._get_value())) != 2.0:
                raise ValueError("Wrong pods amount - {0} (2)".format(len(util.objDeduplicatorByName(p.podList._get_value()))))
            return
    raise ValueError("Could not find service loded")

def test_load_n_apply():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.apply_resource(open(TEST_DEPLOYMENT_repl10).read())
    k._build_state()
    for p in filter(lambda x: isinstance(x, Deployment), k.state_objects):
        if p.metadata_name == "redis-master":
            # WARNING poodle bug p.podList._get_value() return list which 
            if len(util.objDeduplicatorByName(p.podList._get_value())) != 10.0:
                raise ValueError("Wrong pods amount - {0} (10)".format(len(util.objDeduplicatorByName(p.podList._get_value()))))
            for pod in p.podList._get_value():
                ok = False
                for label in pod.metadata_labels._get_value():
                    if label._get_value()[0:3] == "app":
                        ok = True
                        assert label._get_value() == "app:redis-custom"
                if not ok:
                    raise ValueError("Could not find renamed pod")
            return
    raise ValueError("Could not find service loded")

