import sys
from poodle import planned
from logzero import logger
from kalc.model.system.base import HasLimitsRequests, HasLabel
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.model.system.primitives import TypeServ
from kalc.model.system.math import Permutations, permutation_list
from kalc.model.system.Controller import Controller
from kalc.model.system.primitives import Label
from kalc.model.kinds.Service import Service
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
from kalc.misc.const import *
from kalc.model.kubeactions import KubernetesModel
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from kalc.misc.const import STATUS_SCHED
from kalc.misc.script_generator import script_remove_node
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
        
    @planned(cost=1)
    def Mark_node_outage_event(self,
        node:"Node",
        globalvar:GlobalVar):
        assert node.status == STATUS_NODE["Inactive"]
        assert node.searchable == True
        globalvar.is_node_disrupted = True
        
        
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
    
  
    @planned(cost=1)
    def Scheduler_cant_place_pod(self, scheduler: "Scheduler",
        globalVar: GlobalVar):
        # assert globalVar.block_node_outage_in_progress == False
        scheduler.queueLength -= 1
        
class Check_deployments(OptimisticRun):
    @planned(cost=1)
    def AnyDeploymentInterrupted(self,globalVar:GlobalVar,
                scheduler: "Scheduler"):
        assert globalVar.is_deployment_disrupted == True
        # assert scheduler.status == STATUS_SCHED["Clean"]
        globalVar.goal_achieved = True 
        
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
        
    @planned(cost=1) # this works for no-outage case
    def SchedulerQueueCleanLowCost(self, scheduler: Scheduler, global_: GlobalVar):
        assert scheduler.status == STATUS_SCHED["Clean"]
        assert global_.block_node_outage_in_progress == False
        global_.goal_achieved = True

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
#             for pod1, pod2 in itertools.permutations(filter(lambda x: isinstance(x, Pod) and x in service.podList, self.objectList),2):
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
        
class Antiaffinity_check_basis(KubernetesModel):
    # @planned(cost=1)
    # def brakepoint(self,
    #     target_pod: Pod):
    #     assert target_pod.status == STATUS_POD["Pending"]
    #     # assert target_pod.antiaffinity_set == True
    #     target_pod.antiaffinity_met = True
    # @planned(cost=1)
    # def brakepoint2(self,
    #     target_pod: Pod,
    #     node: Node):
    #     assert target_pod.status == STATUS_POD["Running"]
    #     assert target_pod.atNode == node
    #     assert node.isSearched == True
    #     target_pod.antiaffinity_met = True
    # @planned(cost=1)
    # def finish_cluster_changes_calculate_meassures(self,
    #     scheduler: Scheduler,
    #     globalVar: GlobalVar):
    #     assert globalVar.block_policy_calculated == False
    #     assert scheduler.queueLength == 0
    #     globalVar.block_policy_calculated = True


    @planned(cost=1)
    def mark_checked_pod_as_antiaffinity_checked_for_target_pod(self,
        target_pod: Pod,
        antiaffinity_pod: Pod,
        globalVar: GlobalVar,
        scheduler: Scheduler,
        antiaffinity_pod_node: Node):
        if antiaffinity_pod.atNode != target_pod.atNode and \
                    target_pod.antiaffinity_set == True and \
                antiaffinity_pod not in target_pod.calc_antiaffinity_pods_list:
                target_pod.calc_antiaffinity_pods_list.add(antiaffinity_pod)
                target_pod.calc_antiaffinity_pods_list_length += 1
        assert antiaffinity_pod in target_pod.podsMatchedByAntiaffinity
        assert globalVar.deploymentsWithAntiaffinityBalanced == True 
        assert antiaffinity_pod.atNode == antiaffinity_pod_node
        assert antiaffinity_pod_node.isNull == False
        # assert globalVar.block_policy_calculated == True
        globalVar.block_policy_calculated = True


    # @planned(cost=1)
    # def calculate_length_of_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod(self,
    #     target_pod: Pod,
    #     antiaffinity_pod: Pod,
    #     antiaffinity_pod_node: Node,
    #     debug_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length: int):
    #     assert antiaffinity_pod in target_pod.podsMatchedByAntiaffinity
    #     assert antiaffinity_pod in target_pod.calc_affinity_pods_list
    #     assert antiaffinity_pod_node == antiaffinity_pod.atNode
    #     if antiaffinity_pod_node not in target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod:
    #         assert debug_nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length == target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length           
    #         target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod.add(antiaffinity_pod_node)
    #         target_pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length += 1
    # @planned(cost=1)
    # def mark_checked_pod_as_affinity_checked_for_target_pod(self,
    #     target_pod: Pod,
    #     checked_pod: Pod,
    #     globalVar: GlobalVar,
    #     scheduler: Scheduler):
    #     if checked_pod.atNode == target_pod.atNode and \
    #                 target_pod.affinity_set == True and \
    #             checked_pod not in target_pod.calc_affinity_pods_list:
    #             target_pod.calc_affinity_pods_list.add(checked_pod)
    #             target_pod.calc_affinity_pods_list_length += 1
    #     assert checked_pod in target_pod.podsMatchedByAffinity
    #     assert globalVar.deploymentsWithAntiaffinityBalanced == True 
    #     # assert globalVar.block_policy_calculated == True 
    #     globalVar.block_policy_calculated = True
    @planned(cost=1)
    def mark_2_pods_of_deployment_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            deployment: Deployment):
        assert node_of_pod2 == pod2.atNode
        assert pod1.atNode in node_of_pod2.different_than
        assert pod1 in deployment.podList
        assert pod2 in deployment.podList
        assert pod1.antiaffinity_set == True 
        assert pod2.antiaffinity_set == True
        assert pod2 in pod1.podsMatchedByAntiaffinity
        assert pod1 in pod2.podsMatchedByAntiaffinity
        if pod2 not in pod1.calc_antiaffinity_pods_list and \
            pod1 not in pod2.calc_antiaffinity_pods_list:
            pod1.calc_antiaffinity_pods_list.add(pod2)
            pod1.calc_antiaffinity_pods_list_length += 1
            pod2.calc_antiaffinity_pods_list.add(pod1)
            pod2.calc_antiaffinity_pods_list_length += 1

    # @planned(cost=1)
    # def mark_3_pods_of_deployment_as_not_at_same_node(self,
    #         pod1: Pod,
    #         pod2: Pod,
    #         pod3: Pod,
    #         node_of_pod1: Node,
    #         node_of_pod2: Node,
    #         node_of_pod3: Node,
    #         deployment: Deployment):
        
    #     assert node_of_pod1 == pod1.atNode
    #     assert node_of_pod2 == pod2.atNode
    #     assert node_of_pod3 == pod3.atNode
    #     assert node_of_pod1 in node_of_pod2.different_than
    #     assert node_of_pod1 in node_of_pod3.different_than
    #     assert node_of_pod2 in node_of_pod3.different_than
    #     assert pod1 in deployment.podList
    #     assert pod2 in deployment.podList
    #     assert pod3 in deployment.podList
    #     assert pod1.antiaffinity_set == True 
    #     assert pod2.antiaffinity_set == True
    #     assert pod3.antiaffinity_set == True
    #     assert pod2 in pod1.podsMatchedByAntiaffinity
    #     assert pod1 in pod2.podsMatchedByAntiaffinity
    #     assert pod2 in pod3.podsMatchedByAntiaffinity
    #     assert pod1 in pod3.podsMatchedByAntiaffinity
    #     assert pod3 in pod1.podsMatchedByAntiaffinity
    #     assert pod3 in pod2.podsMatchedByAntiaffinity

    #     if pod2 not in pod1.calc_antiaffinity_pods_list and \
    #         pod1 not in pod2.calc_antiaffinity_pods_list and \
    #         pod2 not in pod3.calc_antiaffinity_pods_list and \
    #         pod1 not in pod3.calc_antiaffinity_pods_list and \
    #         pod3 not in pod1.calc_antiaffinity_pods_list and \
    #         pod3 not in pod2.calc_antiaffinity_pods_list:

    #         pod1.calc_antiaffinity_pods_list.add(pod2)
    #         pod1.calc_antiaffinity_pods_list.add(pod3)
    #         pod1.calc_antiaffinity_pods_list_length += 2
    #         pod2.calc_antiaffinity_pods_list.add(pod1)
    #         pod2.calc_antiaffinity_pods_list.add(pod3)
    #         pod2.calc_antiaffinity_pods_list_length += 2
    #         pod3.calc_antiaffinity_pods_list.add(pod1)
    #         pod3.calc_antiaffinity_pods_list.add(pod2)
    #         pod3.calc_antiaffinity_pods_list_length += 2


