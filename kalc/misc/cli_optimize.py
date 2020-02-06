import timeit
from kalc.interactive import *
from kalc.model.search import Optimize_directly
from kalc.model.kinds.Deployment import Deployment
from kalc.misc.script_generator import generate_compat_header, print_metric, print_stats
from collections import defaultdict
from poodle.schedule import SchedulingError
from itertools import combinations, product
from logzero import logger
import logzero
import os
logzero.logfile("./kalc-optimize.log")
kalc_debug = os.getenv('KALC_DEBUG', "0")
if kalc_debug == "0": logzero.loglevel(20)

D_RANK = 0
D_DEPLOYMENT = 1
D_PODS = 2
D_UNBALANCED_PODS = 3

L_TARGETS = 0
L_DEPLOYMENTS = 1
L_NODES = 2
L_PODS = 3

C_TYPE = 1
C_NUM = 0

def generate_hypothesys_combination(deployments, nodes):
    deployments_maxpods = []
    drain_node_frequency = 2
    twice_drain_node_frequency = 3
    deployment_amount = 0
    searchable_deployments = set()
    searchable_pods = set()
    deployments_by_ranks = []
    max_pod_number = 0
    comb_nodes_pods_fitered = []
    for d in deployments:
        deployment_amount += 1
        deployment_max_pod_number = 0
        list_for_comb = []
        pod_node = defaultdict(list)
        if len(d.podList._get_value()) == 0:
            continue
        for pod in d.podList:
            pods_node = pod.atNode._property_value # Poodle bug. https://github.com/criticalhop/poodle/issues/122
            pod_node[str(pods_node.metadata_name)].append(pod) # str: poodle bug
            deployment_max_pod_number += 1
        # Find which pods are the worst
        unbalanced_pods_indexed = [[len(x), x] for x in pod_node.values()]
        unbalanced_pods_indexed.sort(key=lambda x: x[0], reverse=True)
        unbalanced_pods = [x[1] for x in unbalanced_pods_indexed]
        only_unbalanced = unbalanced_pods_indexed[0][1]
        unbalanced_pods = [item for sublist in unbalanced_pods for item in sublist] # flatten
        if deployment_max_pod_number > max_pod_number:
            max_pod_number = deployment_max_pod_number
        if unbalanced_pods_indexed:
            deployments_maxpods.append([max([x[0] for x in unbalanced_pods_indexed]), d, unbalanced_pods, only_unbalanced])
    deployments_maxpods = sorted(deployments_maxpods, key=lambda x: x[0], reverse=True) 
    if deployments_maxpods:
        highest_max_pods_deployment = max(x[0] for x in deployments_maxpods)
    else:
        highest_max_pods_deployment = 0
    list_of_deployments_sorted = []
    prev_deployments_current_rank=[]
    list_deployments_targets = []
    for processed_rank in range(highest_max_pods_deployment,0,-1):
        deployments_current_rank = []
        for d in deployments_maxpods:
            if d[0] == processed_rank:
                deployments_current_rank.append(d[1])
            if processed_rank == 0:
                deployments_current_rank.append(d[1])
        if deployments_current_rank:
            deployments_current_rank.extend(prev_deployments_current_rank)
            list_of_deployments_sorted.append(deployments_current_rank)
            prev_deployments_current_rank = deployments_current_rank
    if deployments_maxpods:
        logger.info(f"Worst case deployment {str(deployments_maxpods[0][D_DEPLOYMENT])}, with {deployments_maxpods[0][D_RANK]} pods on same node")
    list_deployments_targets = list(range(1,deployment_amount+1))
    list_nodes = list(range(0,2))
    list_pods = list(range(2,max_pod_number+1))
    list_for_comb = []
    if list_deployments_targets:
        list_for_comb.append(list_deployments_targets)
    list_for_comb.append(list_of_deployments_sorted)
    list_for_comb.append(list_nodes)
    list_for_comb.append(list_pods)
    comb_nodes_pods = list(product(*list_for_comb))
    #TODO: Exclude combinations when number of serachable deployments is less than list of deployments 
    comb_nodes_pods_fitered = []
    for comb in comb_nodes_pods:
        if len(comb[1]) >= comb[0]:
            comb_nodes_pods_fitered.append(comb)
    return comb_nodes_pods_fitered

