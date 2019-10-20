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

import logging
import logzero
from logzero import logger

# This log message goes to the console
logger.debug("hello")
# Set a minimum log level
logzero.loglevel(logging.INFO)
# Set a minimum log level
logzero.loglevel(logging.INFO)

# You can also set a different loglevel for the file handler
logzero.logfile("./logs/log.log")
logzero.logfile("./logs/loginfo.log", loglevel=logging.INFO)
logzero.logfile("./logs/loginfo.log", loglevel=logging.ERROR)

# Set a custom formatter
formatter = logging.Formatter('%(name)s - %(asctime)-15s - %(levelname)s: %(message)s');
logzero.formatter(formatter)

# Log some variables
# logger.info("var1: %s, var2: %s", var1, var2)

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONSET = "./tests/daemonset_eviction/daemonset_create.yaml"


daemonset1_100_100_h = "./tests/test-scenario/test_data/daemonset1_100_100_h.yaml"
daemonset1_500_1000_h = "./tests/test-scenario/test_data/daemonset1_500_1000_h.yaml"
daemonset3_500_1000_z = "./tests/test-scenario/test_data/daemonset3_500_1000_z.yaml"
daemonset4_300_300_h = "./tests/test-scenario/test_data/daemonset4_300_300_h.yaml"

deployment1_5_100_100_h = "./tests/test-scenario/test_data/deployment1_5_100_100_h.yaml"
deployment2_5_100_100_z = "./tests/test-scenario/test_data/deployment2_5_100_100_z.yaml"
deployment3_5_100_100_z = "./tests/test-scenario/test_data/deployment3_5_100_100_z_s3.yaml"

node1_3200_3200 = "./tests/test-scenario/test_data/node1_3200_3200.yaml"
node2_3200_3200 = "./tests/test-scenario/test_data/node2_3200_3200.yaml"
node3_3200_3200 = "./tests/test-scenario/test_data/node3_3200_3200.yaml"

pods1_1_100_100_h_n2 = "./tests/test-scenario/test_data/pods1_1_100_100_h_n2.yaml"
pods2_1_100_100_h_s1_n2 = "./tests/test-scenario/test_data/pods2_1_100_100_h_s1_n2.yaml"
pods3_1_100_100_h_s2_n2 = "./tests/test-scenario/test_data/pods3_1_100_100_h_s2_n2.yaml"
pods4_1_100_100_z_n2 = "./tests/test-scenario/test_data/pods4_1_100_100_z_n2.yaml"
pods5_1_100_100_z_s1_n1 = "./tests/test-scenario/test_data/pods5_1_100_100_z_s1_n1.yaml"
pods6_1_100_100_z_s2_n2 = "./tests/test-scenario/test_data/pods6_1_100_100_z_s2_n2.yaml"
pods7_1_1000_1000_h_n1 = "./tests/test-scenario/test_data/pods7_1_1000_1000_h_n1.yaml"
pods8_1_1000_1000_h_s1_n2 = "./tests/test-scenario/test_data/pods8_1_1000_1000_h_s1_n2.yaml"
pods9_1_1000_1000_h_s2_n2 = "./tests/test-scenario/test_data/pods9_1_1000_1000_h_s2_n2.yaml"
pods10_1_1000_1000_z_n2 = "./tests/test-scenario/test_data/pods10_1_1000_1000_z_n2.yaml"
pods11_1_1000_1000_z_s1_n1 = "./tests/test-scenario/test_data/pods11_1_1000_1000_z_s1_n1.yaml"
pods12_1_1000_1000_z_s2_n2 = "./tests/test-scenario/test_data/pods12_1_1000_1000_z_s2_n2.yaml"
pods13_5_100_100_h_d1_2n1_1n2_2n3 = "./tests/test-scenario/test_data/pods13_5_100_100_h_d1_2n1_1n2_2n3.yaml"
pods14_5_100_100_z_d2_3n1_2n3 = "./tests/test-scenario/test_data/pods14_5_100_100_z_d2_3n1_2n3.yaml"
pods15_5_100_100_z_d3_2n2_3n3 = "./tests/test-scenario/test_data/pods15_5_100_100_z_d3_2n2_3n3.yaml"
pods16_1_1000_1000_h_s1_n2 = "./tests/test-scenario/test_data/pods16_1_1000_1000_h_s1_n2.yaml"
pods17_1_1000_1000_z_s1_n1 = "./tests/test-scenario/test_data/pods17_1_1000_1000_z_s1_n1.yaml"
pods18_5_100_100_z_d2_3n1_2n2 = "./tests/test-scenario/test_data/pods18_5_100_100_z_d2_3n1_2n2.yaml"

