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
deployment1_5_100_100_h = "./tests/test-scenario/test_data/deployment1_5_100_100_h.yaml"
deployment2_5_100_100_z = "./tests/test-scenario/test_data/deployment2_5_100_100_z.yaml"
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

DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY = [priorityclass,\
                                        nodes1_2_940_2700,\
                                        pods_1_100_100_h,\
                                        pods_1_100_100_h_s1,\
                                        pods_1_100_100_z,\
                                        pods_1_100_100_z_s1,\
                                        pods_1_100_100_z_s2,\
                                        pods_1_500_1000_h,\
                                        pods_1_500_1000_h_s1,\
                                        pods_1_500_1000_z,\
                                        pods_1_500_1000_z_s1,\
                                        pods_1_500_1000_z_s2,\
                                        service1,\
                                        service2]
CHANGE_DEPLOYMENT_HIGH = [deployment1_5_100_100_h]
CHANGE_DAEMONSET_HIGH = [daemonset1_500_1000_h]
CHANGE_DEPLOYMENT_ZERO = [deployment2_5_100_100_z]

def calculate_variable_dump(DUMP_local):
    DUMP_with_command = []
    for dump_item in DUMP_local:
        DUMP_with_command.append("--dump-file")
        DUMP_with_command.append(dump_item)
    return DUMP_with_command

def calculate_variable_change(CHANGE_local):
    CHANGE_with_command = []
    for change_item in CHANGE_local:
        CHANGE_with_command.extend(["-f"])
        CHANGE_with_command.extend([change_item])
    CHANGE_with_command.extend(["-o", "yaml", "-t", "650","--pipe"])
    return CHANGE_with_command

def run_wo_cli(DUMP_local,CHANGE_local):
    k = KubernetesCluster()
    for dump_item in DUMP_local:
        k.load(open(dump_item).read())
    for change_item in CHANGE_local:
        k.create_resource(open(change_item).read())
    k._build_state()
    p = AnyGoal(k.state_objects)
    print_objects(k.state_objects)
    p.run(timeout=660, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)

def run_cli_directly(DUMP_with_command_local,CHANGE_with_command_local):
    k = KubernetesCluster()
    args = []
    args.extend(calculate_variable_dump(DUMP_with_command_local))
    args.extend(calculate_variable_change(CHANGE_DEPLOYMENT_HIGH))
    run(args)

def run_cli_invoke(DUMP_with_command_local,CHANGE_with_command_local):
    runner = CliRunner()
    args=[]
    args.extend(calculate_variable_dump(DUMP_with_command_local))
    args.extend(calculate_variable_change(CHANGE_DEPLOYMENT_HIGH))
    result = runner.invoke(run,args)
    print(result.output)
    assert result.exit_code == 0