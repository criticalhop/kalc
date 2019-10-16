import pytest
import yaml
import sys
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.search import AnyGoal
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario
import guardctl.model.kinds.Service as mservice
from tests.test_util import print_objects
import guardctl.model.kinds.Pod as mpod
from guardctl.cli import run
import click
from click.testing import CliRunner
from poodle import planned
from guardctl.model.scenario import ScenarioStep, describe
from guardctl.model.system.globals import GlobalVar
 

daemonset1_100_100_h = "./tests/test-scenario/test_data/daemonset1_100_100_h.yaml"
daemonset1_500_1000_h = "./tests/test-scenario/test_data/daemonset1_500_1000_h.yaml"
deployment1_5_100_100_z = "./tests/test-scenario/test_data/deployment1_5_100_100_z.yaml"
deployment2_5_100_100_h = "./tests/test-scenario/test_data/deployment2_5_100_100_h.yaml"
node1 = "./tests/test-scenario/test_data/node1.yaml"
node2 = "./tests/test-scenario/test_data/node2.yaml"
nodes1_2_940_2700 = "./tests/test-scenario/test_data/nodes1_2_940_2700.yaml"
pods_1_100_100_h = "./tests/test-scenario/test_data/pods_1_100_100_h.yaml"
pods_1_100_100_h_s1 = "./tests/test-scenario/test_data/pods_1_100_100_h_s1.yaml"
pods_1_100_100_h_s2 = "./tests/test-scenario/test_data/pods_1_100_100_h_s2.yaml"
pods_1_100_100_z_s1 = "./tests/test-scenario/test_data/pods_1_100_100_z_s1.yaml"
pods_1_100_100_z_s2 = "./tests/test-scenario/test_data/pods_1_100_100_z_s2.yaml"
pods_1_100_100_z = "./tests/test-scenario/test_data/pods_1_100_100_z.yaml"
pods_1_500_1000_h = "./tests/test-scenario/test_data/pods_1_500_1000_h.yaml"
pods_1_500_1000_h_s1 = "./tests/test-scenario/test_data/pods_1_500_1000_h_s1.yaml"
pods_1_500_1000_h_s2 = "./tests/test-scenario/test_data/pods_1_500_1000_h_s2.yaml"
pods_1_500_1000_z = "./tests/test-scenario/test_data/pods_1_500_1000_z.yaml"
pods_1_500_1000_z_s1 = "./tests/test-scenario/test_data/pods_1_500_1000_z_s1.yaml"
pods_1_500_1000_z_s2 = "./tests/test-scenario/test_data/pods_1_500_1000_z_s2.yaml"
pods_5_100_100_h_d2 = "./tests/test-scenario/test_data/pods_5_100_100_h_d2.yaml"
pods_5_100_100_z_d1 = "./tests/test-scenario/test_data/pods_5_100_100_z_d1.yaml"
priorityclass = "./tests/test-scenario/test_data/priorityclass.yaml"
replicaset_for_deployment1 = "./tests/test-scenario/test_data/replicaset_for_deployment1.yaml"
replicaset_for_deployment2 = "./tests/test-scenario/test_data/replicaset_for_deployment2.yaml"
service1 = "./tests/test-scenario/test_data/service1.yaml"
service2 = "./tests/test-scenario/test_data/service2.yaml"

