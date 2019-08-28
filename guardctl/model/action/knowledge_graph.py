from poodle import planned 
class KnowledgeGraph():
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
