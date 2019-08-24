class KubernetesCluster:
    def __init__(self):
        pass

    def load_conf(self, conf: str):
        raise NotImplementedError()
    
    def create_resource(self, res: str):
        raise
    
    def fetch_default(self):
        raise
    