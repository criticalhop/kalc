from poodle import Object
from guardctl.model.system.primitives import Type, Status
from guardctl.model.kinds.Node import Node


class GlobalVar(Object):
    is_depl_interrupted: bool
    is_service_interrupted: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_service_interrupted = False
        