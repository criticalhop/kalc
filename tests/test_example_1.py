from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest
import yaml
EXAMPLE_FOLDER = "./EXAMPLES/daemonset_eviction_small/"


def test_example_1():
    run(["cd",EXAMPLE_FOLDER])
    run("kubectl apply -f ./deployment.yaml")
    run("sleep 10")
    run("kubectl get deployments")
    run("rm -R ./cluster_dump/")
    run("kubectl get po -o yaml > ./cluster_dump/pods.yaml")
    run("kubectl get no -o yaml > ./cluster_dump/nodes.yaml")
    run("kubectl get services -o yaml > ./cluster_dump/service.yaml")
    run("kubectl get priorityclass -o yaml > ./cluster_dump/priorityclass.yaml")
    result = run("kubectl val -d ./cluster_dump/ -f ./daemonset_create.yaml")
    assert result.exit_code == 0
    print(result.output)