import random
from poodle import Object
from guardctl.model.system.primitives import TypePolicy
from guardctl.misc.const import *
from guardctl.misc.util import convertPriorityValue


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
        self.priority = convertPriorityValue(value)
        
    def __str__(self): return str(self._get_value())

zeroPriorityClass = PriorityClass("ZERO")
zeroPriorityClass.metadata_name = "Normal-zero"
