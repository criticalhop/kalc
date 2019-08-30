import yaml
from collections import defaultdict
from guardctl.misc.object_factory import labelFactory
from poodle import planned, Property, Relation
from guardctl.misc.util import dget, objwalk, find_property, k8s_to_domain_object
from guardctl.model.full import kinds_collection
from guardctl.misc.problem import ProblemTemplate

class KubernetesCluster:
    def __init__(self):
        self.dict_states = defaultdict(list)
        self.state_objects = []

    def load(self, str_, create=False):
        for doc in yaml.load_all(str_):
            if "items" in doc:
                for item in doc["items"]: self.load_item(item, create)
            else: self.load_item(doc, create)
    
    def load_item(self, item, create=False):
        self.dict_states[item["kind"]].append(item)
    
    def _build_item(item):
        obj = kinds_collection[item["kind"]]()
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

    def _build_state(self):
        collected = self.dict_states.copy()
        for k in ["Node", "Pod"]:
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
        raise

    def run(self):
        self._build_state()
        plan = ProblemTemplate(self.state_objects).run()
        # TODO: represent plan
    