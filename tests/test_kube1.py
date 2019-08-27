from poodle import * 
from  guardctl.model.problem.goals import *
from guardctl.importers.poodleGen import *
from guardctl.importers.problemConfigLoad import *

daemonYAMLPath = "./tests/kube-config/daemon-set-custom.yaml"
serviceYAMLPath = "./tests/kube-config/guestbook-all-in-one.yaml"

def test():

    tests = [TestServiceInterrupted()]
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