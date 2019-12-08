import random
from poodle import Object
from kalc.model.system.primitives import TypePolicy
from kalc.misc.const import *
from kalc.misc.util import convertPriorityValue


class PriorityClass(Object):
    metadata_name: str

    priority: int
    preemptionPolicy: TypePolicy

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.metadata_name = "modelPriorityClass"+str(random.randint(100000000, 999999999))
        # self.metadata_name = "model-default-name"
        self.preemptionPolicy = POLICY["PreemptLowerPriority"]
        self.priority = 0

    @property
    def value(self):
        pass
    @value.setter 
    def value(self, value):
        norm_pri = convertPriorityValue(value)
        if norm_pri > 1000: norm_pri = 1000
        self.priority = norm_pri
        
    def __str__(self): return str(self._get_value())

zeroPriorityClass = PriorityClass("ZERO")
zeroPriorityClass.metadata_name = "Normal-zero"
