from kalc.misc.script_generator import move_pod_with_deployment_script, move_pod_with_deployment_script_simple 
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.ReplicaSet import ReplicaSet
from kalc.model.system.primitives import Label
from kalc.model.search import Balance_pods_and_drain_node
from kalc.model.kubernetes import KubernetesCluster
from kalc.misc.const import *
import pytest

@pytest.mark.skip(reason="FIXME")
def test_move_pod_generation_works():
    p = Pod()
    p.metadata_name = "test-pod-1"
    n = Node()
    l1 = Label("a:b")
    l1.key = "a"
    l1.value = "b"
    l2 = Label("c:d")
    l2.key = "c"
    l2.value = "b"
    n.metadata_labels.add(l1)
    n.metadata_labels.add(l2)

    d = Deployment()
    d.metadata_name = "dep-test1"
    d.podList.add(p)
    p.hasDeployment = True

    rs = ReplicaSet()
    rs.metadata_name = "rs-test1"
    # typically, you can find correct replicaSet by ownerReferences
    # TODO: create utililty function to do that 

    print(move_pod_with_deployment_script(p, n, d, rs))
    

@pytest.mark.skip(reason="FIXME")
def test_get_deployment():
    p = Pod()
    p.metadata_name = "test-pod-1"
    n = Node()
    l1 = Label("a:b")
    l1.key = "a"
    l1.value = "b"
    l2 = Label("c:d")
    l2.key = "c"
    l2.value = "b"
    n.metadata_labels.add(l1)
    n.metadata_labels.add(l2)

    d = Deployment()
    d.metadata_name = "dep-test1"
    d.podList.add(p)
    p.hasDeployment = True

    rs = ReplicaSet()
    rs.metadata_name = "rs-test1"
    rs.metadata_ownerReferences__name = "dep-test1"
    # typically, you can find correct replicaSet by ownerReferences
    # TODO: create utililty function to do that 

    # print(move_pod_with_deployment_script_simple(p, n, [d, n, p, rs])) # E: 64,10: No value for argument 'object_space' in function call (no-value-for-parameter)
    

@pytest.mark.skip(reason="FIXME")
def test_get_fullscript():
    k = KubernetesCluster()
    p = Pod()
    p.status = STATUS_POD["Running"]
    p.metadata_name = "test-pod-1"
    p.cpuRequest = 2
    p.memRequest = 2
    n_orig = Node("orgi")
    n = Node()
    p.nodeSelectorList.add(n)
    n_orig.metadata_name = "ORIG"
    n_orig.currentFormalMemConsumption = 5
    n_orig.currentFormalCpuConsumption = 5
    n.status = STATUS_NODE["Active"]
    n.cpuCapacity = 10
    n.memCapacity = 10
    l1 = Label("a:b")
    l1.key = "a"
    l1.value = "b"
    l2 = Label("c:d")
    l2.key = "c"
    l2.value = "b"
    n.metadata_labels.add(l1)
    n.metadata_labels.add(l2)

    d = Deployment()
    d.metadata_name = "dep-test1"
    d.podList.add(p)
    p.hasDeployment = True
    p.atNode = n_orig

    rs = ReplicaSet()
    rs.metadata_name = "rs-test1"
    rs.metadata_ownerReferences__name = "dep-test1"
    # typically, you can find correct replicaSet by ownerReferences
    # TODO: create utililty function to do that 

    k.state_objects.extend([d, n, p, rs])

    prob = Balance_pods_and_drain_node(k.state_objects)
    s = k.scheduler
    g = k.globalvar
    prob.MoveRunningPodToAnotherNode(p, n_orig, n, s, g)

    assert len(prob.script)

    


