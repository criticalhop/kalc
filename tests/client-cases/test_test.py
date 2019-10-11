import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from tests.test_util import print_objects

def test_load_deployment():
    k = KubernetesCluster()
    k.load(open("./tests/client-cases/criticalhopmanifest_prefixed.yaml").read())
    k._build_state()
    print_objects(k.state_objects)
    # print(yaml.load_all(open("./tests/criticalhopmanifest.yaml").read(), Loader=yaml.FullLoader))
    # print(yaml.dump(yaml.load(open("./tests/criticalhopmanifest.yaml").read(), Loader=yaml.FullLoader)))
