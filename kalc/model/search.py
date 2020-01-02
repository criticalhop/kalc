import sys
from poodle import planned
from logzero import logger
from kalc.model.system.base import HasLimitsRequests, HasLabel
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.model.system.primitives import TypeServ
from kalc.model.system.Controller import Controller
from kalc.model.system.primitives import Label
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from kalc.model.scenario import ScenarioStep, describe
from kalc.misc.const import *
from kalc.model.kubeactions import KubernetesModel
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from kalc.misc.const import STATUS_SCHED
import re
import itertools

class ExcludeDict:
    name: str
    objType: str
    obj: TypeServ

    def __init__(self, kn):
        self.objType = kn.split(":")[0]
        self.name = kn.split(":")[1]
        self.obj = TypeServ(self.name)

class K8ServiceInterruptSearch(KubernetesModel):

    @planned(cost=1)
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
    @planned(cost=1)
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
    
    # @planned(cost=9000) # this works for deployment-outage case
    # def SchedulerQueueCleanHighCost(self, scheduler: Scheduler, global_: GlobalVar):
    #     assert scheduler.status == STATUS_SCHED["Clean"]
    #     assert global_.block_node_outage_in_progress == False
    #     global_.goal_achieved = True
    
    #     return ScenarioStep(
    #         name=sys._getframe().f_code.co_name,
    #         subsystem=self.__class__.__name__,
    #         description="Processing finished",
    #         # parameters={"podsNotPlaced": int(scheduler.queueLength._get_value())},
    #         parameters={},
    #         probability=1.0,
    #         affected=[]
    #     )
    @planned(cost=1)
    def Scheduler_cant_place_pod(self, scheduler: "Scheduler",
        globalVar: GlobalVar):
        # assert globalVar.block_node_outage_in_progress == False
        scheduler.queueLength -= 1
        return ScenarioStep(
            name=sys._getframe().f_code.co_name,
            subsystem=self.__class__.__name__,
            description="Can't place a pod",
            parameters={},
            probability=1.0,
            affected=[]
        )
class Check_deployments(OptimisticRun):
    @planned(cost=1)
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
    @planned(cost=1)
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
    @planned(cost=1)
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
        assert pod1 in service1.podList
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
    @planned(cost=1)
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
        assert pod1 in service1.podList
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
    @planned(cost=1) # this works for no-outage case
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
    @planned(cost=1)
    def AnyServiceInterrupted(self,globalVar:GlobalVar, scheduler: Scheduler):
        assert globalVar.is_service_disrupted == True
        assert scheduler.status == STATUS_SCHED["Clean"]
        globalVar.goal_achieved = True 
class Check_daemonsets(OptimisticRun):        
    @planned(cost=1)
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


class HypothesisysClean(K8ServiceInterruptSearch):
    def Remove_pod_common_part(self,
        pod: Pod,
        scheduler: Scheduler):
        pod.status = STATUS_POD["Outaged"]
        scheduler.podQueue.remove(pod)
        scheduler.queueLength -= 1
        scheduler.queueLength -= 0 #TODO: remove this once replaced with costs
        scheduler.queueLength -= 0 #TODO: remove this once replaced with costs

    @planned(cost=100)
    def Remove_pod_from_the_cluster(self,
                service : Service,
                pod : Pod,
                scheduler : Scheduler,
                globalVar : GlobalVar
            ):
        # This action helps to remove pods from queue 
        assert globalVar.block_node_outage_in_progress == False
        assert pod.status == STATUS_POD["Pending"]
        assert pod in scheduler.podQueue
        if pod.hasService == True:
            assert pod in service.podList
            if service.amountOfActivePods + service.amountOfPodsInQueue == 1:
                    service.status = STATUS_SERV["Interrupted"]
                    globalVar.is_service_disrupted = True
                    self.Remove_pod_common_part()
            else:
                assert service.amountOfActivePods + service.amountOfPodsInQueue > 1
                self.Remove_pod_common_part()
        else:
            assert pod.hasService == False
            self.Remove_pod_common_part()
    
