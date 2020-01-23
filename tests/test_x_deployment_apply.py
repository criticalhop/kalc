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

TEST_DEPLOYMENT_repl10 = "./tests/test-deployment/deployment_repl10.yaml"
TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"

def test_create_n_apply():
    result = CliRunner().invoke(run, ["--from-dir", TEST_DEPLOYMENT_DUMP, "-f",TEST_DEPLOYMENT_repl10, "-o", "yaml", \
        "-t", "150", "--pipe", "-m", "apply"])
    assert result.exit_code == 0