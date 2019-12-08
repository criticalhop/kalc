from typing import Set
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from kalc.model.system.primitives import Label
from kalc.misc.object_factory import labelFactory
from kalc.misc.const import *

from poodle import Object


class HasLabel(Object):
    metadata_labels: Set[Label]
    metadata_name: str

class HasLimitsRequests(Object):
    """A mixin class to implement Limts/Requests loading and initialiaztion"""
    memRequest: int
    cpuRequest: int
    memLimit: int
    memLimitsStatus: StatusLim
    """Status to set if the limit is reached"""
    cpuLimit: int
    cpuLimitsStatus: StatusLim
    """Status to set if the limit is reached"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cpuLimit = -1
        self.memLimit = -1
        self.cpuRequest = -1
        self.memRequest = -1
        self.memLimitsStatus = STATUS_LIM["Limit Met"]
        self.cpuLimitsStatus = STATUS_LIM["Limit Met"]

    @property
    def spec_template_spec_containers__resources_limits_cpu(self):
        pass
    @spec_template_spec_containers__resources_limits_cpu.setter
    def spec_template_spec_containers__resources_limits_cpu(self, res):
        if self.cpuLimit == -1: self.cpuLimit = 0
        self.cpuLimit += cpuConvertToAbstractProblem(res)

    @property
    def spec_template_spec_containers__resources_limits_memory(self):
        pass
    @spec_template_spec_containers__resources_limits_memory.setter
    def spec_template_spec_containers__resources_limits_memory(self, res):
        if self.memLimit == -1: self.memLimit = 0
        self.memLimit += memConvertToAbstractProblem(res)

    @property
    def spec_template_spec_containers__resources_requests_cpu(self):
        pass
    @spec_template_spec_containers__resources_requests_cpu.setter
    def spec_template_spec_containers__resources_requests_cpu(self, res):
        if self.cpuRequest == -1: self.cpuRequest = 0
        self.cpuRequest += cpuConvertToAbstractProblem(res)

    @property
    def spec_template_spec_containers__resources_requests_memory(self):
        pass
    @spec_template_spec_containers__resources_requests_memory.setter
    def spec_template_spec_containers__resources_requests_memory(self, res):
        if self.memRequest == -1: self.memRequest = 0
        self.memRequest += memConvertToAbstractProblem(res)
