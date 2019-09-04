from typing import Set
from guardctl.model.system.primitives import Label
from guardctl.model.system.base import HasLabel
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem

class Node(HasLabel):
    # k8s attributes
    metadata_ownerReferences__name: str
    metadata_name: str
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
    
    @property
    def status_capacity_memory(self):
        pass
    @status_capacity_memory.setter
    def status_capacity_memory(self, value):
        if value == -1: value = 0
        self.memCapacity = memConvertToAbstractProblem(value)

    # @property
    # def status_capacity_cpu(self):
    #     pass
    # @status_capacity_cpu.setter
    # def status_capacity_cpu(self, value):
    #     if value == -1: value = 0
    #     self.cpuCapacity = cpuConvertToAbstractProblem(value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isNull = False

    # def __repr__(self):
    #     return 'Nodename : ' + str(self._get_value()) 


Node.NODE_NULL = Node("NULL")
Node.NODE_NULL.isNull = True

