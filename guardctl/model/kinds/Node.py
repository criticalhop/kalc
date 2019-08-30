from typing import Set
from guardctl.model.system.primitives import *
from guardctl.model.system.base import HasLabel

class Node(HasLabel):
    def __init__(self, value=""):
        super().__init__(self, value)
        self.isNull = False
    # k8s attributes
    metadata_ownerReferences__name: String
    spec_priorityClassName: String
    labels: Set[Label]
    cpuCapacity: int
    memCapacity: int
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    AmountOfPodsOverwhelmingMemLimits: int
    podAmount: int
    isNull: bool
    status: String
Node.NODE_NULL = Node("NULL")
Node.NODE_NULL.isNull = True

