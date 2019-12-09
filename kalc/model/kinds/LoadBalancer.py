from poodle import * 
from kalc.model.system.base import ModularKind
from kalc.model.system.Controller import Controller
from kalc.model.system.base import HasLimitsRequests
from kalc.model.kinds.Node import Node
import kalc.model.kinds.Pod as mpod
from kalc.model.system.primitives import Status


class LoadBalancer(ModularKind):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
    