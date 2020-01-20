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
        # print(node.metadata_name)

    for d in range(1, deploymentRange):
        deployment = Deployment()
        k.state_objects.append(deployment)
        # print("d num ", d)
        for p in range(d):
            pod = Pod()
            pod.currentRealCpuConsumption = 1
            pod.currentRealMemConsumption = 1
            k.state_objects.append(pod)
            pod.atNode = nodes[p]
            nodes[p].currentRealCpuConsumption += 1
            nodes[p].currentRealMemConsumption += 1
            deployment.podList.add(pod)
        for p in range(10):
            pod = Pod()
            pod.currentRealCpuConsumption = 1
            pod.currentRealMemConsumption = 1
            k.state_objects.append(pod)
            pod.atNode = nodes[d]
            nodes[p].currentRealCpuConsumption += 1
            nodes[p].currentRealMemConsumption += 1
            deployment.podList.add(pod)
        # for i in deployment.podList._get_value():
        #     print("id ", i.atNode._property_value)

    metric = Metric(k.state_objects)
    metric.setUnusedRes()
    metric.faultTolerance()

    deployments = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    idx = 0
    print("\nfaultTolerancesquare\n") 
    testMetric = [0.9136250564655354, 0.8416254115301732, 0.7806839665455554, 0.7284313590846836, 0.6831300510639732, 0.6434768838116876, 0.6084753195758, 0.5773502691896258, 0.54948981625845]
    for idx, mS in enumerate(deployments):
        print("{0} - {1}".format(idx,mS.metric))
        assert mS.metric == testMetric[idx]
    
    # metric.nodeOverSubscribe()


    


