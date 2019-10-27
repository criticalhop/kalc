from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest

from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.search import Check_services
from tests.libs_for_tests import convert_space_to_yaml
from guardctl.model.scenario import Scenario
from tests.test_util import print_objects

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

# def test_direct():
    # run(["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml"])  # pylint: disable=no-value-for-parameter

# To debug eviction test, we need:
# 1. Create the eviction problem with synthetic method, solve
# 2. Dump the problem, solve from files
# 3. Solve from real cluster dump

def test_anyservice_interrupted_fromfiles():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    yamlState = convert_space_to_yaml(k.state_objects)
    for y in yamlState: print(y)

    # mark_excluded_service(k.state_objects)
    p = Check_services(k.state_objects)
    print_objects(k.state_objects)
    p.run(timeout=6600, sessionName="test_anyservice_interrupted_fromfiles")
    if not p.plan:
        raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())

RESULT=""

# @pytest.mark.skip(reason="covered by above")
def test_load_from_dir():
    runner = CliRunner()
    result = runner.invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", "--pipe", "--timeout", "100"])
    assert result.exit_code == 0
    global RESULT
    RESULT=result
    print(RESULT.output)

#@pytest.mark.skip(reason="specific scenario is not selected")
def test_result_any_scenario():
    assert "redis-master" in RESULT.output

# @pytest.mark.skip(reason="need to find a way to trigger no-tty mode")
def test_result_readable():
    import yaml
    yaml.load(RESULT.output)

# @pytest.mark.skip(reason="need to find a way to trigger no-tty mode")
# def test_result_specific_senario():
#     assert "redis-master-evict" in RESULT.output
