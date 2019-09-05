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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.AmountOfPodsOverwhelmingMemLimits = 0
        self.currentFormalCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentRealCpuConsumption = 0
        self.currentRealMemConsumption = 0
        self.cpuCapacity = 0
        self.memCapacity = 0
        self.isNull = False
    
    @property
    def status_allocatable_memory(self):
        pass
    @status_allocatable_memory.setter
    def status_allocatable_memory(self, value):
        self.memCapacity = memConvertToAbstractProblem(value)

    @property
    def status_allocatable_cpu(self):
        pass
    @status_allocatable_cpu.setter
    def status_allocatable_cpu(self, value):
        self.cpuCapacity = cpuConvertToAbstractProblem(value)

    # def __repr__(self):
    #     return 'Nodename : ' + str(self._get_value()) 


Node.NODE_NULL = Node("NULL")
Node.NODE_NULL.isNull = True

