from kalc.misc.cli_optimize import optimize_cluster
import sys
sys.path.append('./tests/')
from test_util import print_objects
from libs_for_tests import prepare_yamllist_for_diff
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
from libs_for_tests import convert_space_to_yaml_dump,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
import kalc.misc.util
from typing import Set

DEBUG_MODE = 2 # 0 - no debug,  1- debug with yaml load , 2 - debug without yaml load

TEST_DUMP = "/home/vasily/artem/kalc/tests/client-cases/tesg1.yaml"

def test_optimmize_cluster_real():
    assert optimize_cluster(open(TEST_DUMP).read(), runs=2)