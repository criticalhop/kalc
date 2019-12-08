import random
from typing import Set
from kalc.model.system.primitives import Label, StatusServ
import kalc.model.kinds.Pod as mpod
from kalc.model.system.base import HasLabel
import kalc.model.kinds.Pod as mpod
from kalc.model.system.primitives import StatusSched
from kalc.misc.const import *


class Service(HasLabel):
    spec_selector: Set[Label]
    amountOfActivePods: int
    amountOfPodsInQueue: int
    amountOfPodsOnDifferentNodes: int
    targetAmountOfPodsOnDifferentNodes: int
    status: StatusServ
    metadata_name: str
    searchable: bool
    isNull: bool
    isSearched: bool
    podList: Set["mpod.Pod"]
    antiaffinity: bool
    policy_antiaffinity_prefered : bool
    antiaffinity_prefered_policy_met: bool
    
    
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
        self.amountOfPodsOnDifferentNodes = 0
        self.targetAmountOfPodsOnDifferentNodes = 0
        self.policy_antiaffinity_prefered = False    
    def __str__(self): return str(self.metadata_name)

    # def __repr__(self):
    #     return 'Servicename : ' + str(self._get_value()) 

Service.SERVICE_NULL = Service("NULL")
Service.SERVICE_NULL.metadata_name = "Null-Service"
Service.SERVICE_NULL.isNull = True
Service.SERVICE_NULL.searchable == False


