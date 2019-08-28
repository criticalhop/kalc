from poodle import planned 
from guardctl.model.effects.abstract import Effect
from guardctl.model.object.k8s_classes import Pod, Service, Deployment, Label

class KnowledgeGraph(Effect):
    @planned
    def connect_pod_service(self, 
            pod: Pod,  
            service: Service, 
            deployment: Deployment,
            label: Label):
        assert deployment == pod.ownerReferences
        assert label in deployment.labels
        assert label == service.selector
        pod.targetService = service
