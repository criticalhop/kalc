import random
from typing import Set
from guardctl.model.system.primitives import Label, StatusServ
import guardctl.model.kinds.Pod as mpod
from guardctl.model.system.base import HasLabel
import guardctl.model.kinds.Node as mnode
from guardctl.model.system.primitives import StatusSched
from guardctl.misc.const import *


class Service(HasLabel):
    spec_selector: Set[Label]
    amountOfActivePods: int
    amountOfPodsInQueue: int
    status: StatusServ
    metadata_name: str
    searchable: bool
    isNull: bool
    isSearched: bool
    podList: Set["mpod.Pod"]
    antiaffinity: bool
    not_present_at_node: Set["mnode.Node"]
    affinity_met: bool
    
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.metadata_name = "modelService"+str(random.randint(100000000, 999999999))
        # self.metadata_name = "model-default-name"
        self.amountOfActivePods = 0
        self.status = STATUS_SERV["Pending"]
        self.searchable = True
        self.isNull = False
        self.isSearched = False
        self.amountOfPodsInQueue = 0
        self.antiaffinity = False
        self.affinity_met = False
    
    def __str__(self): return str(self.metadata_name)
    
    def hook_after_load(self, object_space, _ignore_orphan=False):
        nodes = list(filter(lambda x: isinstance(x, mnode.Node), object_space))
        for node in nodes:
                self.not_present_at_node.add(node)
    # def __repr__(self):
    #     return 'Servicename : ' + str(self._get_value()) 

Service.SERVICE_NULL = Service("NULL")
Service.SERVICE_NULL.metadata_name = "Null-Service"
Service.SERVICE_NULL.isNull = True
Service.SERVICE_NULL.searchable == False


