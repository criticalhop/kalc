import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8SearchEviction
from guardctl.misc.object_factory import labelFactory

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

class SingleGoalEvictionDetect(K8SearchEviction):
    def goal(self):
        # for ob in self.objectList:
        #     print(str(ob))
        pod_loaded_list = filter(lambda x: isinstance(x, Pod), self.objectList)
        for poditem in pod_loaded_list:
            print("pod:"+ str(poditem.metadata_name._get_value()) + " status_phase: " + str(poditem.status_phase) + " spec_nodeName: " + str(poditem.spec_nodeName._get_value()) + " cpuRequest: " + str(poditem.cpuRequest._get_value()) + " memRequest: " + str(poditem.memRequest._get_value()) + \
                " cpuLimit: " + str(poditem.cpuLimit._get_value()) + " memLimit: " + str(poditem.memLimit._get_value())+ \
                "metadata_labels:" + str(poditem.metadata_labels._get_value))
        node_loaded_list = filter(lambda x: isinstance(x, Node), self.objectList)
        for nodeitem in node_loaded_list:
            print("node:"+ str(nodeitem.metadata_name._get_value()) + " cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + " memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
            " currentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
            " currentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
            " AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
            " podAmount: "  + str(nodeitem.podAmount._get_value()) + \
            " isNull:"  + str(nodeitem.isNull._get_value()) + \
            " status:"  + str(nodeitem.status._get_value()))

        evict_service = next(filter(lambda x: isinstance(x, Service) and \
            labelFactory.get("app", "redis-evict") in x.spec_selector._get_value(),
            self.objectList))
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        pod = next(filter(lambda x: isinstance(x, Pod), self.objectList))
        return  pod.status_phase == STATUS_POD_PENDING   #  evict_service.status == scheduler.status == STATUS_SCHED_CLEAN and STATUS_SERV_INTERRUPTED 
                                    
def test_priority_is_loaded():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    priorityClasses = filter(lambda x: isinstance(x, PriorityClass), k.state_objects)
    for p in priorityClasses:
        if p.metadata_name == "high-priority" and p.preemptionPolicy == TYPE_POLICY_PreemptLowerPriority\
            and p.priority > 0:
            return
    raise ValueError("Could not find priority loded")

def test_service_load():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    objects = filter(lambda x: isinstance(x, Service), k.state_objects)
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels:
            return
    raise ValueError("Could not find service loded")

def test_service_status():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    objects = filter(lambda x: isinstance(x, Service), k.state_objects)
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels and \
                p.status == STATUS_SERV_STARTED:
            return
    raise ValueError("Could not find service loded")

def test_service_active_pods():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    objects = filter(lambda x: isinstance(x, Service), k.state_objects)
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels and \
                p.status == STATUS_SERV_STARTED and\
                    p.amountOfActivePods > 0:
            return
    raise ValueError("Could not find service loded")


def test_service_link_to_pods():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    objects = filter(lambda x: isinstance(x, Service), k.state_objects)
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels and \
                p.status == STATUS_SERV_STARTED:
                serv = p
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels and \
                p.status == STATUS_SERV_STARTED:
                if p.targetService == serv:
                    return
    raise ValueError("Could not find service loded")

def test_queue_status():
    "test length and status of scheduler queue after load"
    pass

#@pytest.mark.skip(reason="no way of currently testing this")
def test_eviction_fromfiles_strictgoal():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    p = SingleGoalEvictionDetect(k.state_objects)
    p.run(timeout=60, sessionName="test_eviction_fromfiles_strictgoal")
    # p.run(timeout=60)
    if not p.plan: 
        # print("Could not solve %s" % p.__class__.__name__)
        raise Exception("Could not solve %s" % p.__class__.__name__)
    if p.plan:
        i=0
        for a in p.plan:
            i=i+1
            print(i,":",a.__class__.__name__,"\n",yaml.dump({str(k):repr(v._get_value()) if v else f"NONE_VALUE:{v}" for (k,v) in a.kwargs.items()}, default_flow_style=False))