class HypothesisysNodeAndService(HypothesisysClean):
    goal = lambda self: self.scheduler.status == STATUS_SCHED["Clean"] and \
                        self.globalVar.is_node_disrupted == True and \
                        self.globalVar.is_service_disrupted == True


class HypothesisysNode(HypothesisysClean):
    goal = lambda self: self.scheduler.status == STATUS_SCHED["Clean"] and \
                           self.globalVar.is_node_disrupted == True 

# class Antiaffinity_implement(KubernetesModel):

#     def generate_goal(self):
#         self.generated_goal_in = []
#         self.generaged_goal_eq = []
#         for service in filter(lambda s: isinstance(s, Service) and s.antiaffinity == True , self.objectList):
#             for pod1, pod2 in itertools.combinations(filter(lambda x: isinstance(x, Pod) and x in service.podList, self.objectList),2):
#                 self.generated_goal_in.append([pod1, pod2.not_on_same_node])

#     def goal(self):
#         for what, where in self.generated_goal_in:
#             assert what in where
#         for what1, what2 in self.generaged_goal_eq:
#             assert what1 == what2
       

#     @planned(cost=1)
#     def manually_initiate_killing_of_pod(self,
#         node_with_outage: "Node",
#         pod_killed: "podkind.Pod",
#         globalVar: GlobalVar
#         ):
#         assert pod_killed.status == STATUS_POD["Running"]
#         pod_killed.status = STATUS_POD["Killing"]
#         return ScenarioStep(
#             name=sys._getframe().f_code.co_name,
#             subsystem=self.__class__.__name__,
#             description="Killing of pod initiated because of node outage",
#             parameters={},
#             probability=1.0,
#             affected=[]
#         )
#     @planned(cost=1)
#     def Not_at_same_node(self,
#             pod1: Pod,
#             pod2: Pod,
#             node_of_pod2: Node,
#             scheduler: Scheduler):
#         assert node_of_pod2 == pod2.atNode
#         assert pod1.atNode in node_of_pod2.different_than
#         assert scheduler.status == STATUS_SCHED["Clean"]
#         pod1.not_on_same_node.add(pod2)


# class Antiaffinity_implement_with_add_node(Antiaffinity_implement):

#     @planned(cost=1)
#     def Add_node(self,
#                 node : Node):
#         assert node.status == STATUS_NODE["New"]
#         node.status = STATUS_NODE["Active"]

# class Antiaffinity_prefered(KubernetesModel):

#     goal = lambda self: self.globalVar.antiaffinity_prefered_policy_met == True

#     @planned(cost=1)
#     def mark_antiaffinity_prefered_policy_set(self,
#         service: Service,
#         globalVar: GlobalVar):
#         assert service.amountOfPodsInAntiaffinityGroup == service.targetAmountOfPodsOnDifferentNodes
#         assert service.isSearched == True
#         assert service.antiaffinity == True
#         service.antiaffinity_prefered_policy_set = True

#     @planned(cost=1)
#     def mark_antiaffinity_prefered_policy_met(self,
#         service: Service,
#         globalVar: GlobalVar):
#         assert service.amountOfPodsOnDifferentNodes == service.targetAmountOfPodsOnDifferentNodes
#         assert service.isSearched == True
#         assert service.antiaffinity == True
#         service.antiaffinity_prefered_policy_met = True

#     @planned(cost=1)
#     def manually_initiate_killing_of_pod_3(self,
#         node_with_outage: "Node",
#         pod_killed: "podkind.Pod",
#         globalVar: GlobalVar
#         ):
#         assert pod_killed.status == STATUS_POD["Running"]
#         pod_killed.status = STATUS_POD["Killing"]
#         return ScenarioStep(
#             name=sys._getframe().f_code.co_name,
#             subsystem=self.__class__.__name__,
#             description="Killing of pod initiated because of node outage",
#             parameters={},
#             probability=1.0,
#             affected=[]
#         )

#     @planned(cost=1)
#     def mark_2_pods_of_service_as_not_at_same_node(self,
#             pod1: Pod,
#             pod2: Pod,
#             node_of_pod1: Node,
#             node_of_pod2: Node,
#             service: Service,
#             scheduler: Scheduler):
#         assert node_of_pod2 == pod2.atNode
#         assert pod1.atNode in node_of_pod2.different_than
#         assert pod1 in service.podList
#         assert pod2 in service.podList
#         assert scheduler.status == STATUS_SCHED["Clean"]
#         pod1.not_on_same_node.add(pod2)
#         service.amountOfPodsOnDifferentNodes = 2

