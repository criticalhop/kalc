from kalc.interactive import *
from kalc.model.search import Balance_pods_and_drain_node
from kalc.model.kinds.Deployment import Deployment


def optimize_cluster(clusterData):
    update(clusterData)

    import sys
    sys.path.append('./tests/')
    import test_util
    test_util.print_objects(kalc_state_objects)


    p = Balance_pods_and_drain_node(kalc_state_objects)
    deployments = filter(lambda x: isinstance(x, Deployment), kalc_state_objects)
    globalVar = next(filter(lambda x: isinstance(x, GlobalVar), kalc_state_objects))
    pods = filter(lambda x: isinstance(x, Pod), kalc_state_objects)
    drain_node_counter = 0 
    drain_node_frequency = 2
    twice_drain_node_frequency = 3
    deployment_amount = 0

    for deployment in deployments:
        deployment_amount += 1
        globalVar.target_DeploymentsWithAntiaffinity_length = deployment_amount
        pod_amount = 1
        for pod in deployment.podList:
            pod_amount += 1
            globalVar.target_amountOfPodsWithAntiaffinity = pod_amount
            drain_node_counter += 1
            if drain_node_counter % drain_node_frequency == 0:
                print("-----------------------------------------------------------------------------------")
                print("--- Solving case for deployment_amount = ",deployment_amount,", pod_amount =  ", pod_amount, ", drain nodes = 1 ---")
                print("-----------------------------------------------------------------------------------")
                globalVar.target_NodesDrained_length = 1
            if drain_node_counter % twice_drain_node_frequency == 0:
                print("-----------------------------------------------------------------------------------")
                print("--- Solving case for deployment_amount = ",deployment_amount,", pod_amount =  ", pod_amount, ", drain nodes = 2 ---")
                print("-----------------------------------------------------------------------------------")
                globalVar.target_NodesDrained_length = 2
            print("-----------------------------------------------------------------------------------")
            print("--- Solving case for deployment_amount = ",deployment_amount,", pod_amount =  ", pod_amount, "---")
            print("-----------------------------------------------------------------------------------")
            # print_objects(k2.state_objects)
            p.run()
            print(p.plan)



def run():
    optimize_cluster(None)
