from poodle import planned
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.Pod import Pod
from guardctl.misc.const import *
from guardctl.misc.problem import ProblemTemplate
from guardctl.model.scenario import ScenarioStep, describe
import sys
from guardctl.model.system.primitives import TypeServ

class ExcludeDict:
    name: str
    objType: str
    obj: TypeServ

    def __init__(self, kn):
        self.objType = kn.split(":")[0]
        self.name = kn.split(":")[1]
        self.obj = TypeServ(self.name)

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
                scheduler1: "Scheduler"
            ):
        assert scheduler1.status == STATUS_SCHED["Clean"] 
        assert service1.amountOfActivePods == 0
        # assert service1.status == STATUS_SERV["Started"]
        assert service1.searchable == True
        assert pod1.targetService == service1

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
    @planned
    def MarkDeploymentOutageEvent(self,
                deployment_current: Deployment,
                pod_current: Pod,
                global_: "GlobalVar",
                scheduler: "Scheduler"
            ):
        assert scheduler.status == STATUS_SCHED["Clean"] 
        assert deployment_current.amountOfActivePods < deployment_current.spec_replicas
        assert deployment_current.searchable == True
        assert pod_current in  deployment_current.podList

        deployment_current.status = STATUS_DEPL["Interrupted"]
        global_.is_depl_interrupted = True
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Detected deployment outage event",
            parameters={"Pod": describe(pod_current)},
            probability=1.0,
            affected=[describe(deployment_current)]
        )

    @planned(cost=10000)
    def No_Deployment_Outage_Event_possible(self,
                deployment_current: Deployment,
                pod_current: Pod,
                global_: "GlobalVar",
                scheduler: "Scheduler"
            ):
        assert scheduler.status == STATUS_SCHED["Clean"] 
        
        global_.is_depl_interrupted = True
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="NO Detected deployment outage event detected",
            parameters={},
            probability=1.0,
            affected=[]
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

def mark_excluded(object_space, exclude, skip_check=False):
    names = []
    types = []
    for obj in object_space:
        if hasattr(obj, 'metadata_name'):
            names.append(obj.metadata_name)
        types.append(obj.__class__.__name__)
        for objExclude in exclude:
            if (obj.__class__.__name__ == objExclude.objType) and (obj.metadata_name == objExclude.name):
                obj.searchable = False
    if skip_check : return
    for objExclude in exclude:
        if not(objExclude.objType in types):
            raise AssertionError("Error: no such type '{0}'".format(objExclude.objType))
        if not(objExclude.name in names):
            raise AssertionError("Error: no such {1}: '{0}'".format(objExclude.name, objExclude.objType))

    return ScenarioStep(
        name=sys._getframe().f_code.co_name,
        subsystem=self.__class__.__name__,
        description="Mark service as started",
        parameters={},
        probability=1.0,
        affected=[describe(service1)]
    )
class AnyServiceInterrupted(K8ServiceInterruptSearch):

    goal = lambda self: self.globalVar.is_service_interrupted == True and \
            self.scheduler.status == STATUS_SCHED["Clean"]
class AnyDeploymentInterrupted(K8ServiceInterruptSearch):

    goal = lambda self: self.globalVar.is_depl_interrupted == True and \
            self.scheduler.status == STATUS_SCHED["Clean"]