def generate_combinations(move_bound,drain_bound,drain_step):
    recomendations_list = []
    move_list = []
    for i in range(move_bound):
        item = [i,'move']
        move_list.append(item)

    drain_list = []
    for d in range(drain_bound):
        item = [d,'drain']
        drain_list.append(item)

    combinations_list = []
    next_drain = 0
    for i in range(move_bound):
        if i > 0:
            combinations_list.append(move_list[i])
        if i % drain_step == 0 and drain_bound > 0 and next_drain < drain_bound-1:
            combinations_list.append(drain_list[next_drain])
            next_drain += 1
    return combinations_list 


def optimize_cluster(clusterData=None, runs=999999):
    start_time = timeit.default_timer()
    logger.warning("WARNING! Not taking into account service SLOs")
    update(clusterData)  # To reload from scratch...
    drain_bound = 0
    metric_start = Metric(kalc_state_objects)
    metric_start.calc()
    success = False
    recomendations_bound = 10
    nodes = len(list(filter(lambda x: isinstance(x, Node), kalc_state_objects))) # pylint: disable=undefined-variable
    drain_bound = nodes - 1
    drain_step = 2
    combinations_list = generate_combinations(recomendations_bound,drain_bound,drain_step)
    index = 0
    for combination in combinations_list:
        if index >= runs:  return success
        success = False
        logzero.loglevel(40)
        update(clusterData) # To reload from scratch...
        logzero.loglevel(20)
        problem = Optimize_directly(kalc_state_objects)
        globalVar_local = next(filter(lambda x: isinstance(x, GlobalVar), kalc_state_objects)) # pylint: disable=undefined-variable
        
        logger.info("Initial utilization {0:.1f}%".format(metric_start.node_utilization*100))
        logger.info("Initial availabilty risk metric {0:.1f} v.u.".format(metric_start.progressive_pod_sum))
        if combination[C_TYPE] == 'move':
            globalVar_local.target_amount_of_recomendations = combination[C_NUM] 
            globalVar_local.target_NodesDrained_length = 0
            logger.debug("Recomendations : " + str(combination[C_NUM]))
            logger.debug("Drained nodes : " + '0')
        if combination[C_TYPE] == 'drain':
            globalVar_local.target_amount_of_recomendations = 0 
            globalVar_local.target_NodesDrained_length = combination[C_NUM]
            logger.debug("Recomendations : " + '0')
            logger.debug("Drained nodes : " + str(combination[C_NUM]))
        logger.info("-----------------------------------------------------------------------------------")
        metric = Metric(kalc_state_objects)
        kalc_state_objects.append(metric)

        try:
            problem.xrun()
        except SchedulingError:
            logger.warning("Could not solve in this configuration, trying next...")
            success = False
            continue
        if len(problem.script) == 0:
            logger.error("Generated solution contains no actions")
            success = False
            continue
        metric.calc()
        metric.run_time = timeit.default_timer() - start_time
        start_time = timeit.default_timer()
        logger.info("Result utilization {0:.1f}%".format(metric.node_utilization * 100))
        logger.info("Result availabilty risk metric {0:.1f} v.u.".format(metric.progressive_pod_sum))
        logger.info("Pod moved {0}".format(len(metric.moved_pod_set)))
        logger.info("Node drained {0}".format(len(metric.drained_node_set)))
        logger.info("Run time 🕐 {0:.0f}s".format(metric.run_time))
        logger.info(f"Pod amount {len(metric.pods)}")
        logger.info(f"Node amount {len(metric.nodes)}")
        move_script = '\n'.join(problem.script)
        full_script = (
            generate_compat_header() + 
            "####################################\n" +
            print_metric(metric_start.node_utilization * 100, "Initial utilization") + 
            print_metric(metric.node_utilization * 100, "Result utilization") + 
            print_metric(metric_start.progressive_pod_sum, "Initial availability risk") + 
            print_metric(metric.progressive_pod_sum, "Result availability risk") + 
            print_stats(metric, "Stats") +
            "####################################\n" +
            move_script)
        scritpt_file = f"./kalc_optimize_{index}.sh"
        logger.info("📜 Generated optimization script at %s" % scritpt_file)
        success = True
        with open(scritpt_file, "w+") as fd:
            fd.write(full_script)
        index += 1
            
            
def run():  # pylint: disable=function-redefined
    optimize_cluster(None)


def tryrun():
    import os, sys
    if kalc_debug == "1":
        optimize_cluster(None)
    else:
        try:
            optimize_cluster(None)
        except KeyboardInterrupt:
            sys.exit(0)
