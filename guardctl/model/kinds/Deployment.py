from guardctl.model.system.Controller import Controller
from guardctl.model.system.base import HasLimitsRequests

class Deployment(Controller, HasLimitsRequests):
    spec_replicas: int

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


    def hook_after_create(self, object_space):
        # TODO
        pass

