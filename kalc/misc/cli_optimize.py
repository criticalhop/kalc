from kalc.interactive import *
from kalc.model.search import Balance_pods_and_drain_node
from kalc.model.kinds.Deployment import Deployment
from kalc.misc.script_generator import generate_compat_header
from collections import defaultdict


def optimize_cluster(clusterData=None):
    print("WARNING! Not taking into account service SLOs")
    update(clusterData) # To reload from scratch...
    deployments = filter(lambda x: isinstance(x, Deployment), kalc_state_objects) # to get amount of deployments

    # Find how many pods are on same node for every deployment
    deployments_maxpods = []
    for d in deployments:
        pod_node = defaultdict(lambda: 0)
        for pod in d.podList:
            pods_node = pod.atNode._property_value # Poodle bug. https://github.com/criticalhop/poodle/issues/122
            pod_node[str(pods_node.metadata_name)] += 1 # str: poodle bug
        deployments_maxpods.append([max(pod_node.values()), d])
    deployments_maxpods = sorted(deployments_maxpods, key=lambda x: x[0]) 
    print(f"Worst case deployment {str(deployments_maxpods[0][1])}, with {deployments_maxpods[0][0]} pods on same node")

    drain_node_counter = 0 
    drain_node_frequency = 2
    twice_drain_node_frequency = 3
    deployment_amount = 0

    for deployment in deployments_maxpods:
        deployment_amount += 1
        pod_amount = 1
        for pod in deployment[1].podList: # actually, for i in range(len(..podList))
            update(clusterData) # To reload from scratch...

            p = Balance_pods_and_drain_node(kalc_state_objects)
            deployments = filter(lambda x: isinstance(x, Deployment), kalc_state_objects)
            globalVar = next(filter(lambda x: isinstance(x, GlobalVar), kalc_state_objects))
            pods = filter(lambda x: isinstance(x, Pod), kalc_state_objects)

            globalVar.target_DeploymentsWithAntiaffinity_length = deployment_amount
            pod_amount += 1
            globalVar.target_amountOfPodsWithAntiaffinity = pod_amount
            drain_node_counter += 1
            if drain_node_counter % drain_node_frequency == 0:
                print("-----------------------------------------------------------------------------------")
                print("--- Solving case for deployment_amount =", deployment_amount, ", pod_amount =", pod_amount, ", drain nodes = 1 ---")
                print("-----------------------------------------------------------------------------------")
                globalVar.target_NodesDrained_length = 1
            elif drain_node_counter % twice_drain_node_frequency == 0:
                print("-----------------------------------------------------------------------------------")
                print("--- Solving case for deployment_amount =", deployment_amount,", pod_amount =", pod_amount, ", drain nodes = 2 ---")
                print("-----------------------------------------------------------------------------------")
                globalVar.target_NodesDrained_length = 2
            else:
                print("-----------------------------------------------------------------------------------")
                print("--- Solving case for deployment_amount =", deployment_amount, ", pod_amount =", pod_amount, "---")
                print("-----------------------------------------------------------------------------------")
            # print_objects(k2.state_objects)
            p.xrun()
            move_script = '\n'.join(p.script)
            full_script = generate_compat_header() + move_script
            scritpt_file = f"./kalc_optimize_{deployment_amount}_{pod_amount}.sh"
            print("Generated optimization script at", scritpt_file)
            with open(scritpt_file, "w+") as fd:
                fd.write(full_script)

def run():
    optimize_cluster(None)
