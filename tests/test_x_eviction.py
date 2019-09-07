import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

ALL_STATE = None

import logzero
logzero.logfile("./test.log", disableStderrLogger=False)

class SingleGoalEvictionDetect(K8ServiceInterruptSearch):
    def select_target_service(self):
        service_found = None
        for servicel in filter(lambda x: isinstance(x, Service), self.objectList):
            if servicel.metadata_name == "redis-master-evict":
                service_found = servicel
                break
        assert service_found
        self.targetservice = service_found
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))

    goal = lambda self: self.targetservice.status == STATUS_SERV["Interrupted"] and \
            self.scheduler.status == STATUS_SCHED["Clean"]

    def print_objects(self):
        print("=====>")
        pod_loaded_list = filter(lambda x: isinstance(x, Pod), self.objectList)
        for poditem in pod_loaded_list:
            print("pod:"+ str(poditem.metadata_name._get_value()) + \
                " status: " + str(poditem.status) + \
                " priority_class: " + str(poditem.priorityClass._property_value.metadata_name) + \
                " toNode: " + str(poditem.toNode._property_value) + \
                " atNode: " + str(poditem.atNode._property_value) + \
                " cpuRequest: " + str(poditem.cpuRequest._get_value()) + " memRequest: " + str(poditem.memRequest._get_value()) + \
                " cpuLimit: " + str(poditem.cpuLimit._get_value()) + " memLimit: " + str(poditem.memLimit._get_value()) + \
                " targetService: "+ str(poditem.targetService._property_value) +\
                " metadata_labels:" + str([str(x) for x in poditem.metadata_labels._property_value]))
        node_loaded_list = filter(lambda x: isinstance(x, Node), self.objectList)
        for nodeitem in node_loaded_list:
            print("node:"+ str(nodeitem.metadata_name._get_value()) + " cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + " memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
            " currentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
            " currentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
            " AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
            " podAmount: "  + str(nodeitem.podAmount._get_value()) + \
            " isNull:"  + str(nodeitem.isNull._get_value()) + \
            " status:"  + str(nodeitem.status._get_value()))
        services = filter(lambda x: isinstance(x, Service), self.objectList)
        for service in services:
            print("service: "+str(service.metadata_name)+\
                " amountOfActivePods: "+str(service.amountOfActivePods._get_value())+\
                " status: "+str(service.status._get_value()) +
                " spec_selector: "+str([str(x) for x in service.spec_selector._property_value]))

        prios = filter(lambda x: isinstance(x, PriorityClass), self.objectList)
        for prio in prios:
            print("priorityClass: "+str(prio.metadata_name)+" "+str(prio.priority._get_value()))


        scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))


def test_priority_is_loaded():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    priorityClasses = filter(lambda x: isinstance(x, PriorityClass), k.state_objects)
    for p in priorityClasses:
        if p.metadata_name == "high-priority" and p.preemptionPolicy == POLICY["PreemptLowerPriority"]\
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
            labelFactory.get("app", "redis-evict") in p.metadata_labels._get_value():
            return
    raise ValueError("Could not find service loded")

def test_service_status():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    objects = filter(lambda x: isinstance(x, Service), k.state_objects)
    service_found = False
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels._get_value() and \
            labelFactory.get("app", "redis-evict") in p.spec_selector._get_value() and \
                p.status == STATUS_SERV["Pending"]:
            service_found = True
            break
    assert service_found

    objects = filter(lambda x: isinstance(x, Pod), k.state_objects)
    for p in objects:
        if p.targetService == Pod.TARGET_SERVICE_NULL and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels._get_value():
            return

    raise ValueError("Could not find service loded")

class StartServiceGoal(K8ServiceInterruptSearch):
    def select_target_service(self):
        service_found = None
        for servicel in filter(lambda x: isinstance(x, Service), self.objectList):
            if servicel.metadata_name == "redis-master-evict":
                service_found = servicel
                break
        assert service_found
        self.targetservice = service_found
    def goal(self):
        return self.targetservice.status == STATUS_SERV["Started"]
    def debug(self):
        self.problem()
        self_methods = [getattr(self,m) for m in dir(self) if callable(getattr(self,m)) and hasattr(getattr(self, m), "_planned")]
        model_methods = []
        methods_scanned = set()
        for obj in self.objectList:
            if not obj.__class__.__name__ in methods_scanned:
                methods_scanned.add(obj.__class__.__name__)
                for m in dir(obj):
                    if callable(getattr(obj, m)) and hasattr(getattr(obj, m), "_planned"):
                        model_methods.append(getattr(obj, m))
        debug_plan(
            methods=self_methods + list(model_methods),
            space=list(self.__dict__.values())+self.objectList,
            goal=lambda:(self.goal()),
            plan=[Pod().connect_pod_service_labels]
        )

def test_service_active_pods():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k._build_state()
    p = StartServiceGoal(k.state_objects)
    p.select_target_service()
    global ALL_STATE
    ALL_STATE = k.state_objects
    # p.debug()
    try:
        p.xrun()
    except EmptyPlanError:
        return
    objects = filter(lambda x: isinstance(x, Service), k.state_objects)
    pods_active = False
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels._get_value() and \
                p.status == STATUS_SERV["Started"] and\
                    p.amountOfActivePods > 0:
            pods_active = True
            break
    assert pods_active

def test_service_link_to_pods():
    objects = filter(lambda x: isinstance(x, Service), ALL_STATE)
    serv = None
    for p in objects:
        if p.metadata_name == "redis-master-evict" and \
            labelFactory.get("app", "redis-evict") in p.metadata_labels._get_value() and \
                p.status == STATUS_SERV["Started"]:
                serv = p
    assert not serv is None
    objects = filter(lambda x: isinstance(x, Pod), ALL_STATE)
    for p in objects:
        if str(p.metadata_name).startswith("redis-master-evict")\
             and p.targetService == serv:
            return
    raise ValueError("Could not find service loded")

def test_queue_status():
    "test length and status of scheduler queue after load"
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    scheduler = next(filter(lambda x: isinstance(x, Scheduler), k.state_objects))
    nodes = list(filter(lambda x: isinstance(x, Node), k.state_objects))
    assert scheduler.queueLength == len(nodes)
    assert scheduler.podQueue._get_value()
    assert scheduler.status == STATUS_SCHED["Changed"]

def test_nodes_status():
    objects = filter(lambda x: isinstance(x, Node), ALL_STATE)
    for node in objects:
        if node.cpuCapacity > 1 and \
            node.memCapacity > 1 and \
           node.currentFormalCpuConsumption > 1 and \
           node.currentFormalMemConsumption > 1:
           return
        # assert node.currentRealMemConsumption > 1
        # assert node.currentRealCpuConsumption > 1
    raise Exception("Could not find valid nodes")

def test_nodes_pods_allocated():
    "test that all pods in status running are allocated to nodes"
    pass

# @pytest.mark.skip(reason="need to test everything else first")
def test_eviction_fromfiles_strictgoal():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    p = SingleGoalEvictionDetect(k.state_objects)
    p.select_target_service()
    p.print_objects()
    p.run(timeout=360, sessionName="test_eviction_fromfiles_strictgoal")
    # p.run(timeout=60)
    if not p.plan:
        # print("Could not solve %s" % p.__class__.__name__)
        raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    if p.plan:
        i=0
        for a in p.plan:
            i=i+1
            print(i,":",a.__class__.__name__,"\n",yaml.dump({str(k):repr(v._get_value()) if v else f"NONE_VALUE:{v}" for (k,v) in a.kwargs.items()}, default_flow_style=False))

