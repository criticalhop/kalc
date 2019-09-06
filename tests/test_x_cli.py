from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

# def test_direct():
#     run(["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml"])

# @pytest.mark.skip(reason="covered by above")
def test_load_from_dir():
    runner = CliRunner()
    result = runner.invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml"])
    assert result.exit_code == 0
    assert "redis-master-evict" in result.output
