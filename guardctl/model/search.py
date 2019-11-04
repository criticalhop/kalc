import sys
from poodle import planned
from logzero import logger
from guardctl.model.system.base import HasLimitsRequests, HasLabel
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.system.globals import GlobalVar
from guardctl.model.system.primitives import TypeServ
from guardctl.model.system.Controller import Controller
from guardctl.model.system.primitives import Label
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.kinds.DaemonSet import DaemonSet
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from guardctl.model.scenario import ScenarioStep, describe
from guardctl.misc.const import *
from guardctl.model.kubeactions import KubernetesModel,Random_events
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
import re

class ExcludeDict:
    name: str
    objType: str
    obj: TypeServ

    def __init__(self, kn):
        self.objType = kn.split(":")[0]
        self.name = kn.split(":")[1]
        self.obj = TypeServ(self.name)

class K8ServiceInterruptSearch(KubernetesModel):


    @planned(cost=100)
    def NodeNServiceInterupted(self,globalVar:GlobalVar, scheduler: Scheduler):
        assert globalVar.is_node_disrupted == True
        assert globalVar.is_service_disrupted == True
        assert scheduler.status == STATUS_SCHED["Clean"]
        globalVar.goal_achieved = True 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Node and Service are interrupted",
            parameters={},
            probability=1.0,
            affected=[]
        )
    
    @planned(cost=100)
    def Mark_node_outage_event(self,
        node:"Node",
        globalvar:GlobalVar):
        assert node.status == STATUS_NODE["Inactive"]
        assert node.searchable == True
        globalvar.is_node_disrupted = True
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="node outage",
            parameters={},
            probability=0.01,
            affected=[describe(node)]
        )
    # @planned(cost=300000)
    # def No_Searched_Goal_possible(self,
    #             deployment_current: Deployment,
    #             pod_current: Pod,
    #             global_: "GlobalVar",
    #             scheduler: "Scheduler"
    #         ):
    #     assert scheduler.status == STATUS_SCHED["Clean"] 
    #     global_.goal_achieved = True
        
        # return ScenarioStep(
        #     name=sys._getframe().f_code.co_name,
        #     subsystem=self.__class__.__name__,
        #     description="NO searched goal possible",
        #     parameters={""},
        #     probability=1.0,
        #     affected=[]
        # )



def mark_excluded(object_space, excludeStr, skip_check=False):
    exclude = []
    if excludeStr != None:
        for kn in excludeStr.split(","):
            exclude.append(ExcludeDict(kn))
    else: 
        return
    names = []
    types = []
    for obj in object_space:
        if hasattr(obj, 'metadata_name'):
            names.append(str(obj.metadata_name))
            types.append(str(obj.__class__.__name__))
            for objExclude in exclude:
                re_name = "^" + objExclude.name.replace('*', '.*') + "$"
                re_objType =  "^" + objExclude.objType.replace('*', '.*') + "$"
                if (re.search(re.compile(re_objType), str(obj.__class__.__name__)) is not None) and \
                    (re.search(re.compile(re_name), str(obj.metadata_name)) is not None):
                    # print("mark unserchable ", str(obj.__class__.__name__), ":", str(obj.metadata_name ))
                    obj.searchable = False
    if skip_check : return
    for objExclude in exclude:
        re_name = "^" + objExclude.name.replace('*', '.*') + "$"
        re_objType =  "^" + objExclude.objType.replace('*', '.*') + "$"

        typeCheck = True
        for type_name in types:  
            if re.search(re.compile(re_objType), type_name) is not None:
                typeCheck = False
        if typeCheck:
            raise AssertionError("Error: no such type '{0}'".format(objExclude.objType))

        nameCheck = True
        for metadata_name in names:
            if re.search(re.compile(re_name), metadata_name) is not None:
                nameCheck = False
        if nameCheck:
            raise AssertionError("Error: no such {1}: '{0}'".format(objExclude.name, objExclude.objType))

class OptimisticRun(K8ServiceInterruptSearch):
    goal = lambda self: self.globalVar.goal_achieved == True 
    
    @planned(cost=900000) # this works for deployment-outage case
    def SchedulerQueueCleanHighCost(self, scheduler: Scheduler, global_: GlobalVar):
        assert scheduler.status == STATUS_SCHED["Clean"]
        assert global_.block_node_outage_in_progress == False
        global_.goal_achieved = True

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Processing finished",
            # parameters={"podsNotPlaced": int(scheduler.queueLength._get_value())},
            parameters={},
            probability=1.0,
            affected=[]
        )
