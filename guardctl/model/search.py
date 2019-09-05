from poodle import planned
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Pod import Pod
from guardctl.misc.const import *
from guardctl.misc.problem import ProblemTemplate
     

class KubernetesModel(ProblemTemplate):
    def problem(self):
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        self.globalVar = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

class K8SearchEviction(KubernetesModel):
     

    @planned(cost=10000)
    def MarkServiceInterruptionEvent(self,
                service1: Service,
                scheduler1: "Scheduler",
                globalVar1: GlobalVar
            ):
        assert scheduler1.status == STATUS_SCHED_CLEAN 
        assert service1.amountOfActivePods == 0
        assert service1.status == STATUS_SERV_STARTED
        service1.status = STATUS_SERV_INTERRUPTED
        globalVar1.searchGoal1 = True
    
    @planned(cost=100)
    def Mark_all_pods_started_except_succeeded(self,
                service1: Service,
                scheduler1: "Scheduler",
                globalVar1: GlobalVar
            ):
        pod_loaded_list = filter(lambda x: isinstance(x, Pod), self.objectList)
        for poditem in pod_loaded_list:
            if poditem.status_phase != STATUS_NODE_SUCCEEDED:
                assert poditem.status_phase == STATUS_POD_RUNNING
        globalVar1.searchGoal1 = True

    
    # @planned(cost=10000)
    # def UnsolveableServiceStart(self,
    #             service1: Service,
    #             scheduler1: "mscheduler.Scheduler"
    #         ):
    #     assert scheduler1.status == STATUS_SCHED_CHANGED 
    #     service1.status = STATUS_SERV_STARTED
    
    # @planned(cost=100)
    # def PodsConnectedToServices(self,
    #             service1: Service,
    #             scheduler1: "mscheduler.Scheduler",
    #             pod1: Pod
    #         ):
    #     assert service1.amountOfActivePods > 0
    #     service1.status = STATUS_SERV_STARTED
    
    # def goal(self):
    #     globalVar1 = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))
    #     globalVar1.searchGoal1 = True
    def getGLobalVar(self):
        self.globalVar1 = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

    goal = lambda self: self.globalVar1.searchGoal1 == True

