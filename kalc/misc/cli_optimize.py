from kalc.interactive import *
from kalc.model.search import Balance_pods_and_drain_node
from kalc.model.kinds.Deployment import Deployment
from kalc.misc.script_generator import generate_compat_header
from collections import defaultdict
from poodle.schedule import SchedulingError
from itertools import combinations

D_RANK = 0
D_DEPLOYMENT = 1
D_PODS = 2
D_UNBALANCED_PODS = 3

def optimize_cluster(clusterData=None):
    print("WARNING! Not taking into account service SLOs")
    update(clusterData) # To reload from scratch...
    deployments = filter(lambda x: isinstance(x, Deployment), kalc_state_objects) # to get amount of deployments

    # Find how many pods are on same node for every deployment
    deployments_maxpods = []
    for d in deployments:
        pod_node = defaultdict(list)
        for pod in d.podList:
            pods_node = pod.atNode._property_value # Poodle bug. https://github.com/criticalhop/poodle/issues/122
            pod_node[str(pods_node.metadata_name)].append(pod) # str: poodle bug
        # Find which pods are the worst
        unbalanced_pods_indexed = [[len(x), x] for x in pod_node.values()]
        unbalanced_pods_indexed.sort(key=lambda x: x[0], reverse=True)
        unbalanced_pods = [x[1] for x in unbalanced_pods_indexed]
        only_unbalanced = unbalanced_pods_indexed[0][1]
        unbalanced_pods = [item for sublist in unbalanced_pods for item in sublist] # flatten
        deployments_maxpods.append([max([x[0] for x in unbalanced_pods_indexed]), d, unbalanced_pods, only_unbalanced])
    deployments_maxpods = sorted(deployments_maxpods, key=lambda x: x[0], reverse=True) 
    print(f"Worst case deployment {str(deployments_maxpods[0][D_DEPLOYMENT])}, with {deployments_maxpods[0][D_RANK]} pods on same node")

     
    drain_node_frequency = 2
    twice_drain_node_frequency = 3
    deployment_amount = 0

    searchable_deployments = set()
    searchable_pods = set()

    user_cases =[]
    nodes = list(filter(lambda x: isinstance(x, Node), kalc_state_objects))
    for deployment_x_s_pods in deployments_maxpods:
        deployment_amount += 1
        pod_amount = 1
        drain_node_counter = 0
        searchable_deployments.add(str(deployment_x_s_pods[D_DEPLOYMENT].metadata_name))
    
        searchable_pods |= set([str(p.metadata_name) for p in deployment_x_s_pods[D_UNBALANCED_PODS]]) # add all unbalanced pods immediately
        user_cases = combinations([range(0,len(nodes)),range(0,len(searchable_pods)])        
        print(user_cases)
        for pod in deployment_x_s_pods[D_DEPLOYMENT].podList: # actually, for i in range(len(..podList))
            update(clusterData) # To reload from scratch...


            problem = Balance_pods_and_drain_node(kalc_state_objects)

            globalVar = next(filter(lambda x: isinstance(x, GlobalVar), kalc_state_objects))
            pods = filter(lambda x: isinstance(x, Pod), kalc_state_objects)

            d_cand = []
            p_cand = []

            if len(searchable_pods) < pod_amount: 
                searchable_pods.add(str(pod.metadata_name))
                continue

            # mark all deployments as isSearchable from searchable_deployments
            for d in deployments:
                if str(d.metadata_name) in searchable_deployments:
                    d.searchable = True
                    d_cand.append(str(d.metadata_name))

            # mark all pods as isSearchable from searchable_pods 
            for spod in pods:
                if str(spod.metadata_name) in searchable_pods:
                    spod.searchable = True
                    p_cand.append(str(spod.metadata_name))

            # add one more pod from the list
            searchable_pods.add(str(pod.metadata_name))

            globalVar.target_DeploymentsWithAntiaffinity_length = deployment_amount
            pod_amount += 1
            globalVar.target_amountOfPodsWithAntiaffinity = pod_amount
            drain_node_counter += 1
            print("Deployment candidates:", ', '.join(d_cand))
            print("Pod candidates:", ", ".join(p_cand))
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
            try:
                problem.xrun()
            except SchedulingError:
                print("Could not solve in this configuration, trying next...")
            move_script = '\n'.join(problem.script)
            full_script = generate_compat_header() + move_script
            scritpt_file = f"./kalc_optimize_{deployment_amount}_{pod_amount}.sh"
            print("Generated optimization script at", scritpt_file)
            with open(scritpt_file, "w+") as fd:
                fd.write(full_script)

def run():
    optimize_cluster(None)
