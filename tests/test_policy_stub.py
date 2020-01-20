from kalc.interactive import *
from libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode

from test_util import print_objects
from libs_for_tests import prepare_yamllist_for_diff
from kalc.model.search import HypothesisysNode, OptimisticRun
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.kubernetes import KubernetesCluster
from kalc.misc.const import *
import pytest
import inspect
from kalc.model.search import *
from kalc.misc.object_factory import labelFactory
from click.testing import CliRunner
from kalc.model.scenario import Scenario
from poodle import planned
from libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from typing import Set



def build_running_pod_with_d(podName, cpuRequest, memRequest, atNode, d, ds, s, pods):
    pod_running_1 = Pod()
    pod_running_1.metadata_name = "pod"+str(podName)
    pod_running_1.cpuRequest = cpuRequest
    pod_running_1.memRequest = memRequest
    pod_running_1.cpuLimit = 1
    pod_running_1.memLimit = 1
    pod_running_1.atNode = atNode
    pod_running_1.status = STATUS_POD["Running"]
    pod_running_1.hasDeployment = False
    pod_running_1.hasService = False
    pod_running_1.hasDaemonset = False
    atNode.currentFormalCpuConsumption += cpuRequest
    atNode.currentFormalMemConsumption += memRequest
    atNode.amountOfActivePods += 1
    pods.append(pod_running_1)
    if d is not None:
        d.podList.add(pod_running_1)
        d.amountOfActivePods += 1
        pod_running_1.hasDeployment = True
    if ds is not None:
        ds.podList.add(pod_running_1)
        ds.amountOfActivePods += 1
        pod_running_1.hasDaemonset = True
    if s is not None:
        pod_running_1.hasService = True
        s.podList.add(pod_running_1)
        s.amountOfActivePods += 1
        s.status = STATUS_SERV["Started"]
    return pod_running_1

def test_stub_completion():
    # create elementary cluster
    # render cluster
    # update with rendered cluster
    # add stub policy
    # run, get solution (empty?)
    k = KubernetesCluster()

    nodes = []
    pods = []
    node_item = Node()
    node_item.metadata_name = "node 1"
    node_item.cpuCapacity = 25
    node_item.memCapacity = 25
    node_item.isNull = False
    node_item.status = STATUS_NODE["Active"]
    nodes.append(node_item)
    # Service to detecte eviction
    s1 = Service()
    s1.metadata_name = "test-service"
    s1.amountOfActivePods = 0
    s1.isSearched = True
    d = Deployment()
    d.spec_replicas = 6    
    d.NumberOfPodsOnSameNodeForDeployment = 4
    pod = build_running_pod_with_d(1,2,2,node_item,d,None,s1,pods)
    k.state_objects.extend(nodes)
    k.state_objects.extend(pods)
    yamlState = convert_space_to_yaml(k.state_objects, wrap_items=True)
    update(''.join(yamlState))
    cluster = next(filter(lambda x: isinstance(x, GlobalVar), kalc_state_objects))
    cluster.policy.stub = True
    run()

