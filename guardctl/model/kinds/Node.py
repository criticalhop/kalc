from typing import Set
from guardctl.model.system.primitives import Label, StatusNode, State, Type

class Node(HasLabel):
    labels: Set[Label]
    cpuCapacity: int
    memCapacity: int
    memCapacityBarier: int
    status: StatusNode
    state: State
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    AmountOfPodsOverwhelmingMemLimits: int
    podAmount: int
    type: Type