#     @planned(cost=1)
#     def mark_3_pods_of_service_as_not_at_same_node(self,
#             pod1: Pod,
#             pod2: Pod,
#             pod3: Pod,
#             node_of_pod1: Node,
#             node_of_pod2: Node,
#             node_of_pod3: Node,
#             service: Service,
#             scheduler: Scheduler):
        
#         assert node_of_pod1 == pod1.atNode
#         assert node_of_pod2 == pod2.atNode
#         assert node_of_pod3 == pod3.atNode
#         assert node_of_pod1 in node_of_pod2.different_than
#         assert node_of_pod1 in node_of_pod3.different_than
#         assert node_of_pod2 in node_of_pod3.different_than
#         assert pod1 in service.podList
#         assert pod2 in service.podList
#         assert pod3 in service.podList
#         assert scheduler.status == STATUS_SCHED["Clean"]
#         service.amountOfPodsOnDifferentNodes = 3

#     @planned(cost=1)
#     def mark_4_pods_of_service_as_not_at_same_node(self,
#             pod1: Pod,
#             pod2: Pod,
#             pod3: Pod,
#             pod4: Pod,
#             node_of_pod1: Node,
#             node_of_pod2: Node,
#             node_of_pod3: Node,
#             node_of_pod4: Node,
#             service: Service,
#             scheduler: Scheduler):
        
#         assert node_of_pod1 == pod1.atNode
#         assert node_of_pod2 == pod2.atNode
#         assert node_of_pod3 == pod3.atNode
#         assert node_of_pod4 == pod4.atNode
#         assert node_of_pod1 in node_of_pod2.different_than
#         assert node_of_pod1 in node_of_pod3.different_than
#         assert node_of_pod1 in node_of_pod4.different_than
#         assert node_of_pod2 in node_of_pod3.different_than
#         assert node_of_pod2 in node_of_pod4.different_than
#         assert node_of_pod3 in node_of_pod4.different_than
#         assert pod1 in service.podList
#         assert pod2 in service.podList
#         assert pod3 in service.podList
#         assert pod4 in service.podList
#         assert scheduler.status == STATUS_SCHED["Clean"]
#         service.amountOfPodsOnDifferentNodes = 4


#     @planned(cost=1)
#     def mark_5_pods_of_service_as_not_at_same_node(self,
#             pod1: Pod,
#             pod2: Pod,
#             pod3: Pod,
#             pod4: Pod,
#             pod5: Pod,
#             node_of_pod1: Node,
#             node_of_pod2: Node,
#             node_of_pod3: Node,
#             node_of_pod4: Node,
#             node_of_pod5: Node,
#             service: Service,
#             scheduler: Scheduler):
        
#         assert node_of_pod1 == pod1.atNode
#         assert node_of_pod2 == pod2.atNode
#         assert node_of_pod3 == pod3.atNode
#         assert node_of_pod4 == pod4.atNode
#         assert node_of_pod5 == pod5.atNode
#         assert node_of_pod1 in node_of_pod2.different_than
#         assert node_of_pod1 in node_of_pod3.different_than
#         assert node_of_pod1 in node_of_pod4.different_than
#         assert node_of_pod1 in node_of_pod5.different_than
#         assert node_of_pod2 in node_of_pod3.different_than
#         assert node_of_pod2 in node_of_pod4.different_than
#         assert node_of_pod2 in node_of_pod5.different_than
#         assert node_of_pod3 in node_of_pod4.different_than
#         assert node_of_pod3 in node_of_pod5.different_than
#         assert node_of_pod4 in node_of_pod5.different_than

#         assert pod1 in service.podList
#         assert pod2 in service.podList
#         assert pod3 in service.podList
#         assert pod4 in service.podList
#         assert pod5 in service.podList
#         assert scheduler.status == STATUS_SCHED["Clean"]
#         service.amountOfPodsOnDifferentNodes = 5

