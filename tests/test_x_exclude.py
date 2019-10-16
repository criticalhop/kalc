from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest
import yaml
from guardctl.model.scenario import Scenario
from tests.test_util import print_objects

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

@pytest.mark.skip(reason="temporary skip")
def test_assert_ServUce():
    # try:
    #     run(["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
    #      "-t", "150", "-e",  "Service:redis-master-evict,ServUc1e:redis-master"])
    # except AssertionError as e:
    #     print(str(e))
    #     assert str(e) == "Error: no such type 'Servic1e'"
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master-evict,ServUce:redis-master"])
    assert result.__str__() == "<Result AssertionError(\"Error: no such type \'ServUce\'\")>"

@pytest.mark.skip(reason="temporary skip")
def test_assert_mUster():
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master-evict,Service:redis-mUster"])
    assert result.__str__() == "<Result AssertionError(\"Error: no such Service: \'redis-mUster\'\")>"

@pytest.mark.skip(reason="temporary skip")
def test_ignore_check_mUster():
    #  run(["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
    #      "-t", "150", "-e",  "Service:redis-master-evict,ServUc1e:redis-mUster","--ignore-nonexistent-exclusions"])
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master-evict,Service:redis-mUster","--ignore-nonexistent-exclusions"])
    assert result.exit_code == 0

@pytest.mark.skip(reason="temporary skip")
def test_excluded_search():
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master-evict,Service:redis-master", "--pipe"])
    assert result.exit_code == 0
    yaml.load(result.output)
    assert not("redis-master\n" in result.output[-200:])
    assert not("redis-master-evict\n" in result.output[-200:])

@pytest.mark.skip(reason="temporary skip")
def test_exclude_all_services():
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master,Service:redis-master-evict,Service:default-http-backend,Service:redis-slave", "--pipe"])
    # run( ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
    #     "-t", "150", "-e",  "Service:redis-master,Service:redis-master-evict,Service:default-http-backend,Service:redis-slave", "--pipe"])
    assert result.exit_code == 0
    assert "Empty scenario" in result.output

@pytest.mark.skip(reason="temporary skip")
def test_exclude_all_services_except_redis_slave():
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master,Service:redis-master-evict,Service:default-http-backend", "--pipe"])
    # run( ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
    #     "-t", "150", "-e",  "Service:redis-master,Service:redis-master-evict,Service:default-http-backend,Service:redis-slave", "--pipe"])
    assert result.exit_code == 0
    print(result.output)
    assert "name: redis-slave" in result.output

def test_exclude_regexp():
    result = CliRunner().invoke(run, ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
        "-t", "650", "-e",  "Service:redis-master*", "--pipe"])
    # run( ["--from-dir", TEST_CLUSTER_FOLDER, "-f", TEST_DAEMONET, "-o", "yaml", \
    #     "-t", "150", "-e",  "Service:redis-master,Service:redis-master-evict,Service:default-http-backend,Service:redis-slave", "--pipe"])
    # assert result.exit_code == 0
    print(result.output)
    # assert "name: redis-master" in result.output

