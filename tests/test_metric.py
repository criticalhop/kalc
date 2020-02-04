import pytest
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Deployment import Deployment
from kalc.misc.metrics import Metric
from kalc.misc.cli_optimize import optimize_cluster
import pytest

def test_faultTolerance():
    k = KubernetesCluster()
    nodes = []
    nodeRange = 10
    deploymentRange = 5
    for n in range(nodeRange):
        node = Node()
        node.memCapacity = 10
        node.cpuCapacity = 10
        nodes.append(node)
        k.state_objects.append(node)
        print(node.metadata_name._get_value())

    for d in range(1, deploymentRange):
        deployment = Deployment()
        k.state_objects.append(deployment)
        print("d num ", d)
        for p in range(d):
            pod = Pod()
            pod.currentFormalCpuConsumption = 1
            pod.currentFormalMemConsumption = 1
            k.state_objects.append(pod)
            pod.atNode = nodes[p]
            nodes[p].currentFormalCpuConsumption += 1
            nodes[p].currentFormalMemConsumption += 1
            deployment.podList.add(pod)
        for p in range(10):
            pod = Pod()
            pod.currentFormalCpuConsumption = 1
            pod.currentFormalMemConsumption = 1
            k.state_objects.append(pod)
            pod.atNode = nodes[d]
            nodes[p].currentFormalCpuConsumption += 1
            nodes[p].currentFormalMemConsumption += 1
            deployment.podList.add(pod)
        # for i in deployment.podList._get_value():
        #     print("id ", i.atNode._property_value)

    metric = Metric(k.state_objects)
    metric.setUnusedRes()
    metric.fault_tolerance()

    deployments = filter(lambda x: isinstance(x, Deployment), k.state_objects)
    idx = 0
    # print("\nDeployment faultTolerancesquare\n") 
    testMetric = [0.9136250564655354, 0.8416254115301732, 0.7806839665455554, 0.7284313590846836, 0.6831300510639732, 0.6434768838116876, 0.6084753195758, 0.5773502691896258, 0.54948981625845]
    for idx, mS in enumerate(deployments):
        # print("{0} {2} - {1}".format(idx, mS.metric, mS.metadata_name._get_value()))
        assert mS.metric == testMetric[idx]
    
    metric.nodeOverSubscribe()

    print("\nNode oversubscribe\n")
    testMetric = [0.8, 0.7, 0.6]
    nodes = filter(lambda x: isinstance(x, Node), k.state_objects)
    for idx, mS in list(enumerate(nodes))[:3]:
        # print("{0} {2} - {1}".format(idx, mS.oversubscribe, mS.metadata_name._get_value()))
        assert mS.oversubscribe == testMetric[idx]
    assert metric.deployment_fault_tolerance_metric == 0.816091448406487

def test_metric_pod_progressive_sum():
    k = KubernetesCluster()
    nodes = []
    for n in range(2):
        node = Node()
        node.memCapacity = 20
        node.cpuCapacity = 20
        nodes.append(node)
        k.state_objects.append(node)
 
    deployment = Deployment()
    k.state_objects.append(deployment)
    for p in range(3):
        pod = Pod()
        pod.currentFormalCpuConsumption = 1
        pod.currentFormalMemConsumption = 1
        k.state_objects.append(pod)
        pod.atNode = nodes[0]
        nodes[0].currentFormalCpuConsumption += 1
        nodes[0].currentFormalMemConsumption += 1
        deployment.podList.add(pod)

    deployment = Deployment()
    k.state_objects.append(deployment)
    for p in range(2):
        pod = Pod()
        pod.currentFormalCpuConsumption = 1
        pod.currentFormalMemConsumption = 1
        k.state_objects.append(pod)
        pod.atNode = nodes[0]
        nodes[0].currentFormalCpuConsumption += 1
        nodes[0].currentFormalMemConsumption += 1
        deployment.podList.add(pod)
    for p in range(2):
        pod = Pod()
        pod.currentFormalCpuConsumption = 1
        pod.currentFormalMemConsumption = 1
        k.state_objects.append(pod)
        pod.atNode = nodes[1]
        nodes[1].currentFormalCpuConsumption += 1
        nodes[1].currentFormalMemConsumption += 1
        deployment.podList.add(pod)

    deployment = Deployment()
    k.state_objects.append(deployment)
    for p in range(5):
        pod = Pod()
        pod.currentFormalCpuConsumption = 1
        pod.currentFormalMemConsumption = 1
        k.state_objects.append(pod)
        pod.atNode = nodes[1]
        nodes[1].currentFormalCpuConsumption += 1
        nodes[1].currentFormalMemConsumption += 1
        deployment.podList.add(pod)

    metric = Metric(k.state_objects)
    metric.setUnusedRes()
    metric.fault_tolerance()

    assert metric.progressive_pod_sum == metric.progressive_sum(3) + metric.progressive_sum(2) + metric.progressive_sum(2) + metric.progressive_sum(5)
    
