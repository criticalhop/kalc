import sys
import random
from guardctl.model.scenario import ScenarioStep, describe
from typing import Set
from guardctl.model.system.primitives import Label, StatusNode
from guardctl.model.system.base import HasLabel
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from guardctl.misc.const import STATUS_NODE
from guardctl.model.scenario import ScenarioStep, describe


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
    status: StatusNode
    amountOfActivePods: int
    searchable: bool
    isSearched: bool
    different_than: Set["Node"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata_name = "modelNode"+str(random.randint(100000000, 999999999))
        # self.metadata_name = "model-default-name"
        self.AmountOfPodsOverwhelmingMemLimits = 0
        self.currentFormalCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentRealCpuConsumption = 0
        self.currentRealMemConsumption = 0
        self.cpuCapacity = 0
        self.memCapacity = 0
        self.isNull = False
        self.status = STATUS_NODE["Active"]
        self.amountOfActivePods = 0
        self.searchable = True
        self.isSearched = False
        
    def hook_after_create(self, object_space):
        nodes = filter(lambda x: isinstance(x, Node), object_space)
        for node in nodes:
            if node != self:
                self.different_than.add(node)

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

    def __str__(self):
        if str(self.metadata_name) == "None":
            return "<unnamed node>"
        return str(self.metadata_name)
    # def __repr__(self):
    #     return 'Nodename : ' + str(self._get_value()) 

Node.NODE_NULL = Node("NULL")
Node.NODE_NULL.isNull = True
Node.NODE_NULL.metadata_name = "Null-Node"
Node.NODE_NULL.searchable = False

