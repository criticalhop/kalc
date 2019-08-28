import yaml
from guardctl.importers.problemConfigLoad import KubernetesYAMLLoad
from collections import defaultdict
from guardctl.model.object.k8s_classes import Service, Label, Pod, Service, Deployment

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
        for item in self.dict_states[kind]: getattr(self, "load_%s" % kind.lower())(item)

    def build_state(self):
        "After loading all configs, we build the state space"
        for kind in ["Node", "Pod", "Service", "Deployment"]:
            self.load_kind(kind)
        self.connect_pods_services()

    def connect_pods_services(self):
        xchain(methods=[self.connect_pod_service], space=self.state_objects)
    
    @planned
    def connect_pod_service(self, 
            pod: Pod,  
            service: Service, 
            deployment: Deployment,
            label: Label):
        assert deployment == pod.owner
        assert label in deployment.labels
        assert label in service.labels
        pod.targetService = service

    #########################################
    # Loading of different kinds
    #

    def load_pod(self, podk):
        kl = KubernetesYAMLLoad()
        self.state_objects.append(kl._loadPodFromDict(podk))
    
    def load_node(self, node):
        kl = KubernetesYAMLLoad()
        self.state_objects.append(kl._loadNodeFromDict(node))

    def load_service(self, service: dict):
        s = Service()
        for name, value in service["labels"].items():
            l = Label()
            l.name = name
            l.value = value
            s.labels.add(l)
    
    #
    #########################################

    def create_resource(self, res: str):
        raise
    
    def fetch_default(self):
        raise
    