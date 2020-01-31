from kalc.misc.cli_optimize import optimize_cluster
import sys
sys.path.append('./tests/')
pass
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.kubernetes import KubernetesCluster
from kalc.misc.const import *
import pytest
import inspect
from kalc.model.search import *
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
from poodle import planned
from kalc.misc.util import split_yamldumps
from typing import Set
from tests.test_util import print_objects
# from libs_for_tests import convert_space_to_yaml_dump

def test_client_yaml():
    optimize_cluster(open("./tests/client_yaml.yaml").read())

