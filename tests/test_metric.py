import pytest
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Deployment import Deployment
from kalc.misc.metrics import Metric

def test_faultTolerance():
    k = KubernetesCluster()
    nodes = []
    nodeRange = 20
    deploymentRange = 10
    for n in range(nodeRange):
        node = Node()
        node.memCapacity = 10
        node.cpuCapacity = 10
        nodes.append(node)
        k.state_objects.append(node)
        print(node.metadata_name)

    for d in range(1, deploymentRange):
        deployment = Deployment()
        k.state_objects.append(deployment)
        print("d num ", d)
        for p in range(d):
            pod = Pod()
            pod.currentRealCpuConsumption = 1
            pod.currentRealMemConsumption = 1
            k.state_objects.append(pod)
            pod.atNode = nodes[p]
            deployment.podList.add(pod)
            print("ff",d, nodes[p],id(nodes[p]))

        for p in range(10):
            pod = Pod()
            pod.currentRealCpuConsumption = 1
            pod.currentRealMemConsumption = 1
            k.state_objects.append(pod)
            pod.atNode = nodes[5]
            print("ff",d, nodes[5],id(nodes[5]),pod.atNode._value().metadata_name)

            deployment.podList.add(pod)
        for i in deployment.podList._get_value():
            print("id ", i.atNode)

    metric = Metric(k.state_objects)
    metric.faultTolerance()

    deployments = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    idx = 0
    print("\nfaultTolerancesquare\n") 
    for mS in deployments:
        print("{0} - {1}".format(idx,mS.metric))
        idx +=1 
    
    print("\n")
    raise "ff"


    


