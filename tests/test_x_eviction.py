import pytest
import yaml
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8SearchEviction
from guardctl.misc.object_factory import labelFactory

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

class SingleGoalEvictionDetect(K8SearchEviction):
    def goal(self):
        for ob in self.objectList:
            print(str(ob))

        evict_service = next(filter(lambda x: isinstance(x, Service) and \
            labelFactory.get("app", "redis-evict") in x.spec_selector._get_value(),
            self.objectList))
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        pod = next(filter(lambda x: isinstance(x, Pod), self.objectList))
        return  pod.status_phase == STATUS_POD_PENDING   #  evict_service.status == scheduler.status == STATUS_SCHED_CLEAN and STATUS_SERV_INTERRUPTED 
                                    

#@pytest.mark.skip(reason="no way of currently testing this")
def test_eviction_fromfiles_strictgoal():
    k = KubernetesCluster()
    k.load_dir(TEST_CLUSTER_FOLDER)
    k.create_resource(open(TEST_DAEMONET).read())
    k._build_state()
    p = SingleGoalEvictionDetect(k.state_objects)
    p.run()
    if not p.plan: 
        print("Could not solve %s" % p.__class__.__name__)
    if p.plan:
        i=0
        for a in p.plan:
            i=i+1
            print(i,":",a.__class__.__name__,"\n",yaml.dump({str(k):repr(v._get_value()) if v else f"NONE_VALUE:{v}" for (k,v) in a.kwargs.items()}, default_flow_style=False))

