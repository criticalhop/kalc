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
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from click.testing import CliRunner
from guardctl.model.scenario import Scenario
from poodle import planned
from tests.libs_for_tests import convert_space_to_yaml,print_objects_from_yaml,print_plan,load_yaml, print_objects_compare, checks_assert_conditions, reload_cluster_from_yaml, checks_assert_conditions_in_one_mode
from tests.test_scenarios_synthetic import build_running_pod_with_d, build_running_pod, build_pending_pod
import inspect

# Some pods on node running priority=0 some pods in pending priority=1 they should swap position
def test_2_pod_swapper():
    nodes_amount = 1
    assert_brake = False
    for node_capacity in range(4,31,3):
        for pod_amount in range(2,15,3):
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
            pod_id=0
            for i in range(nodes_amount):
                node_item = Node("node"+str(i))
                node_item.cpuCapacity = node_capacity
                node_item.memCapacity = node_capacity
                node_item.isNull = False
                node_item.status = STATUS_NODE["Active"]
                nodes.append(node_item)
                
                for j in range(pod_amount):
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
                    pod_running.priorityClass = low
                    pod_running.hasService = False
                    pods_running.append(pod_running)
                    node_item.currentFormalCpuConsumption += 1
                    node_item.currentFormalMemConsumption += 1
                    node_item.amountOfActivePods += 1
                    
            
            for j in range(pod_amount):
                pod_pending = Pod()
                pod_pending.metadata_name = "pod_prio_1_{0}_{1}".format(i,j)
                pod_pending.cpuRequest = 1
                pod_pending.memRequest = 1
                pod_pending.status = STATUS_POD["Pending"]
                pod_pending.hasDeployment = False
                pod_pending.hasService = False
                pod_pending.hasDaemonset = False
                pod_pending.priorityClass = high
                pod_pending.hasService = False
                pods_pending.append(pod_pending)

                scheduler.podQueue.add(pod_pending)
                scheduler.queueLength += 1
            scheduler.status = STATUS_SCHED["Changed"]

            k.state_objects.extend(nodes)
            k.state_objects.extend(pods_pending)
            k.state_objects.extend(pods_running)
            k.state_objects.extend([low,high])
            k._build_state()

            class GoalClass(K8ServiceInterruptSearch):
                #goal = lambda self: self.scheduler.status == STATUS_SCHED["Clean"]
                goal = lambda self: self.running_check()
                def running_check(self):
                    for pp in pods_pending :
                        assert pp.status == STATUS_POD["Running"]
                    for pr in pods_running :
                        assert pr.status == STATUS_POD["Killing"]


            GenClass = type("{0}_{1}_{2}".format(inspect.stack()[1].function, node_capacity, pod_amount),(GoalClass,),{})
            p = GenClass(k.state_objects)
            print("-------------------")
            print("check node_capacity ", node_capacity, " pod amount ", pod_amount)
            print("-------------------")
            # print_objects(k.state_objects)
            # print("-------------------")
            try:
                p.run(timeout=100)
            except Exception as e:
                print("fail")
                # print("run break node_capacity ", node_capacity, " pod_amount " ,pod_amount, "exception is \n",e)
                continue
            # print_plan(p)
            print("ok")
            continue
            try:
                p.xrun(timeout=100)
            except Exception as e:
                print("xrun break node_capacity ", node_capacity, " pod_amount " ,pod_amount, "exception is \n",e)
                break

            print_objects(k.state_objects)
            print("-------------------")

            # assert_conditions = ["StartPod", "Evict_and_replace"]

            
    assert False


# the same as test_2 but only one pod Running and one Pod Pending
def test_3_one_pod_swapper():
    for node_capacity in range(2):
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
        pod_id=0

        node_item = Node("node"+str(i))
        node_item.cpuCapacity = node_capacity
        node_item.memCapacity = node_capacity
        node_item.isNull = False
        node_item.status = STATUS_NODE["Active"]
        nodes.append(node_item)
            
        pod_running = Pod()
        pod_running.metadata_name = "pod_prio_0_{0}_{1}".format(i,j)
        pod_running.cpuRequest = 1
        pod_running.memRequest = 1
        pod_running.atNode = node_item
        pod_running.status = STATUS_POD["Running"]
        pod_running.hasDeployment = False
        pod_running.hasService = False
        pod_running.hasDaemonset = False
        pod_running.priorityClass = low
        pod_running.hasService = False
        pods_running.append(pod_running)
        node_item.currentFormalCpuConsumption += 1
        node_item.currentFormalMemConsumption += 1
        node_item.amountOfActivePods += 1
        
        pod_pending = Pod()
        pod_pending.metadata_name = "pod_prio_1_{0}_{1}".format(i,j)
        pod_pending.cpuRequest = 1
        pod_pending.memRequest = 1
        pod_pending.status = STATUS_POD["Pending"]
        pod_pending.hasDeployment = False
        pod_pending.hasService = False
        pod_pending.hasDaemonset = False
        pod_pending.priorityClass = high
        pod_pending.hasService = False
        pods_pending.append(pod_pending)

        scheduler.podQueue.add(pod_pending)
        scheduler.queueLength += 1
        scheduler.status = STATUS_SCHED["Changed"]

        k.state_objects.extend([pod_running,pod_pending,node_item,low,high])
        k._build_state()

        class GoalClass(K8ServiceInterruptSearch):
            # goal = lambda self: self.scheduler.status == STATUS_SCHED["Clean"]
            goal = lambda self: pod_pending.status == STATUS_POD["Running"] #and pod_running == STATUS_POD["Killing"]

        GenClass = type("{0}".format(inspect.stack()[1].function),(GoalClass,),{})
        p = GenClass(k.state_objects)
        print("check break node_capacity ")
        print("-------------------")
        print_objects(k.state_objects)
        print("-------------------")
        try:
            p.run(timeout=100)
        except Exception as e:
            print("run break node_capacity ", node_capacity, "exception is \n",e)
            continue
        print_plan(p)
        
        try:
            p.xrun(timeout=100)
        except Exception as e:
            print("xrun break node_capacity ", node_capacity, "exception is \n",e)
            continue
            
        print_objects(k.state_objects)
        print("-------------------")

           
    assert False
    

