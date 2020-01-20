import pytest
from kalc.model.kubernetes import KubernetesCluster
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.system.Scheduler import Scheduler
from kalc.misc.const import *
from kalc.model.search import K8ServiceInterruptSearch
from kalc.misc.object_factory import labelFactory
from kalc.misc.problem import ProblemTemplate
from kalc.model.kinds.PriorityClass import PriorityClass

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

class ProblemMixer(KubernetesCluster, ProblemTemplate):

    def __init__(self):
        KubernetesCluster.__init__(self)
        ProblemTemplate.__init__(self, self.state_objects)


class SingleGoalEvictionDetect(K8ServiceInterruptSearch):
    def goal(self):
        # for ob in self.objectList:
        #     print(str(ob))

        evict_service = next(filter(lambda x: isinstance(x, Service) and \
            labelFactory.get("app", "redis-evict") in x.spec_selector._get_value(),
            self.objectList))
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        return evict_service.status == STATUS_SERV["Interrupted"] and \
                                    scheduler.status == STATUS_SCHED["Clean"]

PRIORITY = {'high-priority':1000000, 'system-cluster-critical': 2000000000, 'system-node-critical': 2000001000}

# def test_cluster_folder():
#     mix = ProblemMixer()
#     mix.load_dir(TEST_CLUSTER_FOLDER)
#     mix._build_state()
#     mix.fillObjectLists()
#     assert(len(mix.pod) == 32)
#     assert(len(mix.node) == 5)
#     assert(len(mix.service) == 10)
#     have_high_priority=False
#     for priorityClass in mix.state_objects:
#         if isinstance(priorityClass, PriorityClass):
#             if priorityClass.metadata_name == 'high-priority':
#                 have_high_priority = True
#                 assert(priorityClass.priority == (1000 if PRIORITY[str(priorityClass.metadata_name)] >= 1000 else PRIORITY[str(priorityClass.metadata_name)]))
#     assert(have_high_priority)
    

def test_daemonset_folder():
    mix = ProblemMixer()
    mix.load_dir(TEST_CLUSTER_FOLDER)
    mix.create_resource(open(TEST_DAEMONET).read())
    mix._build_state()
    mix.fillObjectLists()
    assert(len(mix.pod) == 37 - 5 + len(mix.node))
    assert(len(mix.node) == 5)
    assert(len(mix.service) == 10) 

