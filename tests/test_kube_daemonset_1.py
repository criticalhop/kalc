import pytest
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.misc.object_factory import labelFactory
from  tests.problem.goals import *
import yaml
from poodle.schedule import EmptyPlanError
# from mem_top import mem_top

def test_eviction_synthetic():
    p = TestServiceInterrupted()
    p.run(timeout=90, sessionName="test_eviction_synthetic")
    assert len(list(filter(lambda x: isinstance(x, Pod), p.objectList))) == 7
    # print("PODS:", len(list(filter(lambda x: isinstance(x, Pod), p.objectList))))
    if not p.plan: 
        # print("Could not solve %s" % p.__class__.__name__)
        raise Exception("Could not solve %s" % p.__class__.__name__)
    if p.plan:
        i=0
        for a in p.plan:
            i=i+1
            # print(i,":",a.__class__.__name__,"\n",yaml.dump({str(k):repr(v._get_value()) if v else f"NONE_VALUE:{v}" for (k,v) in a.kwargs.items()}, default_flow_style=False))