priorityclass = "./tests/test-scenario/test_data/priorityclass.yaml"
replicaset_for_deployment1 = "./tests/test-scenario/test_data/replicaset_for_deployment1.yaml"
replicaset_for_deployment2 = "./tests/test-scenario/test_data/replicaset_for_deployment2.yaml"
replicaset_for_deployment3 = "./tests/test-scenario/test_data/replicaset_for_deployment3.yaml"
service1 = "./tests/test-scenario/test_data/service1.yaml"
service2 = "./tests/test-scenario/test_data/service2.yaml"
service3 = "./tests/test-scenario/test_data/service3.yaml"

DUMP1_S1_H_S2_Z_FREE_200 = [priorityclass,\
                            node1_3200_3200,\
                            node2_3200_3200,\
                            pods7_1_1000_1000_h_n1,\
                            pods11_1_1000_1000_z_s1_n1,\
                            pods17_1_1000_1000_z_s1_n1,\
                            pods8_1_1000_1000_h_s1_n2,\
                            pods12_1_1000_1000_z_s2_n2,\
                            pods16_1_1000_1000_h_s1_n2,\
                            service1,\
                            service2]
DUMP1_S1_H_S2_Z_FREE_200_WITH_D2=DUMP1_S1_H_S2_Z_FREE_200
DUMP1_S1_H_S2_Z_FREE_200_WITH_D2.extend([deployment2_5_100_100_z,\
                                        replicaset_for_deployment2,\
                                        pods18_5_100_100_z_d2_3n1_2n2])

DUMP1_S1_H_S2_Z_FREE_200_WITH_DAEMONSET_ZERO=DUMP1_S1_H_S2_Z_FREE_200
DUMP1_S1_H_S2_Z_FREE_200_WITH_DAEMONSET_ZERO.extend([daemonset3_500_1000_z])

CHANGE_DEPLOYMENT_HIGH = [deployment1_5_100_100_h]
CHANGE_DAEMONSET_HIGH = [daemonset4_300_300_h]
CHANGE_DEPLOYMENT_ZERO = [deployment2_5_100_100_z]
CHANGE_DEPLOYMENT_ZERO_WITH_SERVICE = [deployment3_5_100_100_z,replicaset_for_deployment3,service3]

def calculate_variable_dump(DUMP_local):
    DUMP_with_command = []
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            DUMP_with_command.extend(["--dump-file"])
            DUMP_with_command.extend([dump_item])
    return DUMP_with_command

def calculate_variable_change(CHANGE_local):
    CHANGE_with_command = []
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            CHANGE_with_command.extend(["-f"])
            CHANGE_with_command.extend([change_item])
    CHANGE_with_command.extend(["-o", "yaml", "-t", "650","--pipe"])
    return CHANGE_with_command

def run_wo_cli(DUMP_local,CHANGE_local):
    k = KubernetesCluster()
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            k.load(open(dump_item).read())
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            k.create_resource(open(change_item).read())
    k._build_state()
    p = AnyGoal(k.state_objects)
    logger.info("---- run_wo_cli:")
    logger.info("----- print_objects before run: ----------")
    logger.info(print_objects(k.state_objects))

    p.run(timeout=6600, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    logger.info("---- Scenario:")
    logger.info(Scenario(p.plan).asyaml())
    logger.info("----- print_objects after run: ----------")
    logger.info(print_objects(k.state_objects))

def run_dir_wo_cli(DUMP_local,CHANGE_local):
    k = KubernetesCluster()
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            k.load_dir(dump_item)
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            k.create_resource(open(change_item).read())
    k._build_state()
    p = AnyGoal(k.state_objects)
    logger.info("---- run_wo_cli:")
    logger.info("----- print_objects before run: ----------")
    logger.info(print_objects(k.state_objects))

    p.run(timeout=6600, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    logger.info("---- Scenario:")
    logger.info(Scenario(p.plan).asyaml())
    logger.info("----- print_objects after run: ----------")
    logger.info(print_objects(k.state_objects))

def run_cli_directly(DUMP_with_command_local,CHANGE_with_command_local):
    k = KubernetesCluster()
    args = []
    args.extend(calculate_variable_dump(DUMP_with_command_local))
    args.extend(calculate_variable_change(CHANGE_DEPLOYMENT_HIGH))
    print(">>args>>", args)
    run(args) # pylint: disable=no-value-for-parameter

def run_cli_invoke(DUMP_with_command_local,CHANGE_with_command_local):
    runner = CliRunner()
    args=[]
    args.extend(calculate_variable_dump(DUMP_with_command_local))
    args.extend(calculate_variable_change(CHANGE_DEPLOYMENT_HIGH))
    result = runner.invoke(run,args)
    logger.info("---- run_cli_invoke:")
    logger.info(result.output)
    assert result.exit_code == 0