# class Antiaffinity_prefered_with_add_node(Antiaffinity_prefered):
#     @planned(cost=1)
#     def Add_node(self,
#             node : Node):
#         assert node.status == STATUS_NODE["New"]
#         node.status = STATUS_NODE["Active"]

class Antiaffinity_set(KubernetesModel):

    goal = lambda self: self.service.antiaffinity_prefered_policy_set == True

    @planned(cost=1)
    def mark_antiaffinity_set(self,
        pod1: Pod,
        pod2: Pod):
        assert pod2.isSearched == True
        assert pod1 in pod2.podsMatchedByAntiaffinity
        pod1.antiaffinity_set = True

class Antiaffinity_met(KubernetesModel):
    @planned(cost=1)
    def mark_antiaffinity_met(self,
        pod: Pod):
        assert pod.calc_antiaffinity_pods_list_length == pod.target_number_of_antiaffinity_pods
        pod.antiaffinity_met = True
    @planned(cost=1)
    def mark_antiaffinity_preferred_met(self,
        pod: Pod):
        assert pod.calc_antiaffinity_preferred_pods_list_length == pod.target_number_of_antiaffinity_preferred_pods
        pod.antiaffinity_preferred_met = True
    
    def generate_goal(self):
        self.generated_goal_in = []
        self.generated_goal_eq = []
        for target_pod in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_set == True, self.objectList):
                self.generated_goal_eq.append([target_pod.calc_antiaffinity_pods_list_length, target_pod.target_number_of_antiaffinity_pods])
        for target_pod in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_preferred_set == True, self.objectList):
                self.generated_goal_eq.append([target_pod.calc_antiaffinity_pods_list_length, target_pod.target_number_of_antiaffinity_preferred_pods])

    def goal(self):
        for what, where in self.generated_goal_in:
            assert what in where
        for what1, what2 in self.generated_goal_eq:
            assert what1 == what2

    @planned(cost=1)
    def manually_initiate_killing_of_pod(self,
        node_with_outage: "Node",
        pod_killed: "podkind.Pod",
        globalVar: GlobalVar
        ):
        assert pod_killed.status == STATUS_POD["Running"]
        pod_killed.status = STATUS_POD["Killing"]

    @planned(cost=1)
    def Not_at_same_node_preferred(self,
            pod1: Pod,
            pod2: Pod,
            node_of_pod2: Node,
            scheduler: Scheduler):
        assert pod2 in pod1.podsMatchedByAntiaffinityPrefered
        assert pod2 not in pod1.calc_antiaffinity_preferred_pods_list
        assert node_of_pod2 == pod2.atNode
        assert pod1.atNode in node_of_pod2.different_than
        assert scheduler.status == STATUS_SCHED["Clean"]
        pod1.not_on_same_node.add(pod2)
        pod1.calc_antiaffinity_preferred_pods_list.add(pod2)
        pod1.calc_antiaffinity_preferred_pods_list_length += 1
        
