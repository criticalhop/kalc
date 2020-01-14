from kalc.misc.script_generator import move_pod_with_deployment_script, move_pod_with_deployment_script_simple 
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.ReplicaSet import ReplicaSet
from kalc.model.system.primitives import Label

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

    print(move_pod_with_deployment_script_simple(p, n, [d, n, p, rs]))
    

