import subprocess
import json
from poodle import Object
from kalc.model.full import kinds_collection
from kalc.misc.kind_filter import FilterByLabelKey, FilterByName, KindPlaceholder
from kalc.model.kubernetes import KubernetesCluster

kalc_state_objects = []
kind = KindPlaceholder

for k, v in kinds_collection.items():
    v.by_name = FilterByName(k, kalc_state_objects)
    v.by_label = FilterByLabelKey(k, kalc_state_objects)
    globals()[k] = v
    setattr(kind, k, v)

def update():
    "Fetch information from currently selected ccluster"
    result = subprocess.run(['kubectl', 'get', 'all', '-o=json'], stdout=subprocess.PIPE)
    data = json.loads(result.stdout.decode("utf-8"))
    k = KubernetesCluster()
    for item in data["items"]:
        k.load_item(item)
    k._build_state()
    global kalc_state_objects
    kalc_state_objects.clear()
    kalc_state_objects.extend(k.state_objects)
