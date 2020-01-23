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
from kalc.cli import run


TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"
TEST_DEPLOYMENT = "./tests/test-deployment/deployment.yaml"
TEST_DEPLOYMENT1 = "./tests/test-deployment/deployment1.yaml"
TEST_DEPLOYMENT2 = "./tests/test-deployment/deployment2.yaml"

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_run_simple_dump():
    result = CliRunner().invoke(run, ["--from-dir", TEST_DEPLOYMENT_DUMP, "-o", "yaml", \
        "-t", "150", "--pipe", "-m", "scale", "--replicas" "10", "deployment/redis-master"])
    assert result.exit_code == 0

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_run_simple_create():
    result = CliRunner().invoke(run, ["-f", TEST_DEPLOYMENT, "-o", "yaml", \
        "-t", "150", "--pipe", "-m", "scale", "--replicas" "10", "deployment/redis-master"])
    assert result.exit_code == 0

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_run_simple_dump_create():
    result = CliRunner().invoke(run, ["--from-dir", TEST_DEPLOYMENT_DUMP, "-f", TEST_DEPLOYMENT1, "-o", "yaml", \
        "-t", "150", "--pipe", "-m", "scale", "--replicas" "10", "deployment/redis-master"])
    assert result.exit_code == 0

@pytest.mark.skip(reason="Scale doesn't support yet")
def test_run_simple_dump_create_harder():
    result = CliRunner().invoke(run, ["--from-dir", TEST_DEPLOYMENT_DUMP, "-f", TEST_DEPLOYMENT1, "-f", TEST_DEPLOYMENT2, "-o", "yaml", \
        "-t", "150", "--pipe", "-m", "scale", "--replicas" "10",  "deployment/redis-master", "deployment/redis-master1"])
    assert result.exit_code == 0