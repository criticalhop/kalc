import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from guardctl.cli import run


TEST_DEPLOYMENT_DUMP = "./tests/test-deployment/dump"

@pytest.mark.skip(reason="covered by above")
def test_run_simple():
    result = CliRunner().invoke(run, ["--from-dir", TEST_DEPLOYMENT_DUMP, "-o", "yaml", \
        "-t", "150", "--pipe"])
    assert result.exit_code == 0