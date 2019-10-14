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

#replicas 3 cpu: 100m memory: 500Mi
DEPLOYMENT_NEW = "./tests/test-scenario/deployment/deployment-new.yaml"
DEPLOYMENT_NEW_WO_PRIO = "./tests/test-scenario/deployment/deployment-new-wo-priority.yaml"

DUMP = "./tests/test-scenario/deployment/dump"
# cpu = 940m * 2  memory = 2701496Ki + 2701504Ki
NODE1 = "./tests/test-scenario/deployment/dump/node1.yaml"
NODE2 = "./tests/test-scenario/deployment/dump/node2.yaml"
# pod cpu = 100m * 7 memory = 500m * 5
PODS = "./tests/test-scenario/deployment/dump/pods.yaml"
PODS_BIG = "./tests/test-scenario/deployment/dump/pods_big200.yaml"

# the same but one pon in pending TODO may me need to load from cluster
PODS_PENDING = "./tests/test-scenario/deployment/dump/pods_pending.yaml"
SERVICES = "./tests/test-scenario/deployment/dump/services.yaml"
REPLICASETS = "./tests/test-scenario/deployment/dump/replicasets.yaml"
PRIORITYCLASSES = "./tests/test-scenario/deployment/dump/priorityclass.yaml"
DEPLOYMENT = "./tests/test-scenario/deployment/dump/deployments.yaml"



# @pytest.mark.skip(reason="temporary skip")
def test_test():
    runner = CliRunner()
    result = runner.invoke(run, ["--from-dir", DUMP, "-f", DEPLOYMENT_NEW, "-o", "yaml", "--pipe"])
    
    global RESULT
    RESULT=result
    print(RESULT.output)
    assert result.exit_code == 0

@pytest.mark.skip(reason="temporary skip")
def test_AnyGoal():
    k = KubernetesCluster()
    k.load(open(NODE1).read())
    k.load(open(NODE2).read())
    k.load(open(PODS).read())
    k.load(open(PODS_BIG).read())
    
    # k.load(open(PODS_PENDING).read())
    k.load(open(SERVICES).read())
    k.load(open(REPLICASETS).read())
    k.load(open(PRIORITYCLASSES).read())
    k.load(open(DEPLOYMENT).read())
    k.create_resource(open(DEPLOYMENT_NEW).read())
    k._build_state()
    p = AnyGoal(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
    # print_objects(k.state_objects)
    print_objects(k.state_objects)
    p.run(timeout=360, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)
