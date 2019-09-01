import pytest
from poodle import * 
from  tests.problem.goals import *
from guardctl.misc.const import *

daemonYAMLPath = "./tests/kube-config/daemon-set-custom.yaml"
serviceYAMLPath = "./tests/kube-config/guestbook-all-in-one.yaml"

# @pytest.mark.skip(reason="no way of currently testing this")
def test():
    dumpList = [daemonYAMLPath, './examples/currentCloud/coreV1_api_list_node.yaml', './examples/currentCloud/coreV1_api_list_pod_for_all_namespaces.yaml',  './examples/currentCloud/coreV1_list_service_for_all_namespaces.yaml','./examples/currentCloud/shV1beta1_api_list_priority_class.yaml']
    tests = [TestServiceInterrupted()]
    for t in tests: t.run()
    import yaml
    for p in tests:
        if not p.plan: 
            print("Could not solve %s" % p.__class__.__name__)
            print(p)
            continue
        if p.plan:
            print("Created plan for %s:" % p.__class__.__name__)
            print(p)
            assert p.plan