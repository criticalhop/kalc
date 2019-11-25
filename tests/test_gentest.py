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
from guardctl.model.search import K8ServiceInterruptSearch, HypothesisysNode
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from guardctl.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from tests.test_scenarios_synthetic import build_running_pod_with_d, build_running_pod, build_pending_pod
import inspect
import cloudpickle as pickle
import glob
import git
import os
os.environ["RUN_ALGO"] = ""


def test_node_killer_pod_with_service():
#   value                         start   stop    step
    node_amount_range =       range(2,     10,     2)
    pod_amount_range =        range(10,    15,     3)
    per_node_capacity_range = range(30,    31,     2)

    search = True

    assert_brake = False
    for node_capacity in per_node_capacity_range:
        for node_amount in node_amount_range:
            for pod_amount in pod_amount_range:
                # Initialize scheduler, globalvar
                k = KubernetesCluster()
                scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
                # initial node state
                i = 0
                j = 0
                nodes = []
                pods_running = []
                pods_pending = []
                high = PriorityClass()
                high.priority = 10
                high.metadata_name = "high"
                low = PriorityClass()
                low.priority = 0
                low.metadata_name = "low"
                s = Service()
                s.metadata_name = "test-service"
                s.amountOfActivePods = 0
                pod_id=0
                for i in range(node_amount):
                    node_item = Node("node"+str(i))
                    node_item.cpuCapacity = node_capacity
                    node_item.memCapacity = node_capacity
                    node_item.isNull = False
                    node_item.status = STATUS_NODE["Active"]
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
                    pod_running.atNode = True
                    pod_running.status = STATUS_POD["Running"]
                    pod_running.hasDeployment = False
                    pod_running.hasService = False
                    pod_running.hasDaemonset = False
                    pod_running.priorityClass = low
                    pod_running.hasService = True
                    pods_running.append(pod_running)
                    node_item.podList.add(pod_running)
                    node_item.currentFormalCpuConsumption += 1
                    node_item.currentFormalMemConsumption += 1
                    node_item.amountOfActivePods += 1
                    s.podList.add(pod_running)
                    s.amountOfActivePods += 1
                    node_counter += 1
                    if node_counter == len(nodes):
                        node_counter=0

                k.state_objects.extend(nodes)
                k.state_objects.extend(pods_pending)
                k.state_objects.extend(pods_running)
                k.state_objects.extend([low,high])
                k._build_state()
                
                if (node_capacity * (node_amount - 1)) < pod_amount:
                    task_type = "no-outage"
                else:
                    task_type = "node-outage"

    
            print("check break node_amount ", node_amount, " pod amount " ,pod_amount)
            print("-------------------")
            print_objects(k.state_objects)

            sha = git.Repo(search_parent_directories=True).head.object.hexsha

            GenClass = type("{0}_{1}_{2}_{3}".format(inspect.stack()[1].function, node_amount, pod_amount, sha[:7]),(HypothesisysNode,),{})

            p = GenClass(k.state_objects)
            

            print("-------------------")
            try:
                p.run(timeout=100)
            except Exception as e:
                print("run break exception is \n",e)
                assert False
            print_plan(p)

# def test_pickler_load():
#     pickles = glob.glob('*.pickle')
#     for file_name in pickles:
#         with open(file_name, 'rb') as handle:
#             d = pickle.load(handle)
#             kubernetesCluster = d["kluster"]
    
#         print("check break node_amount ", file_name.split('.')[0].split("-")[0], " pod amount " , file_name.split('.')[0].split("-")[1])
#         print("-------------------")
#         print_objects(kubernetesCluster.state_objects)

#         sha = git.Repo(search_parent_directories=True).head.object.hexsha

#         GenClass = type("{0}_{1}_{2}".format(inspect.stack()[1].function, file_name.split('.')[0], sha),(HypothesisysNode,),{})

#         p = GenClass(kubernetesCluster.state_objects)
        

#         print("-------------------")
#         try:
#             p.run(timeout=100)
#         except Exception as e:
#             print("run break exception is \n",e)
#             assert False
#         print_plan(p)