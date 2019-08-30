from guardctl.misc.util import objwalk, find_property
from poodle import Object
import yaml
from typing import Set

TEST_PODS = "./tests/kube-config/pods.yaml"

class Label2(Object):
    pass
class HasLabel2(Object):
    metadata_labels: Set[Label2]

class Pod2(HasLabel2):
    metadata_ownerReferences__name: int

def test_find_prop():
    found = []
    for doc in yaml.load_all(open(TEST_PODS)):
        for item in doc["items"]:
            for p in objwalk(item):
                obj = "Pod",2()
                p, val = find_property(obj, p)
                found.append([p,val])
            # print(found)
            break
    assert ['metadata_labels', {'controller-revision-hash': '7668596989'}] in found and \
        ['metadata_ownerReferences__name', 'fluentd-elasticsearch'] in found
