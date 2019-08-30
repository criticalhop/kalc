from typing import Set
from guardctl.model.system.primitives import Label, StatusServ
from guardctl.model.kinds.Node import Node
from guardctl.model.system.base import HasLabel
import guardctl.model.kinds.Pod as mpod
from guardctl.model.system.primitives import StatusSched, String


class Service(HasLabel):
    spec_selector: Set[Label]
    lastPod: "mpod.Pod"
    atNode: Node
    amountOfActivePods: int
    status: String
    
    def __init__(self, value=""):
        super().__init__(self, value)
        self.amountOfActivePods = 0

Service.SERVICE_NULL = Service("NULL")
