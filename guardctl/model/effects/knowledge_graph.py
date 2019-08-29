from poodle import planned 
from guardctl.model.effects.abstract import Effect
from guardctl.model.object.k8s_classes import Pod, Service, Deployment, Label, PriorityClass

class KnowledgeGraph(Effect):
    # @planned
    # def connect_pod_service_internal(self, 
    #         pod: Pod,  
    #         service: Service, 
    #         deployment: Deployment,
    #         label: Label):
    #     assert deployment == pod.ownerReferences
    #     assert label in deployment.labels
    #     assert label == service.selector
    #     pod.targetService = service

    @planned
    def connect_pod_service_labels(self, 
            pod: Pod,  
            service: Service, 
            label: Label):
        # TODO: full selector support
        assert pod.targetService == pod.TARGET_SERVICE_NULL
        assert label in pod.metadata_labels
        assert label in service.spec_selector
        pod.targetService = service
        service.amountOfActivePods += 1
    
    @planned 
    def fill_priority_class_object(self,
            pod: Pod,
            pclass: PriorityClass):
        assert pod.spec_priorityClassName == pclass.metadata_name
        pod.priorityClass = pclass
