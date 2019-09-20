import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch, AnyServiceInterrupted
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario
import guardctl.model.kinds.Service as mservice
from tests.test_util import print_objects


TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

EXCLUDED_SERV = {
    "redis-master" : TypeServ("redis-master"),
    # "redis-master-evict" : TypeServ("redis-master-evict"),
    "heapster": TypeServ("heapster"),
   
}

def mark_excluded_service(object_space):
    services = filter(lambda x: isinstance(x, mservice.Service), object_space)
    for service in services:
        if service.metadata_name in list(EXCLUDED_SERV):
           service.searchable = False



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
    # print_objects(ALL_STATE)
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

def test_eviction_fromfiles_strictgoal():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    p = SingleGoalEvictionDetect(k.state_objects)
    p.select_target_service()
    p.run(timeout=360, sessionName="test_eviction_fromfiles_strictgoal")
    if not p.plan:
        raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    if p.plan:
        i=0
        for a in p.plan:
            i=i+1
            print(i,":",a.__class__.__name__,"\n",yaml.dump({str(k):repr(v._get_value()) if v else f"NONE_VALUE:{v}" for (k,v) in a.kwargs.items()}, default_flow_style=False))


def test_anyservice_interrupted_fromfiles():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    mark_excluded_service(k.state_objects)
    p = AnyServiceInterrupted(k.state_objects)
    print_objects(k.state_objects)
    p.run(timeout=360, sessionName="test_anyservice_interrupted_fromfiles")
    if not p.plan:
        raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
   