from poodle import * 
from  guardctl.model.problem.goals import *
from guardctl.importers.poodleGen import *
from guardctl.importers.problemConfigLoad import *

daemonYAMLPath = "./tests/kube-config/daemon-set-custom.yaml"
serviceYAMLPath = "./tests/kube-config/guestbook-all-in-one.yaml"

def test():
    dumpList = [daemonYAMLPath, './examples/currentCloud/coreV1_api_list_node.yaml', './examples/currentCloud/coreV1_api_list_pod_for_all_namespaces.yaml',  './examples/currentCloud/coreV1_list_service_for_all_namespaces.yaml','./examples/currentCloud/shV1beta1_api_list_priority_class.yaml']
    tests = [TestServiceInterrupted(*dumpList)]
    for t in tests: t.run()
    import yaml
    for p in tests:
        if not p.plan: 
            print("Could not solve %s" % p.__class__.__name__)
            continue
        print("Created plan for %s:" % p.__class__.__name__)
        i=0
        for a in p.plan:
            i=i+1
            print(i,":",a.__class__.__name__,"\n",yaml.dump({k:v.value if v else f"NONE{v}" for (k,v) in a.kwargs.items()}, default_flow_style=False))