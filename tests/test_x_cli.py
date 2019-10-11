from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

# def test_direct():
#     run(["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml"])

RESULT=""

# @pytest.mark.skip(reason="covered by above")
def test_load_from_dir():
    runner = CliRunner()
    result = runner.invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", "--pipe"])
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
