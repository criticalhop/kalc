from tests.test_util import print_objects
from tests.libs_for_tests import prepare_yamllist_for_diff
from guardctl.model.search import Check_services, Check_deployments, Check_daemonsets, OptimisticRun, CheckNodeOutage, Check_node_outage_and_service_restart
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.DaemonSet import DaemonSet
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.misc.const import *
import pytest
from guardctl.model.search import K8ServiceInterruptSearch, HypothesisysNodeAndService, HypothesisysNode
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from guardctl.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from tests.test_scenarios_synthetic import build_running_pod_with_d, build_running_pod, build_pending_pod
import inspect
import glob
import git
import os,time,csv

sha = git.Repo(search_parent_directories=True).head.object.hexsha


def test_node_killer_pod_with_service():
#   value                         start   stop    step
    node_amount_range =       range(2,     5,     2)
    pod_amount_range =        range(6,    61,     2)
    per_node_capacity_range = range(30,    31,     10)

    search = True

    assert_brake = False

    csvfile = open("{0}_{1}.csv".format(inspect.stack()[1].function, sha[:7]), 'w')
    csvwriter = csv.writer(csvfile, delimiter=';')

    for node_capacity in per_node_capacity_range:
        for node_amount in node_amount_range:
            for pod_amount in pod_amount_range:
                if pod_amount > (node_amount * node_capacity) : continue
                # Initialize scheduler, globalvar
                start = time.time()
                k = KubernetesCluster()
                scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
                # initial node state
                i = 0
                j = 0
                nodes = []
                pods_running = []
                high = PriorityClass()
                high.priority = 10
                high.metadata_name = "high"
                # low = PriorityClass()
                # low.priority = 0
                # low.metadata_name = "low"
                s = Service()
                s.metadata_name = "test-service"
                s.amountOfActivePods = 0
                s.status = STATUS_SERV["Started"]
                s.isSearched = True
                pod_id=0
                for i in range(node_amount):
                    node_item = Node("node"+str(i))
                    node_item.cpuCapacity = node_capacity
                    node_item.memCapacity = node_capacity
                    node_item.isNull = False
                    node_item.status = STATUS_NODE["Active"]
                    node_item.isSearched = True
                    nodes.append(node_item)
                node_counter = 0
                for j in range(pod_amount):
                    node_item = nodes[node_counter]
                    if node_item.currentFormalCpuConsumption == node_capacity:
                        break
                    pod_running = Pod()
                    pod_running.metadata_name = "pod_prio_0_{0}_{1}".format(i,j)
                    pod_running.cpuRequest = 1
                    pod_running.memRequest = 1
                    pod_running.atNode = node_item
                    pod_running.status = STATUS_POD["Running"]
                    pod_running.hasDeployment = False
                    pod_running.hasService = False
                    pod_running.hasDaemonset = False
                    pod_running.priorityClass = high
                    pod_running.hasService = True
                    pods_running.append(pod_running)
                    # node_item.podList.add(pod_running)
                    node_item.currentFormalCpuConsumption += 1
                    node_item.currentFormalMemConsumption += 1
                    node_item.amountOfActivePods += 1
                    s.podList.add(pod_running)
                    s.amountOfActivePods += 1
                    node_counter += 1
                    if node_counter == len(nodes):
                        node_counter=0

                k.state_objects.extend(nodes)
                k.state_objects.extend(pods_running)
                # k.state_objects.extend([low])
                k.state_objects.append(high)
                k.state_objects.append(s)
                k._build_state()
                
                print("(node_capacity * (node_amount - 1))(",(node_capacity * (node_amount - 1)), ")<(", pod_amount,")pod_amount")

                if (node_capacity * (node_amount - 1)) < pod_amount:
                    task_type = "no-outage"
                else:
                    task_type = "NodeOutageFinished"

    
                print("check break node_amount {0} with capacity {1} pod amount {2}".format( node_amount, node_capacity,pod_amount))
                print("-------------------")
                print_objects(k.state_objects)


                GenClass = type("{0}_{1}_{2}_{3}".format(inspect.stack()[1].function, node_amount, pod_amount, sha[:7]),(HypothesisysNode,),{})

                p = GenClass(k.state_objects)

                try:
                    p.run(timeout=1000, sessionName=f"gen_test_{node_capacity}_{node_amount}_{pod_amount}")
                except Exception as e:
                    print("run break exception is \n",e)
                    assert False
                # print_plan(p)
                end = time.time()
                print("-------------------")
                print("timer :", int(end - start))
                if p.plan != None:
                    csvwriter.writerow([node_amount, node_capacity, pod_amount, int(end - start), "ok"])
                else:
                    csvwriter.writerow([node_amount, node_capacity, pod_amount, int(end - start), "empty_plan"])
                csvfile.flush()
                print("-------------------")