class Check_deployments(OptimisticRun):
    @planned(cost=100)
    def AnyDeploymentInterrupted(self,globalVar:GlobalVar,
                scheduler: "Scheduler"):
        assert globalVar.is_deployment_disrupted == True
        # assert scheduler.status == STATUS_SCHED["Clean"]
        globalVar.goal_achieved = True 
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Some deployment is interrupted",
            parameters={},
            probability=1.0,
            affected=[]
        )
    @planned(cost=100)
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
        assert pod_current.status == STATUS_POD["Pending"]

        deployment_current.status = STATUS_DEPLOYMENT["Interrupted"]
        global_.is_deployment_disrupted = True
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Detected deployment outage event",
            parameters={"Pod": describe(pod_current)},
            probability=1.0,
            affected=[describe(deployment_current)]
        )
class Check_services(OptimisticRun):
    @planned(cost=100)
    def MarkServiceOutageEvent(self,
                service1: Service,
                pod1: Pod,
                global_: "GlobalVar",
                scheduler: "Scheduler"
            ):
            
        assert scheduler.status == STATUS_SCHED["Clean"] 
        assert service1.amountOfActivePods == 0
        # assert service1.status == STATUS_SERV["Started"] # TODO: Activate  this condition -  if service has to be started before eviction  
        assert service1.searchable == True  
        assert pod1.targetService == service1
        assert service1.isNull == False

        service1.status = STATUS_SERV["Interrupted"]
        global_.is_service_disrupted = True #TODO:  Optimistic search 
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Detected service outage event",
            parameters={"service.amountOfActivePods": 0, "service": describe(service1)},
            probability=1.0,
            affected=[describe(service1)]
        )

class Check_services_restart(OptimisticRun):
    @planned(cost=100)
    def MarkServiceOutageEvent(self,
                service1: Service,
                pod1: Pod,
                global_: "GlobalVar",
                scheduler: "Scheduler"
            ):
            
        # assert scheduler.status == STATUS_SCHED["Clean"] # Removed this assert  to make profile that check if service outage may happed temporary ( restart of service on the other node will help)
        assert service1.amountOfActivePods == 0
        # assert service1.status == STATUS_SERV["Started"] # TODO: Activate  this condition -  if service has to be started before eviction  
        assert service1.searchable == True  
        assert pod1.targetService == service1
        assert service1.isNull == False

        service1.status = STATUS_SERV["Interrupted"]
        global_.is_service_disrupted = True #TODO:  Optimistic search 
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Detected service outage event",
            parameters={"service.amountOfActivePods": 0, "service": describe(service1)},
            probability=1.0,
            affected=[describe(service1)]
        )

    @planned(cost=9000) # this works for no-outage case
    def SchedulerQueueCleanLowCost(self, scheduler: Scheduler, global_: GlobalVar):
        assert scheduler.status == STATUS_SCHED["Clean"]
        assert global_.block_node_outage_in_progress == False
        global_.goal_achieved = True

        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Processing finished",
            # parameters={"podsNotPlaced": int(scheduler.queueLength._get_value())},
            parameters={},
            probability=1.0,
            affected=[]
        )
    
    @planned(cost=100)
    def AnyServiceInterrupted(self,globalVar:GlobalVar, scheduler: Scheduler):
        assert globalVar.is_service_disrupted == True
        assert scheduler.status == STATUS_SCHED["Clean"]
        globalVar.goal_achieved = True 

class Check_daemonsets(OptimisticRun):        
    @planned(cost=100)
    def MarkDaemonsetOutageEvent(self,
                daemonset_current: DaemonSet,
                pod_current: Pod,
                global_: "GlobalVar",
                scheduler: "Scheduler"
            ):
        assert scheduler.status == STATUS_SCHED["Clean"] 
        assert daemonset_current.searchable == True
        assert pod_current in  daemonset_current.podList
        assert pod_current.status == STATUS_POD["Pending"]

        # daemonset_current.status = STATUS_DAEMONSET_INTERRUPTED
        global_.is_daemonset_disrupted = True
        
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Detected daemonset outage event",
            parameters={"Pod": describe(pod_current)},
            probability=1.0,
            affected=[describe(daemonset_current)]
        )

class CheckNodeOutage(Check_services):
    goal = lambda self: self.globalVar.goal_achieved == True and \
                                self.globalVar.is_node_disrupted == True

class Check_services_and_deployments(Check_services,Check_deployments):
    pass

class Check_services_deployments_daemonsets(Check_daemonsets,Check_services,Check_deployments):
    pass
class Check_node_outage_and_service_restart(Check_services_restart):
    goal = lambda self: self.globalVar.is_service_disrupted == True and \
                                self.globalVar.is_node_disrupted == True