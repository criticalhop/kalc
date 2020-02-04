import pytest
import yaml
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.system.Scheduler import Scheduler
from kalc.misc.const import *
from kalc.model.search import K8ServiceInterruptSearch
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
from tests.test_util import print_objects

@pytest.mark.skip(reason="FIXME")
def test_load_deployment():
    k = KubernetesCluster()
    k.load(open("./tests/client-cases/criticalhopmanifest_prefixed.yaml").read())
    k._build_state()
    print_objects(k.state_objects)
    # print(yaml.load_all(open("./tests/criticalhopmanifest.yaml").read(), Loader=yaml.FullLoader))
    # print(yaml.dump(yaml.load(open("./tests/criticalhopmanifest.yaml").read(), Loader=yaml.FullLoader)))