# THis can't be used yet because of  BUG 131
    # @planned(cost=1)
    # def mark_4_pods_of_deployment_as_not_at_same_node(self,
    #         pod1: Pod,
    #         pod2: Pod,
    #         pod3: Pod,
    #         pod4: Pod,
    #         node_of_pod1: Node,
    #         node_of_pod2: Node,
    #         node_of_pod3: Node,
    #         node_of_pod4: Node,
    #         deployment: Deployment):
        
    #     assert node_of_pod1 == pod1.atNode
    #     assert node_of_pod2 == pod2.atNode
    #     assert node_of_pod3 == pod3.atNode
    #     assert node_of_pod4 == pod4.atNode
    #     assert node_of_pod1 in node_of_pod2.different_than
    #     assert node_of_pod1 in node_of_pod3.different_than
    #     assert node_of_pod1 in node_of_pod4.different_than
    #     assert node_of_pod2 in node_of_pod3.different_than
    #     assert node_of_pod2 in node_of_pod4.different_than
    #     assert node_of_pod3 in node_of_pod4.different_than
    #     assert pod1 in deployment.podList
    #     assert pod2 in deployment.podList
    #     assert pod3 in deployment.podList
    #     assert pod4 in deployment.podList
    #     assert pod1.antiaffinity_set == True 
    #     assert pod2.antiaffinity_set == True
    #     assert pod3.antiaffinity_set == True
    #     assert pod4.antiaffinity_set == True
    #     assert pod1 in pod2.podsMatchedByAntiaffinity
    #     assert pod1 in pod3.podsMatchedByAntiaffinity
    #     assert pod1 in pod4.podsMatchedByAntiaffinity
    #     assert pod2 in pod1.podsMatchedByAntiaffinity
    #     assert pod2 in pod3.podsMatchedByAntiaffinity
    #     assert pod2 in pod4.podsMatchedByAntiaffinity
    #     assert pod3 in pod1.podsMatchedByAntiaffinity
    #     assert pod3 in pod2.podsMatchedByAntiaffinity
    #     assert pod3 in pod4.podsMatchedByAntiaffinity
    #     assert pod4 in pod1.podsMatchedByAntiaffinity
    #     assert pod4 in pod2.podsMatchedByAntiaffinity
    #     assert pod4 in pod3.podsMatchedByAntiaffinity
        
    #     if pod1 not in pod2.calc_antiaffinity_pods_list and \
    #         pod1 not in pod3.calc_antiaffinity_pods_list and \
    #         pod1 not in pod4.calc_antiaffinity_pods_list and \
    #         pod2 not in pod1.calc_antiaffinity_pods_list and \
    #         pod2 not in pod3.calc_antiaffinity_pods_list and \
    #         pod2 not in pod4.calc_antiaffinity_pods_list and \
    #         pod3 not in pod1.calc_antiaffinity_pods_list and \
    #         pod3 not in pod2.calc_antiaffinity_pods_list and \
    #         pod3 not in pod4.calc_antiaffinity_pods_list and \
    #         pod4 not in pod1.calc_antiaffinity_pods_list and \
    #         pod4 not in pod2.calc_antiaffinity_pods_list and \
    #         pod4 not in pod3.calc_antiaffinity_pods_list:

    #         pod1.calc_antiaffinity_pods_list.add(pod2)
    #         pod1.calc_antiaffinity_pods_list.add(pod3)
    #         pod1.calc_antiaffinity_pods_list.add(pod4)
    #         pod1.calc_antiaffinity_pods_list_length += 3
    #         pod2.calc_antiaffinity_pods_list.add(pod1)
    #         pod2.calc_antiaffinity_pods_list.add(pod3)
    #         pod2.calc_antiaffinity_pods_list.add(pod4)
    #         pod2.calc_antiaffinity_pods_list_length += 3
    #         pod3.calc_antiaffinity_pods_list.add(pod1)
    #         pod3.calc_antiaffinity_pods_list.add(pod2)
    #         pod3.calc_antiaffinity_pods_list.add(pod4)
    #         pod3.calc_antiaffinity_pods_list_length += 3
    #         pod4.calc_antiaffinity_pods_list.add(pod1)
    #         pod4.calc_antiaffinity_pods_list.add(pod2)
    #         pod4.calc_antiaffinity_pods_list.add(pod3)
    #         pod4.calc_antiaffinity_pods_list_length += 3


