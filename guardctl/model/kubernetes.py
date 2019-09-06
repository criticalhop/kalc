import yaml
import os
from collections import defaultdict
from guardctl.misc.object_factory import labelFactory
from poodle import planned, Property, Relation
from guardctl.misc.util import dget, objwalk, find_property, k8s_to_domain_object
from guardctl.model.full import kinds_collection
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.model.system.globals import GlobalVar
from guardctl.model.system.Scheduler import Scheduler

KINDS_LOAD_ORDER = ["PriorityClass", "Service", "Node", "Pod"]

class KubernetesCluster:
    def __init__(self):
        self.dict_states = defaultdict(list)
        self._reset()

    def _reset(self):
        "Reset object states and require a rebuild with _bulid_state"
        self.state_objects = [Scheduler(), GlobalVar()]

    def load_dir(self, dir_path):
        for root, dirs, files in os.walk(dir_path):
            for fn in files:
                self.load(open(os.path.join(root, fn)).read())

    def load(self, str_, create=False):
        for doc in yaml.load_all(str_, Loader=yaml.FullLoader):
            if "items" in doc:
                for item in doc["items"]: self.load_item(item, create)
            else: self.load_item(doc, create)

    def load_item(self, item, create=False):
        assert isinstance(item, dict), item
        item["__created"] = create
        self.dict_states[item["kind"]].append(item)

    def _build_item(self, item):
        obj = kinds_collection[item["kind"]]()
        create = item["__created"]
        obj.kubeguard_created = create # special property to distinguish "created"
        for prop in objwalk(item):
            p, val = find_property(obj, prop)
            if p is None: continue
            val = k8s_to_domain_object(val)
            if isinstance(getattr(obj, p), Relation):
                getattr(obj, p).add(val)
            elif isinstance(getattr(obj, p), Property):
                setattr(obj, p, val)
            else:
                # means has setter
                setattr(obj, p, val)
        if create and hasattr(obj, "hook_after_create"):
            obj.hook_after_create(self.state_objects)
        if not create and hasattr(obj, "hook_after_load"):
            obj.hook_after_load(self.state_objects)
        self.state_objects.append(obj)

    def _build_state(self):
        collected = self.dict_states.copy()
        for k in KINDS_LOAD_ORDER:
            if not k in collected: continue
            for item in collected[k]:
                self._build_item(item)
            del collected[k]
        for k,v in collected.items():
            for item in v:
                self._build_item(item)

    def create_resource(self, res: str):
        self.load(res, create=True)

    def fetch_state_default(self):
        "Fetch state from cluster using default method"
        raise NotImplementedError()

    def run(self):
        if len(self.state_objects) < 3: self._build_state()
        k = K8ServiceInterruptSearch(self.state_objects)
        k.run()
        self.plan = k.plan
        return self.plan
        # TODO: represent plan

