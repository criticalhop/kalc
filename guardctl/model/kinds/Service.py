from typing import Set
from guardctl.model.system.primitives import Label, StatusServ
from guardctl.model.kinds.Node import Node
from guardctl.model.system.base import HasLabel


class Service(HasLabel):
    spec_selector: Set[Label]
    lastPod: "Pod"
    atNode: Node
    amountOfActivePods: int
    status: StatusServ
    
    def __init__(self, value):
        super().__init__(self, value)
        self.amountOfActivePods = 0

