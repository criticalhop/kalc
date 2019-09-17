from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest
import yaml

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

# @pytest.mark.skip(reason="covered by above")
def test_load_from_dir():
    # run(["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
    #      "-t", "150", "-e",  "Service:redis-master-evict,Service:redis-master"])
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "150", "-e",  "Service:redis-master-evict,Service:redis-master"])
    assert result.exit_code == 0
    yaml.load(result.output)
    print(result.output)
    assert not("redis-master\n" in result.output[-200:])
    assert not("redis-master-evict\n" in result.output[-200:])
