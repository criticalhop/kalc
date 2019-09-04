from poodle import Object
from guardctl.model.system.primitives import Type


class PriorityClass(Object):
    metadata_name: str

    priority: int
    preemptionPolicy: Type

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

    @property
    def value(self):
        pass
    @value.setter 
    def value(self, value):
        if value > 1000: value = 1000
        self.priority = value


