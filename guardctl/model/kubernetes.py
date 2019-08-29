import yaml
from guardctl.importers.problemConfigLoad import KubernetesYAMLLoad
from collections import defaultdict
from guardctl.model.object.k8s_classes import Service, Label, Pod, Service, Deployment
from guardctl.misc.object_factory import labelFactory
from poodle import planned, Property, Relation
from guardctl.misc.util import dget, objwalk, find_property, k8s_to_domain_object
from guardctl.model.full import FullModel
import guardctl.model.object.k8s_classes

class KubernetesCluster:
    def __init__(self):
        self.dict_states = defaultdict(list)
        self.state_objects = []

    def load_state(self, conf: str):
        "Load kubernetes state from file"
        d = yaml.safe_load(conf)
        for item in d["items"]:
            self.dict_states[item["kind"]].append(item)
    
    def load_kind(self, kind):
        for item in self.dict_states[kind]: 
            self.state_objects.append(getattr(self, "load_%s" % kind.lower())(item))

    def build_state(self):
        "After loading all configs, we build the state space"
        CONTROLLERS = ["Service", "Deployment"]
        for kind in ["Node"] + CONTROLLERS + ["Pod"]:
            self.load_kind(kind)

    def load(self, str_, create=False):
        for doc in yaml.load_all(str_):
            if "items" in doc:
                for item in doc["items"]: self.load_item(item, create)
            else: self.load_item(doc)
    
    def load_item(self, item, create=False):
        obj = getattr(guardctl.model.object.k8s_classes, item["kind"])()
        obj.kubeguard_created = create # special property to distinguish "created"
        for prop in objwalk(item):
            p, val = find_property(obj, prop)
            if p is None: continue
            val = k8s_to_domain_object(val)
            if isinstance(getattr(obj, p), Property):
                setattr(obj, p, val)
            elif isinstance(getattr(obj, p), Relation):
                getattr(obj, p).add(val)
            else:
                # means has setter
                setattr(obj, p, val)
        if create and hasattr(obj, "hook_after_create"):
            obj.hook_after_create(self.state_objects)

        
    #########################################
    # Loading of different kinds: load_{kind}
    #

    def load_pod(self, podk):
        # TODO: load priority, priorityClassName
        pod = KubernetesYAMLLoad()._loadPodFromDict(podk)
        for name, value in dget(podk, "metadata/labels", None).items():
            pod.labels.add(labelFactory.get(name, value))
        return pod
    
    def load_node(self, node):
        n = KubernetesYAMLLoad()._loadNodeFromDict(node)
        for name, value in dget(node, "metadata/labels", None).items():
            n.labels.add(labelFactory.get(name, value))
        return n

    def load_service(self, service: dict):
        s = Service(service["name"])
        s.nameString = service["name"]
        for name, value in dget(service, "metadata/labels", None).items():
            s.labels.add(labelFactory.get(name, value))
        for name, value in dget(service, "spec/selector", None).items():
            s.selector = labelFactory.get(name, value) # TODO: complex selector suport
        return s
        
    def load_deployment(self, deployment: dict):
        name = dget(deployment, "metadata/name", "NO_NAME")
        d = Deployment(name)
        d.nameString = name
        for name, value in dget(deployment, "metadata/labels", None).items():
            d.labels.add(labelFactory.get(name, value))
        return d
    
    # TODO HERE: load priority!
    # TODO: add priority to knowledge propagation

    #
    #########################################

    def create_resource(self, res: str):
        self.load(res, create=True)
    
    def fetch_state_default(self):
        "Fetch state from cluster using default method"
        raise

    def run(self):
        plan = FullModel(self.state_objects).run()
        # TODO: represent plan
    