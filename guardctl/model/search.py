from poodle import planned
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Pod import Pod
from guardctl.misc.const import *
from guardctl.misc.problem import ProblemTemplate


class KubernetesModel(ProblemTemplate):
    def problem(self):
        self.scheduler = self.addObject(Scheduler())
        self.globalVar = self.addObject(GlobalVar())

class K8SearchEviction(KubernetesModel):
    @planned
    def MarkServiceOutageEvent(self,
                service1: Service,
                pod1: "Pod",
                globalVar1: "GlobalVar",
                scheduler1: "Scheduler",
                currentFormalCpuConsumptionLoc: int,
                currentFormalMemConsumptionLoc: int,
                cpuRequestLoc: int,
                memRequestLoc: int
            ):
        assert scheduler1.status == STATUS_SCHED_CLEAN 
        assert service1.amountOfActivePods == 0
        assert service1.status == STATUS_SERV_STARTED
        assert pod1.targetService == service1
        assert globalVar1.currentFormalCpuConsumption == currentFormalCpuConsumptionLoc
        assert globalVar1.currentFormalMemConsumption == currentFormalMemConsumptionLoc
        assert pod1.cpuRequest == cpuRequestLoc
        assert pod1.memRequest == memRequestLoc
        assert globalVar1.currentFormalCpuConsumption + pod1.cpuRequest <= globalVar1.cpuCapacity
        assert globalVar1.currentFormalMemConsumption + pod1.memRequest <= globalVar1.memCapacity

        service1.status = STATUS_SERV_INTERRUPTED
    

    
    @planned(cost=10000)
    def UnsolveableServiceStart(self,
                service1: Service,
                scheduler1: "mscheduler.Scheduler"
            ):
        assert scheduler1.status == STATUS_SCHED_CHANGED 
        service1.status = STATUS_SERV_STARTED

    def goal(self):
        self.service[0].status == STATUS_SERV_INTERRUPTED and \
            self.scheduler1.status == STATUS_SCHED_CLEAN