class Antiaffinity_check(KubernetesModel):
    # @planned(cost=1)
    def brakepoint(self,
        target_pod: Pod):
        assert target_pod.status == STATUS_POD["Pending"]
        # assert target_pod.antiaffinity_set == True
        target_pod.antiaffinity_met = True
    # @planned(cost=1)
    def brakepoint2(self,
        target_pod: Pod,
        node: Node):
        assert target_pod.status == STATUS_POD["Running"]
        assert target_pod.atNode == node
        assert node.isSearched == True
        target_pod.antiaffinity_met = True
    @planned(cost=1)
    def finish_cluster_changes_calculate_meassures(self,
        globalVar: GlobalVar):
        assert globalVar.block_policy_calculated == False
        globalVar.block_policy_calculated = True
    @planned(cost=1)
    def mark_checked_pod_as_antiaffinity_checked_for_target_pod(self,
        target_pod: Pod,
        checked_pod: Pod,
        globalVar: GlobalVar,
        scheduler: Scheduler):
        if checked_pod.atNode != target_pod.atNode and \
                    target_pod.antiaffinity_set == True and \
                checked_pod not in target_pod.calc_antiaffinity_pods_list:
                target_pod.calc_antiaffinity_pods_list.add(checked_pod)
                target_pod.calc_antiaffinity_pods_list_length += 1
        assert checked_pod in target_pod.podsMatchedByAntiaffinity 
        assert globalVar.block_policy_calculated == True 
        target_pod.antiaffinity_set = True
    @planned(cost=1)
    def mark_that_node_cant_allocate_pod_by_cpu(self,
        checked_pod: Pod,
        node: Node,
        globalVar: GlobalVar):
        if not node in checked_pod.nodesThatCantAllocateThisPod:
            assert checked_pod.cpuRequest > node.cpuCapacity - node.currentFormalCpuConsumption
            assert globalVar.block_policy_calculated == True
            checked_pod.nodesThatCantAllocateThisPod.add(node)
            checked_pod.nodesThatCantAllocateThisPod_length += 1
    @planned(cost=1)
    def mark_that_node_cant_allocate_pod_by_mem(self,
        checked_pod: Pod,
        node: Node,
        globalVar: GlobalVar):
        if not node in checked_pod.nodesThatCantAllocateThisPod:
            assert checked_pod.memRequest > node.memCapacity - node.currentFormalMemConsumption
            assert globalVar.block_policy_calculated == True
            checked_pod.nodesThatCantAllocateThisPod.add(node)
            checked_pod.nodesThatCantAllocateThisPod_length += 1
    @planned(cost=1)
    def mark_that_node_cant_allocate_pod_because_of_antiaffinity(self,
        target_pod: Pod,
        checked_pod:Pod,
        node: Node,
        globalVar: GlobalVar):
        if not node in target_pod.nodesThatCantAllocateThisPod:
            assert checked_pod in target_pod.podsMatchedByAntiaffinity
            assert globalVar.block_policy_calculated == True
            assert node == target_pod.atNode
            checked_pod.nodesThatCantAllocateThisPod.add(node)
            checked_pod.nodesThatCantAllocateThisPod_length += 1
    @planned(cost=1)
    def mark_that_all_nodes_dont_suite_for_checked_pod(self,
        checked_pod: Pod,
        globalVar: GlobalVar):
        assert checked_pod.nodesThatCantAllocateThisPod_length == globalVar.amountOfNodes 
        assert globalVar.block_policy_calculated == True
        checked_pod.calc_cantmatch_antiaffinity = True
    @planned(cost=1)
    def remove_pod_from_cluster_because_of_anitaffinity_conflict(self,
        target_pod: Pod,
        checked_pod:Pod,
        scheduler: Scheduler,
        globalVar: GlobalVar):
        assert checked_pod in target_pod.podsMatchedByAntiaffinity
        assert checked_pod.calc_cantmatch_antiaffinity == True
        scheduler.podQueue.remove(target_pod)
        scheduler.queueLength -= 1
        scheduler.podQueue_excluded_pods.add(target_pod)
        scheduler.podQueue_excluded_pods_length += 1
        target_pod.target_number_of_antiaffinity_pods = 0
    @planned(cost=1)
    def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.calc_antiaffinity_pods_list_length == pod.podsMatchedByAntiaffinity_length
        # assert globalVar.block_policy_calculated == True
        pod.antiaffinity_met = True
    @planned(cost=1)
    def mark_antiaffinity_met_bacause_all_antiaffinity_pods_are_matched_and_those_that_cant_dont_suite(self,
        pod: Pod,
        globalVar: GlobalVar):
        if pod.calc_antiaffinity_pods_list_length == pod.target_number_of_antiaffinity_pods:
            assert globalVar.block_policy_calculated == True
            pod.antiaffinity_met = True
    def generate_goal(self):
        self.generated_goal_in = []
        self.generated_goal_eq = []
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_met, True])
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_preferred_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_preferred_met, True])

    def goal(self):
        for what, where in self.generated_goal_in:
            assert what in where
        for what1, what2 in self.generated_goal_eq:
            assert what1 == what2
class Antiaffinity_check_with_add_node(Antiaffinity_check):
    @planned(cost=1)
    def Add_node(self,
            node : Node):
        assert node.status == STATUS_NODE["New"]
        node.status = STATUS_NODE["Active"]