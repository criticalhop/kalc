from kalc.model.system.base import ModularKind

class NameSpace(ModularKind):
    # k8s attributes
    metadata_name: str
    # spec_finalizers__kubernetes
    status_phase: str #Active