def test_4_node_killer():
    nodes_amount = 1
    assert_brake = False
    for node_capacity in range(34,35,2):
        for pod_amount in range(11,21,3):
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
            pod_id=0
            for i in range(nodes_amount):
                node_item = Node("node"+str(i))
                node_item.cpuCapacity = node_capacity
                node_item.memCapacity = node_capacity
                node_item.isNull = False
                node_item.status = STATUS_NODE["Active"]
                nodes.append(node_item)
                
                for j in range(pod_amount):
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
                    pod_running.priorityClass = low
                    pod_running.hasService = False
                    pods_running.append(pod_running)
                    node_item.currentFormalCpuConsumption += 1
                    node_item.currentFormalMemConsumption += 1
                    node_item.amountOfActivePods += 1
                    
            k.state_objects.extend(nodes)
            k.state_objects.extend(pods_pending)
            k.state_objects.extend(pods_running)
            k.state_objects.extend([low,high])
            k._build_state()

            class GoalClass(K8ServiceInterruptSearch):
                goal = lambda self: self.globalVar.is_node_disrupted == True and self.scheduler.status == STATUS_SCHED["Clean"]

            GenClass = type("{0}_{1}_{2}".format(inspect.stack()[1].function, node_capacity, pod_amount),(GoalClass,),{})
            p = GenClass(k.state_objects)
            print("check break node_capacity ", node_capacity, " pod amount " ,pod_amount)
            print("-------------------")
            print_objects(k.state_objects)
            print("-------------------")
            try:
                p.run(timeout=100)
            except Exception as e:
                print("run break node_capacity ", node_capacity, " pod_amount " ,pod_amount, "exception is \n",e)
                assert False
            print_plan(p)
            
            # try:
            #     p.xrun(timeout=100)
            # except Exception as e:
            #     print("xrun break node_capacity ", node_capacity, " pod_amount " ,pod_amount, "exception is \n",e)
            #     assert False

            # print_objects(k.state_objects)
            # print("-------------------")
    
def test_5_node_killer_pod_with_service():
    nodes_amount = 1
    assert_brake = False
    for node_capacity in range(30,31,2):
        for pod_amount in range(10,15,3):
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
            for i in range(nodes_amount):
                node_item = Node("node"+str(i))
                node_item.cpuCapacity = node_capacity
                node_item.memCapacity = node_capacity
                node_item.isNull = False
                node_item.status = STATUS_NODE["Active"]
                nodes.append(node_item)
                
                for j in range(pod_amount):
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
                    pod_running.priorityClass = low
                    pod_running.hasService = True
                    pods_running.append(pod_running)
                    node_item.currentFormalCpuConsumption += 1
                    node_item.currentFormalMemConsumption += 1
                    node_item.amountOfActivePods += 1
                    s.podList.add(pod_running)
                    s.amountOfActivePods += 1

            k.state_objects.extend(nodes)
            k.state_objects.extend(pods_pending)
            k.state_objects.extend(pods_running)
            k.state_objects.extend([low,high])
            k._build_state()

            class GoalClass(K8ServiceInterruptSearch):
                goal = lambda self: self.globalVar.is_node_disrupted == True and self.scheduler.status == STATUS_SCHED["Clean"]

            GenClass = type("{0}_{1}_{2}".format(inspect.stack()[1].function, node_capacity, pod_amount),(GoalClass,),{})
            p = GenClass(k.state_objects)
            print("check break node_capacity ", node_capacity, " pod amount " ,pod_amount)
            print("-------------------")
            print_objects(k.state_objects)
            print("-------------------")
            try:
                p.run(timeout=100)
            except Exception as e:
                print("run break node_capacity ", node_capacity, " pod_amount " ,pod_amount, "exception is \n",e)
                assert False
            print_plan(p)