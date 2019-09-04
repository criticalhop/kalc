from typing import Set
from guardctl.model.system.primitives import Label
from guardctl.model.system.base import HasLabel

class Node(HasLabel):
    # k8s attributes
    metadata_ownerReferences__name: str
    spec_priorityClassName: str
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
    status: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isNull = False

    # def __repr__(self):
    #     return 'Nodename : ' + str(self._get_value()) 


Node.NODE_NULL = Node("NULL")
Node.NODE_NULL.isNull = True