# THis can't be used yet because of  BUG 131
    # @planned(cost=1)
    # def mark_5_pods_of_deployment_as_not_at_same_node(self,
    #         pod1: Pod,
    #         pod2: Pod,
    #         pod3: Pod,
    #         pod4: Pod,
    #         pod5: Pod,
    #         node_of_pod1: Node,
    #         node_of_pod2: Node,
    #         node_of_pod3: Node,
    #         node_of_pod4: Node,
    #         node_of_pod5: Node,
    #         deployment: Deployment):
        
    #     assert node_of_pod1 == pod1.atNode
    #     assert node_of_pod2 == pod2.atNode
    #     assert node_of_pod3 == pod3.atNode
    #     assert node_of_pod4 == pod4.atNode
    #     assert node_of_pod5 == pod5.atNode
    #     assert node_of_pod1 in node_of_pod2.different_than
    #     assert node_of_pod1 in node_of_pod3.different_than
    #     assert node_of_pod1 in node_of_pod4.different_than
    #     assert node_of_pod1 in node_of_pod5.different_than
    #     assert node_of_pod2 in node_of_pod3.different_than
    #     assert node_of_pod2 in node_of_pod4.different_than
    #     assert node_of_pod2 in node_of_pod5.different_than
    #     assert node_of_pod3 in node_of_pod4.different_than
    #     assert node_of_pod3 in node_of_pod5.different_than
    #     assert node_of_pod4 in node_of_pod5.different_than

    #     assert pod1 in deployment.podList
    #     assert pod2 in deployment.podList
    #     assert pod3 in deployment.podList
    #     assert pod4 in deployment.podList
    #     assert pod5 in deployment.podList
    #     assert pod1.antiaffinity_set == True 
    #     assert pod2.antiaffinity_set == True
    #     assert pod3.antiaffinity_set == True
    #     assert pod4.antiaffinity_set == True
        
    #     assert pod1 in pod2.podsMatchedByAntiaffinity
    #     assert pod1 in pod3.podsMatchedByAntiaffinity
    #     assert pod1 in pod4.podsMatchedByAntiaffinity
    #     assert pod1 in pod5.podsMatchedByAntiaffinity
    #     assert pod2 in pod1.podsMatchedByAntiaffinity
    #     assert pod2 in pod3.podsMatchedByAntiaffinity
    #     assert pod2 in pod4.podsMatchedByAntiaffinity
    #     assert pod2 in pod5.podsMatchedByAntiaffinity
    #     assert pod3 in pod1.podsMatchedByAntiaffinity
    #     assert pod3 in pod2.podsMatchedByAntiaffinity
    #     assert pod3 in pod4.podsMatchedByAntiaffinity
    #     assert pod3 in pod5.podsMatchedByAntiaffinity
    #     assert pod4 in pod1.podsMatchedByAntiaffinity
    #     assert pod4 in pod2.podsMatchedByAntiaffinity
    #     assert pod4 in pod3.podsMatchedByAntiaffinity
    #     assert pod4 in pod5.podsMatchedByAntiaffinity
    #     assert pod5 in pod1.podsMatchedByAntiaffinity
    #     assert pod5 in pod2.podsMatchedByAntiaffinity
    #     assert pod5 in pod3.podsMatchedByAntiaffinity
    #     assert pod5 in pod4.podsMatchedByAntiaffinity

    #     if pod1 not in pod2.calc_antiaffinity_pods_list  and \
    #         pod1 not in pod3.calc_antiaffinity_pods_list and \
    #         pod1 not in pod4.calc_antiaffinity_pods_list and \
    #         pod1 not in pod5.calc_antiaffinity_pods_list and \
    #         pod2 not in pod1.calc_antiaffinity_pods_list and \
    #         pod2 not in pod3.calc_antiaffinity_pods_list and \
    #         pod2 not in pod4.calc_antiaffinity_pods_list and \
    #         pod2 not in pod5.calc_antiaffinity_pods_list and \
    #         pod3 not in pod1.calc_antiaffinity_pods_list and \
    #         pod3 not in pod2.calc_antiaffinity_pods_list and \
    #         pod3 not in pod4.calc_antiaffinity_pods_list and \
    #         pod3 not in pod5.calc_antiaffinity_pods_list and \
    #         pod4 not in pod1.calc_antiaffinity_pods_list and \
    #         pod4 not in pod2.calc_antiaffinity_pods_list and \
    #         pod4 not in pod3.calc_antiaffinity_pods_list and \
    #         pod4 not in pod5.calc_antiaffinity_pods_list and \
    #         pod5 not in pod1.calc_antiaffinity_pods_list and \
    #         pod5 not in pod2.calc_antiaffinity_pods_list and \
    #         pod5 not in pod3.calc_antiaffinity_pods_list and \
    #         pod5 not in pod4.calc_antiaffinity_pods_list:

    #         pod1.calc_antiaffinity_pods_list.add(pod2)
    #         pod1.calc_antiaffinity_pods_list.add(pod3)
    #         pod1.calc_antiaffinity_pods_list.add(pod4)
    #         pod1.calc_antiaffinity_pods_list.add(pod5)
    #         pod1.calc_antiaffinity_pods_list_length += 4

    #         pod2.calc_antiaffinity_pods_list.add(pod1)
    #         pod2.calc_antiaffinity_pods_list.add(pod3)
    #         pod2.calc_antiaffinity_pods_list.add(pod4)
    #         pod2.calc_antiaffinity_pods_list.add(pod5)
    #         pod2.calc_antiaffinity_pods_list_length += 4
            
    #         pod3.calc_antiaffinity_pods_list.add(pod1)
    #         pod3.calc_antiaffinity_pods_list.add(pod2)
    #         pod3.calc_antiaffinity_pods_list.add(pod4)
    #         pod3.calc_antiaffinity_pods_list.add(pod5)
    #         pod3.calc_antiaffinity_pods_list_length += 4

    #         pod4.calc_antiaffinity_pods_list.add(pod1)
    #         pod4.calc_antiaffinity_pods_list.add(pod2)
    #         pod4.calc_antiaffinity_pods_list.add(pod3)
    #         pod4.calc_antiaffinity_pods_list.add(pod5)
    #         pod4.calc_antiaffinity_pods_list_length += 4

    #         pod5.calc_antiaffinity_pods_list.add(pod1)
    #         pod5.calc_antiaffinity_pods_list.add(pod2)
    #         pod5.calc_antiaffinity_pods_list.add(pod3)
    #         pod5.calc_antiaffinity_pods_list.add(pod4)
    #         pod5.calc_antiaffinity_pods_list_length += 4
    # @planned(cost=1)
    # def mark_that_node_cant_allocate_pod_by_cpu(self,
    #     pod: Pod,
    #     node: Node,
    #     globalVar: GlobalVar):
    #     if not node in pod.nodesThatCantAllocateThisPod:
    #         assert pod.cpuRequest > node.cpuCapacity - node.currentFormalCpuConsumption
    #         pod.nodesThatCantAllocateThisPod.add(node)
    #         pod.nodesThatCantAllocateThisPod_length += 1
    #     # assert globalVar.block_policy_calculated == True
    #     globalVar.block_policy_calculated = True
    #     assert node.isNull == False
    # @planned(cost=1)
    # def mark_that_node_cant_allocate_pod_by_mem(self,
    #     pod: Pod,
    #     node: Node,
    #     globalVar: GlobalVar):
    #     assert node.isNull == False
    #     if not node in pod.nodesThatCantAllocateThisPod:
    #         assert pod.memRequest > node.memCapacity - node.currentFormalMemConsumption
    #         pod.nodesThatCantAllocateThisPod.add(node)
    #         pod.nodesThatCantAllocateThisPod_length += 1
    #     # assert globalVar.block_policy_calculated == True
    #     globalVar.block_policy_calculated = True
    # @planned(cost=1)
    # def mark_that_node_cant_allocate_pod_because_of_antiaffinity(self,
    #     target_pod: Pod,
    #     antiaffinity_pod:Pod,
    #     antiaffinity_pod_node: Node,
    #     globalVar: GlobalVar):
    #     if not antiaffinity_pod_node in target_pod.nodesThatCantAllocateThisPod:
    #         assert antiaffinity_pod in target_pod.podsMatchedByAntiaffinity
    #         # assert antiaffinity_pod == antiaffinity_pod.atNode
    #         assert antiaffinity_pod in antiaffinity_pod_node.allocatedPodList
    #         assert antiaffinity_pod_node == antiaffinity_pod.atNode
    #         target_pod.nodesThatCantAllocateThisPod.add(antiaffinity_pod_node)
    #         target_pod.nodesThatCantAllocateThisPod_length += 1
    #     # assert globalVar.block_policy_calculated == True
    #     globalVar.block_policy_calculated = True
    # @planned(cost=1)
    # def mark_that_node_cant_allocate_pod_because_of_affinity(self,
    #     target_pod: Pod,
    #     affinity_pod:Pod,
    #     node: Node,
    #     globalVar: GlobalVar):
    #     assert affinity_pod in target_pod.podsMatchedByAffinity
    #     assert node == affinity_pod.atNode
    #     if node not in target_pod.nodesThatCantAllocateThisPod and \
    #         affinity_pod not in node.allocatedPodList:
    #             target_pod.nodesThatCantAllocateThisPod.add(node)
    #             target_pod.nodesThatCantAllocateThisPod_length += 1
    #     # assert globalVar.block_policy_calculated == True
    #     globalVar.block_policy_calculated = True
    # @planned(cost=1)
    # def remove_pod_from_cluster_because_of_anitaffinity_conflict(self,
    #     target_pod: Pod,
    #     scheduler: Scheduler,
    #     globalVar: GlobalVar):
    #     # assert globalVar.block_policy_calculated == True
    #     assert target_pod.nodesThatCantAllocateThisPod_length == globalVar.amountOfNodes
    #     scheduler.podQueue.remove(target_pod)
    #     scheduler.queueLength -= 1
    #     scheduler.podQueue_excluded_pods.add(target_pod)
    #     scheduler.podQueue_excluded_pods_length += 1
    #     target_pod.target_number_of_antiaffinity_pods = 0
    #     globalVar.block_policy_calculated = True
    #     target_pod.antiaffinity_met = True
    # @planned(cost=1)
    # def remove_pod_from_antiaffinitymatched_pod_list_of_target_pod(self,
    #     target_pod: Pod,
    #     antiaffinity_pod: Pod,
    #     globalVar: GlobalVar,
    #     scheduler: Scheduler):
    #     assert antiaffinity_pod in scheduler.podQueue_excluded_pods
    #     assert antiaffinity_pod in target_pod.podsMatchedByAntiaffinity
    #     target_pod.podsMatchedByAntiaffinity.remove(antiaffinity_pod)
    #     target_pod.podsMatchedByAntiaffinity_length -= 1   
    #     target_pod.target_number_of_antiaffinity_pods -= 1
    # @planned(cost=1)
    # def remove_pod_from_cluster_because_of_affinity_conflict(self,
    #     target_pod: Pod,
    #     checked_pod:Pod,
    #     scheduler: Scheduler,
    #     globalVar: GlobalVar):
    #     assert checked_pod in target_pod.podsMatchedByAffinity
    #     assert checked_pod.calc_cantmatch_affinity == True
    #     scheduler.podQueue.remove(checked_pod)
    #     scheduler.queueLength -= 1
    #     scheduler.podQueue_excluded_pods.add(checked_pod)
    #     scheduler.podQueue_excluded_pods_length += 1
    #     target_pod.target_number_of_antiaffinity_pods = 0
    #     globalVar.block_policy_calculated = True
    #     target_pod.affinity_met = True
    @planned(cost=1)
    def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.calc_antiaffinity_pods_list_length == pod.podsMatchedByAntiaffinity_length
        assert pod.antiaffinity_set == True
        assert globalVar.deploymentsWithAntiaffinityBalanced == True 
        # assert globalVar.block_policy_calculated == True
        pod.antiaffinity_met = True
        globalVar.block_policy_calculated = True
    @planned(cost=1)
    def mark_affinity_met_because_all_affinity_pods_are_matched(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.calc_affinity_pods_list_length == pod.podsMatchedByAffinity_length
        assert pod.affinity_set == True
        assert globalVar.deploymentsWithAntiaffinityBalanced == True 
        # assert globalVar.block_policy_calculated == True
        pod.affinity_met = True
        globalVar.block_policy_calculated = True
    # @planned(cost=1)
    # def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched_and_those_that_cant_dont_suite(self,
    #     pod: Pod,
    #     globalVar: GlobalVar):
    #     assert pod.calc_antiaffinity_pods_list_length == pod.target_number_of_antiaffinity_pods
    #     assert pod.antiaffinity_set == True
    #     assert globalVar.deploymentsWithAntiaffinityBalanced == True 
    #     # assert globalVar.block_policy_calculated == True
    #     pod.antiaffinity_met = True
    #     globalVar.block_policy_calculated = True
    @planned(cost=1)
    def mark_antiaffinity_met_because_antiaffinity_is_not_set(self,
        pod: Pod,
        globalVar: GlobalVar):
        assert pod.antiaffinity_set == False
        assert globalVar.deploymentsWithAntiaffinityBalanced == True 
        # assert globalVar.block_policy_calculated == True
        pod.antiaffinity_met = True
    # @planned(cost=1)
    # def mark_antiaffinity_met_because_all_antiaffinity_pods_are_matched_and_those_that_cant_dont_suite_below_the_limit_for_node_amount(self,
    #     pod: Pod,
    #     globalVar: GlobalVar):
    #     assert pod.nodesThatHaveAllocatedPodsThatHaveAntiaffinityWithThisPod_length + pod.nodesThatCantAllocateThisPod_length == globalVar.amountOfNodes_limit
    #     assert pod.antiaffinity_set == True
    #     pod.antiaffinity_met = True

class Antiaffinity_check(Antiaffinity_check_basis):       
    def generate_goal(self):
        self.generated_goal_in = []
        self.generated_goal_eq = []
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_met, True])
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.antiaffinity_preferred_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_preferred_met, True])
        for pod1 in filter(lambda p: isinstance(p, Pod) and p.affinity_set == True, self.objectList):
                self.generated_goal_eq.append([pod1.affinity_met, True])
        scheduler = next(filter(lambda x: isinstance(x, Scheduler),self.objectList))
        self.generated_goal_eq.append([scheduler.status, STATUS_SCHED["Clean"]])
    def goal(self):
        for what, where in self.generated_goal_in:
            assert what in where
        for what1, what2 in self.generated_goal_eq:
            assert what1 == what2
