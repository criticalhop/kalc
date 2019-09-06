from poodle import planned
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Pod import Pod
from guardctl.misc.const import *
from guardctl.misc.problem import ProblemTemplate
from guardctl.model.scenario import ScenarioStep, describe
import sys


class KubernetesModel(ProblemTemplate):
    def problem(self):
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        self.globalVar = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

class K8ServiceInterruptSearch(KubernetesModel):
    @planned
    def MarkServiceOutageEvent(self,
                service1: Service,
                pod1: Pod,
                global_: "GlobalVar",
                scheduler1: "Scheduler",
                currentFormalCpuConsumptionLoc: int,
                currentFormalMemConsumptionLoc: int,
                cpuCapacityLoc:int,
                memCapacityLoc:int,
                cpuRequestLoc: int,
                memRequestLoc: int
            ):
        assert scheduler1.status == STATUS_SCHED["Clean"] 
        assert service1.amountOfActivePods == 0
        assert service1.status == STATUS_SERV["Started"]
        assert pod1.targetService == service1
        # assert globalVar1.currentFormalCpuConsumption == currentFormalCpuConsumptionLoc
        # assert globalVar1.currentFormalMemConsumption == currentFormalMemConsumptionLoc
        assert pod1.cpuRequest == cpuRequestLoc
        assert pod1.memRequest == memRequestLoc
        # assert globalVar1.cpuCapacity == cpuCapacityLoc 
        # assert globalVar1.memCapacity == memCapacityLoc 
        #### assert globalVar1.currentFormalCpuConsumption + pod1.cpuRequest > globalVar1.cpuCapacity
        # assert globalVar1.currentFormalMemConsumption + pod1.memRequest > globalVar1.memCapacity

        service1.status = STATUS_SERV["Interrupted"]
        global_.is_service_interrupted = True
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Detected service outage event",
            parameters={"service.amountOfActivePods": 0, "service": describe(service1)},
            probability=1.0,
            affected=[describe(service1)]
        )
    

    
    # @planned(cost=10000)
    # def UnsolveableServiceStart(self,
    #             service1: Service,
    #             scheduler1: "mscheduler.Scheduler"
    #         ):
    #     assert scheduler1.status == STATUS_SCHED["Changed"] 
    #     service1.status = STATUS_SERV["Started"]
    
    @planned(cost=100)
    def PodsConnectedToServices(self,
                service1: Service,
                scheduler1: "mscheduler.Scheduler"
            ):
        assert service1.amountOfActivePods > 0
        service1.status = STATUS_SERV["Started"]
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Mark service as started",
            parameters={},
            probability=1.0,
            affected=[describe(service1)]
        )

    def goal(self):
        # TODO: find and define service or fix domain!
        self.service[0].status == STATUS_SERV["Interrupted"] and \
            self.scheduler.status == STATUS_SCHED["Clean"]

class AnyServiceInterrupted(K8ServiceInterruptSearch):

    goal = lambda self: self.globalVar.is_service_interrupted == True and \
            self.scheduler.status == STATUS_SCHED["Clean"]

