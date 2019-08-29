from typing import Set
from guardctl.model.system.primitives import Label, StatusNode, State, Type
from guardctl.model.system.base import HasLabel

class Node(HasLabel):
    labels: Set[Label]
    cpuCapacity: int
    memCapacity: int
    memCapacityBarier: int
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    AmountOfPodsOverwhelmingMemLimits: int
    podAmount: int
    type: Type