class Antiaffinity_check_with_add_node(Antiaffinity_check):
    @planned(cost=1)
    def Add_node(self,
            node : Node,
            globalVar: GlobalVar):
        assert node.status == STATUS_NODE["New"]
        node.status = STATUS_NODE["Active"]
        globalVar.amountOfNodes += 1

class Antiaffinity_check_with_limited_number_of_pods(Antiaffinity_check_basis):
    def generate_goal(self):
        self.generated_goal_in = []
        self.generated_goal_eq = []
        for globalVar in filter(lambda p: isinstance(p, GlobalVar), self.objectList):
                self.generated_goal_eq.append([globalVar.deploymentsWithAntiaffinityBalanced, True])
        for pod1 in filter(lambda p: isinstance(p, Pod), self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_met, True])
        scheduler = next(filter(lambda x: isinstance(x, Scheduler),self.objectList))
        self.generated_goal_eq.append([scheduler.status, STATUS_SCHED["Clean"]])

    def goal(self):
        for what, where in self.generated_goal_in:
            assert what in where
        for what1, what2 in self.generated_goal_eq:
            assert what1 == what2

    # @planned(cost=1)
    # def Set_antiaffinity_between_pods_of_deployment(self,
    #     pod1: Pod,
    #     pod2: Pod,
    #     deployment: Deployment,
    #     globalVar: GlobalVar):
    #     assert pod1.searchable == True
    #     assert pod2.searchable == True
    #     if pod1 not in pod2.podsMatchedByAntiaffinity and pod2 not in pod1.podsMatchedByAntiaffinity and pod1 != pod2:
    #         assert pod1 in deployment.podList
    #         assert pod2 in deployment.podList
    #         assert deployment.amountOfActivePods > 1
    #         assert deployment.NumberOfPodsOnSameNodeForDeployment == globalVar.maxNumberOfPodsOnSameNodeForDeployment
    #         pod1.antiaffinity_set = True
    #         pod1.podsMatchedByAntiaffinity.add(pod2)
    #         pod1.podsMatchedByAntiaffinity_length += 1
    #         pod2.antiaffinity_set = True
    #         pod2.podsMatchedByAntiaffinity.add(pod1)
    #         pod2.podsMatchedByAntiaffinity_length += 1
    #         deployment.podsMatchedByAntiaffinity_length += 2
    @planned(cost=1)
    def Set_antiaffinity_between_2_pods_of_deployment(self,
        pod1: Pod,
        pod2: Pod,
        deployment: Deployment,
        globalVar: GlobalVar):
        assert pod1.atNode == pod2.atNode
        assert pod1.searchable == True
        assert pod2.searchable == True
        assert pod1 in deployment.podList
        assert pod2 in deployment.podList
        if  pod1 not in pod2.podsMatchedByAntiaffinity and \
            pod2 not in pod1.podsMatchedByAntiaffinity and \
            pod1 != pod2:
            pod1.antiaffinity_set = True
            pod1.podsMatchedByAntiaffinity.add(pod2)
            pod1.podsMatchedByAntiaffinity_length += 1
            pod2.antiaffinity_set = True
            pod2.podsMatchedByAntiaffinity.add(pod1)
            pod2.podsMatchedByAntiaffinity_length += 1
            deployment.podsMatchedByAntiaffinity_length += 2
            # if globalVar.target_amountOfPodsWithAntiaffinity == 2 and deployment not in globalVar.DeploymentsWithAntiaffinity:
            #     globalVar.DeploymentsWithAntiaffinity.add(deployment)
            #     globalVar.DeploymentsWithAntiaffinity_length += 1


    # @planned(cost=1)
    # def Set_antiaffinity_between_3_pods_of_deployment(self,
    #     pod1: Pod,
    #     pod2: Pod,
    #     pod3: Pod,
    #     deployment: Deployment,
    #     globalVar: GlobalVar):
    #     assert pod1.searchable == True
    #     assert pod2.searchable == True
    #     assert pod3.searchable == True
    #     assert pod1 in deployment.podList
    #     assert pod2 in deployment.podList
    #     assert pod3 in deployment.podList
    #     assert pod1.atNode == pod2.atNode
    #     assert pod2.atNode == pod3.atNode
    #     if pod1 not in pod2.podsMatchedByAntiaffinity and \
    #         pod2 not in pod1.podsMatchedByAntiaffinity and \
    #         pod1 not in pod3.podsMatchedByAntiaffinity and \
    #         pod2 not in pod3.podsMatchedByAntiaffinity and \
    #         pod3 not in pod1.podsMatchedByAntiaffinity and \
    #         pod3 not in pod2.podsMatchedByAntiaffinity and \
    #         pod1 != pod2 and pod1 != pod3 and pod2 != pod3:
    #         pod1.antiaffinity_set = True
    #         pod1.podsMatchedByAntiaffinity.add(pod2)
    #         pod1.podsMatchedByAntiaffinity.add(pod3)
    #         pod1.podsMatchedByAntiaffinity_length += 2
    #         pod2.antiaffinity_set = True
    #         pod2.podsMatchedByAntiaffinity.add(pod1)
    #         pod2.podsMatchedByAntiaffinity.add(pod3)
    #         pod2.podsMatchedByAntiaffinity_length += 2
    #         pod3.antiaffinity_set = True
    #         pod3.podsMatchedByAntiaffinity.add(pod1)
    #         pod3.podsMatchedByAntiaffinity.add(pod2)
    #         pod3.podsMatchedByAntiaffinity_length += 2
    #         deployment.podsMatchedByAntiaffinity_length += 6
            ## if globalVar.target_amountOfPodsWithAntiaffinity == 3 and deployment not in globalVar.DeploymentsWithAntiaffinity:
            ##     globalVar.DeploymentsWithAntiaffinity.add(deployment)
            ##     globalVar.DeploymentsWithAntiaffinity_length += 1


    # @planned(cost=1)
    # def Set_antiaffinity_between_4_pods_of_deployment(self,
    #     pod1: Pod,
    #     pod2: Pod,
    #     pod3: Pod,
    #     pod4: Pod,
    #     deployment: Deployment,
    #     globalVar: GlobalVar):
    #     if  pod1 not in pod2.podsMatchedByAntiaffinity and \
    #         pod1 not in pod3.podsMatchedByAntiaffinity and \
    #         pod1 not in pod4.podsMatchedByAntiaffinity and \
    #         pod2 not in pod1.podsMatchedByAntiaffinity and \
    #         pod2 not in pod3.podsMatchedByAntiaffinity and \
    #         pod2 not in pod4.podsMatchedByAntiaffinity and \
    #         pod3 not in pod1.podsMatchedByAntiaffinity and \
    #         pod3 not in pod2.podsMatchedByAntiaffinity and \
    #         pod3 not in pod4.podsMatchedByAntiaffinity and \
    #         pod1 != pod2 and pod1 != pod3 and pod2 != pod3 and pod4 != pod1 and pod4 != pod2  and pod4 != pod3:
    #         assert pod1 in deployment.podList
    #         assert pod2 in deployment.podList
    #         assert pod3 in deployment.podList
    #         assert pod4 in deployment.podList
    #         pod1.antiaffinity_set = True
    #         pod1.podsMatchedByAntiaffinity.add(pod2)
    #         pod1.podsMatchedByAntiaffinity.add(pod3)
    #         pod1.podsMatchedByAntiaffinity.add(pod4)
    #         pod1.podsMatchedByAntiaffinity_length += 3
    #         pod2.antiaffinity_set = True
    #         pod2.podsMatchedByAntiaffinity.add(pod1)
    #         pod2.podsMatchedByAntiaffinity.add(pod3)
    #         pod2.podsMatchedByAntiaffinity.add(pod4)
    #         pod2.podsMatchedByAntiaffinity_length += 3
    #         pod3.antiaffinity_set = True
    #         pod3.podsMatchedByAntiaffinity.add(pod1)
    #         pod3.podsMatchedByAntiaffinity.add(pod2)
    #         pod3.podsMatchedByAntiaffinity.add(pod4)
    #         pod3.podsMatchedByAntiaffinity_length += 3
    #         pod4.antiaffinity_set = True
    #         pod4.podsMatchedByAntiaffinity.add(pod1)
    #         pod4.podsMatchedByAntiaffinity.add(pod2)
    #         pod4.podsMatchedByAntiaffinity.add(pod3)
    #         pod4.podsMatchedByAntiaffinity_length += 3
    #         globalVar.DeploymentsWithAntiaffinity.add(deployment)
    #         globalVar.DeploymentsWithAntiaffinity_length += 1
    #         deployment.podsMatchedByAntiaffinity_length += 12
    #         if globalVar.target_amountOfPodsWithAntiaffinity == 4 and deployment not in globalVar.DeploymentsWithAntiaffinity:
    #             globalVar.DeploymentsWithAntiaffinity.add(deployment)
    #             globalVar.DeploymentsWithAntiaffinity_length += 1
    @planned(cost=1)
    def Reduce_maxNumberOfPodsOnSameNodeForDeployment(self,
        globalVar: GlobalVar):
        globalVar.maxNumberOfPodsOnSameNodeForDeployment -= 1       
   
    @planned(cost=1)
    def Calculate_fulfilled_antiaffinity_pods_of_deployment(self,
        pod: Pod,
        deployment: Deployment,
        permutations_of_amountOfActivePods: Permutations,
        globalVar: GlobalVar):
        if deployment not in globalVar.DeploymentsWithAntiaffinity: 
            assert deployment.amountOfActivePods > 1
            assert permutations_of_amountOfActivePods.number == deployment.amountOfActivePods
            assert deployment.podsMatchedByAntiaffinity_length >= permutations_of_amountOfActivePods.permutations

            # if deployment.amountOfActivePods > 10:
            #     assert pod.podsMatchedByAntiaffinity_length == 45 
            # else:    
            #     assert permutations_of_amountOfActivePods.number == deployment.amountOfActivePods
            #     assert pod.podsMatchedByAntiaffinity_length == permutations_of_amountOfActivePods.permutations - 1
            globalVar.DeploymentsWithAntiaffinity.add(deployment)
            globalVar.DeploymentsWithAntiaffinity_length += 1

    @planned(cost=1)
    def Calculate_fulfilled_antiaffinity_pods_of_deployment_with_pod_limit(self,
        deployment: Deployment,
        permutations_of_target_amountOfPodsWithAntiaffinity: Permutations,
        globalVar: GlobalVar):
        if deployment not in globalVar.DeploymentsWithAntiaffinity: 
            assert deployment.amountOfActivePods > 1
            assert globalVar.target_amountOfPodsWithAntiaffinity > 0
            assert permutations_of_target_amountOfPodsWithAntiaffinity.number == globalVar.target_amountOfPodsWithAntiaffinity
            assert deployment.podsMatchedByAntiaffinity_length >= permutations_of_target_amountOfPodsWithAntiaffinity.permutations
            # if globalVar.target_amountOfPodsWithAntiaffinity > 10:
            #     assert pod.podsMatchedByAntiaffinity_length == 45 
            # else:    
            #     assert permutations_of_target_amountOfPodsWithAntiaffinity.number == globalVar.target_amountOfPodsWithAntiaffinity
            #     assert pod.podsMatchedByAntiaffinity_length == permutations_of_target_amountOfPodsWithAntiaffinity.permutations - 1
            globalVar.DeploymentsWithAntiaffinity.add(deployment)
            globalVar.DeploymentsWithAntiaffinity_length += 1

    @planned(cost=1)
    def mark_that_antiaffinity_is_set_for_requested_number_of_deployments(self, 
        globalVar: GlobalVar):
        assert globalVar.DeploymentsWithAntiaffinity_length == globalVar.target_DeploymentsWithAntiaffinity_length
        globalVar.deploymentsWithAntiaffinityBalanced = True
    
