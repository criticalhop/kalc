from typing import Set
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from guardctl.model.system.primitives import String, Label
from guardctl.misc.object_factory import labelFactory, stringFactory

from poodle import Object


class HasLabel(Object):
    metadata_labels: Set[Label]
    metadata_name: String

class HasLimitsRequests(Object):
    """A mixin class to implement Limts/Requests loading and initialiaztion"""
    memRequest: int
    cpuRequest: int
    memLimit: int
    memLimitsStatus: String
    """Status to set if the limit is reached"""
    cpuLimit: int
    cpuLimitsStatus: String
    """Status to set if the limit is reached"""

    def __init__(self, value = ''):
        super().__init__(value)
        self.cpuLimit = -1
        self.memLimit = -1
        self.cpuRequest = -1
        self.memRequest = -1
        self.memLimitsStatus = stringFactory.get("Limits_met")
        self.cpuLimitsStatus = stringFactory.get("Limits_met")

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
