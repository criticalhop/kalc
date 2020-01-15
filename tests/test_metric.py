import pytest
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Deployment import Deployment
from kalc.misc.metrics import Metric

def test_fault_toleranse():
    k = KubernetesCluster()
    nodes = []
    rangeMax = 100
    for n in range(rangeMax):
        node = Node()
        nodes.append(node)
        k.state_objects.append(node)

    for d in range(rangeMax):
        deployment = Deployment()
        k.state_objects.append(deployment)
        for p in range(d):
            pod = Pod()
            k.state_objects.append(pod)
            pod.atNode = nodes[p]
            deployment.podList.add(pod)
        for p in range(d, rangeMax):
            pod = Pod() 
            k.state_objects.append(pod)
            pod.atNode = nodes[d]
            deployment.podList.add(pod)

    metric = Metric(k.state_objects)
    metric.faultTolerance()

    idx = 0
    print("\nfaultToleranceSquare\n")
    for mS in metric.faultToleranceSquare:
        print("{0} - {1} : ".format(idx,mS))
        idx +=1
    
    idx = 0
    print("\nfaultToleranceGeom\n") 
    for mS in metric.faultToleranceGeom:
        print("{0} - {1} : ".format(idx,mS))
        idx +=1 
    
    print("\n")