class Antiaffinity_check_with_limited_number_of_pods_with_add_node(Antiaffinity_check_with_limited_number_of_pods):
    @planned(cost=1)
    def Add_node(self,
            node : Node,
            globalVar: GlobalVar):
        assert node.status == STATUS_NODE["New"]
        node.status = STATUS_NODE["Active"]
        globalVar.amountOfNodes += 1

class Balance_pods_and_drain_node(Antiaffinity_check_with_limited_number_of_pods):
    # @planned(cost=1)
    # def calculate_daemonset_pods(self,
    #     daemonset: DaemonSet,
    #     node: Node,
    #     pod: Pod):
    #     if pod not in node.daemonset_podList:
    #         assert pod in daemonset.podList
    #         assert pod.atNode == node
    #         node.daemonset_podList.add(pod)
    #         node.daemonset_podList_length += 1


    @planned(cost=1)
    def DrainNode(self,
        node: "Node",
        globalVar: GlobalVar):
        assert node.amountOfActivePods == 0
        assert node.status == STATUS_NODE["Active"]
        assert node.isNull == False
        globalVar.NodesDrained_length += 1
        globalVar.NodesDrained.add(node)
        node.status = STATUS_NODE["Inactive"]

        self.script.append(script_remove_node(node))
    
    @planned(cost=1)
    def Reqested_amount_of_nodes_drained(self,
        globalVar: GlobalVar):
        assert globalVar.NodesDrained_length == globalVar.target_NodesDrained_length
        globalVar.target_NodesDrained_length_reached = True

    def generate_goal(self):
        self.generated_goal_in = []
        self.generated_goal_eq = []
        for globalVar in filter(lambda p: isinstance(p, GlobalVar), self.objectList):
                self.generated_goal_eq.append([globalVar.deploymentsWithAntiaffinityBalanced, True])
        for pod1 in filter(lambda p: isinstance(p, Pod), self.objectList):
                self.generated_goal_eq.append([pod1.antiaffinity_met, True])
        for globalVar in filter(lambda p: isinstance(p, GlobalVar), self.objectList):
            self.generated_goal_eq.append([globalVar.target_NodesDrained_length_reached, True])
        scheduler = next(filter(lambda x: isinstance(x, Scheduler),self.objectList))
        self.generated_goal_eq.append([scheduler.status, STATUS_SCHED["Clean"]])

    # def goal(self):
    #     for what, where in self.generated_goal_in:
    #         assert what in where
    #     for what1, what2 in self.generated_goal_eq:
    #         assert what1 == what2

# class Calculate_metrics(Balance_pods_and_drain_node):
#     @planned(cost=1)
#     def add_node(self,
#             node : Node,
#             globalVar: GlobalVar):
#         assert node.status == STATUS_NODE["New"]
#         node.status = STATUS_NODE["Active"]
#         globalVar.amountOfNodes += 1

#     @planned(cost=1)
#     def calc_reduce_metric_1_node_usage(self,
#         globalVar: GlobalVar,
#         node: Node):
#         assert (node.memCapacity - node.currentFormalMemConsumption) * 10 / node.memCapacity < globalVar. 
#         assert 

#         assert globalVar.