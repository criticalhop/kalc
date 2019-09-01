import pytest
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8SearchEviction
from guardctl.misc.object_factory import stringFactory, labelFactory
from guardctl.misc.problem import ProblemTemplate
from guardctl.model.kinds.PriorityClass import PriorityClass

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

class ProblemMixer(KubernetesCluster, ProblemTemplate):

    def __init__(self):
        KubernetesCluster.__init__(self)
        ProblemTemplate.__init__(self, self.state_objects)


class SingleGoalEvictionDetect(K8SearchEviction):
    def goal(self):
        # for ob in self.objectList:
        #     print(str(ob))

        evict_service = next(filter(lambda x: isinstance(x, Service) and \
            labelFactory.get("app", "redis-evict") in x.spec_selector._get_value(),
            self.objectList))
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        return evict_service.status == STATUS_SERV_INTERRUPTED and \
                                    scheduler.status == STATUS_SCHED_CLEAN

PRIORITY = {'high-priority':1000000, 'system-cluster-critical': 2000000000, 'system-node-critical': 2000001000}

def test_cluster_folder():
    mix = ProblemMixer()
    mix.load_dir(TEST_CLUSTER_FOLDER)
    mix._build_state()
    mix.fillObjectLists()
    assert(len(mix.pod) == 8)
    assert(len(mix.node) == 5)
    assert(len(mix.service) == 6)
    have_high_priority=False
    for priorityClass in mix.state_objects:
        if isinstance(priorityClass, PriorityClass):
            if priorityClass.metadata_name in PRIORITY:
                have_high_priority = True
                assert(priorityClass.priority == (1000 if PRIORITY[priorityClass.metadata_name] > 1000 else PRIORITY[priorityClass.metadata_name]))
    assert(have_high_priority)
    

def test_daemonset_folder():
    mix = ProblemMixer()
    mix.load_dir(TEST_CLUSTER_FOLDER)
    mix.create_resource(open(TEST_DAEMONET).read())
    mix._build_state()
    mix.fillObjectLists()
    assert(len(mix.pod) == 8 + len(mix.node))
    assert(len(mix.node) == 5)
    assert(len(mix.service) == 6) 

