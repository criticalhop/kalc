import yaml
from guardctl.importers.problemConfigLoad import KubernetesYAMLLoad

class KubernetesCluster:
    def __init__(self):
        self.dict_states = []
        self.state_objects = []
    def load_conf(self, conf: str):
        d = yaml.safe_load(conf)
        self.dict_states.append(d)
        for item in d["items"]:
            if item["kind"] == "Pod": self.load_pod(item)
            # if item["kind"] == "Service": self.load_service(item)
    
    def load_pod(self, podk):
        kl = KubernetesYAMLLoad()
        self.state_objects.append(kl._loadPodFromDict(podk))

    def create_resource(self, res: str):
        raise
    
    def fetch_default(self):
        raise
    