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
from kalc.misc.const import *
from kalc.misc.problem import ProblemTemplate
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from kalc.misc.script_generator import move_pod_with_deployment_script_simple

class KubernetesModel(ProblemTemplate):
    def register_goal(self, lambda_fun):
        self.lambda_goal.append(lambda_fun)

    def add_goal_in(self, goal_entry):
        self.goals_in.extend(goal_entry)

    def add_goal_eq(self, goal_entry):
        self.goals_eq.extend(goal_entry)

    def generate_goal(self):
        self.add_goal_eq([[self.scheduler.status, STATUS_SCHED["Clean"]]])

    def goal(self):
        for l in self.lambda_goal:
            assert l()
        if self.goals_in:
            for what, where in self.goals_in:
                assert what in where
        if self.goals_eq:
            for what1, what2 in self.goals_eq:
                assert what1 == what2
       

    def problem(self):
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        self.globalVar = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

    @planned(cost=1)
    def Mark_service_as_started(self,
                service1: Service,
                scheduler: "Scheduler",
                globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert service1.amountOfActivePods > 0
        assert service1.isNull == False
        # assert globalVar.block_node_outage_in_progress == False
        service1.status = STATUS_SERV["Started"]

    @planned(cost=1)
    def Fill_priority_class_object(self,
            pod: "Pod",
            pclass: PriorityClass,
            globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert pod.spec_priorityClassName == pclass.metadata_name
        pod.priorityClass = pclass

        
    @planned(cost=1)
    def SetDefaultMemRequestForPod(self,
        pod1: "Pod",
        memLimit: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.memRequest == -1
            assert pod1.memLimit > -1
            assert memLimit == pod1.memLimit

            pod1.memRequest = memLimit

            
    @planned(cost=1)
    def SetDefaultCpuRequestForPod(self,
        pod1: "Pod",
        cpuLimit: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.cpuLimit > -1
            assert pod1.cpuRequest == -1
            assert cpuLimit == pod1.cpuLimit

            pod1.cpuRequest = cpuLimit

           
    @planned(cost=1)
    def SetDefaultMemLimitForPod(self,
        pod1: "Pod",
        node: "Node" ,
        memCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.memLimit == -1
            assert node == pod1.atNode
            assert memCapacity == node.memCapacity
            pod1.memLimit = memCapacity

            
    @planned(cost=1)
    def SetDefaultCpuLimitForPod(self,
        pod1: "Pod",
        node: "Node" ,
        cpuCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.cpuLimit == -1
            assert node == pod1.atNode
            assert cpuCapacity == node.cpuCapacity

            pod1.cpuLimit = cpuCapacity

            
    @planned(cost=1)
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node: "Node" ,
        memCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.memLimit == -1
            assert memCapacity == node.memCapacity
            pod1.toNode = node
            pod1.memLimit = memCapacity

            
    @planned(cost=1)
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: "Pod",
        node: "Node" ,
        cpuCapacity: int,
        globalVar: GlobalVar
         ):
            assert globalVar.block_policy_calculated == False
            # assert globalVar.block_node_outage_in_progress == False
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node.cpuCapacity
            pod1.toNode = node
            pod1.cpuLimit = cpuCapacity

    @planned(cost=1)
    def Evict_and_replace_less_prioritized_pod_byMEM(self,
                podPending: "Pod",
                podToBeReplaced: "Pod",
                nodeForPodPending: "Node" ,
                scheduler: "Scheduler",
                priorityClassOfPendingPod: PriorityClass,
                priorityClassOfPodToBeReplaced: PriorityClass,
                globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podPending in scheduler.podQueue
        assert podPending.toNode == nodeForPodPending
        assert nodeForPodPending.isNull == False
        assert podToBeReplaced.atNode == nodeForPodPending
        assert podPending.status == STATUS_POD["Pending"]
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass
        # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podPending.memRequest > nodeForPodPending.memCapacity - nodeForPodPending.currentFormalMemConsumption
        assert podToBeReplaced.status == STATUS_POD["Running"]
        podToBeReplaced.status = STATUS_POD["Killing"]

    @planned(cost=1)
    def Evict_and_replace_less_prioritized_pod_byCPU(self,
        podPending: "Pod",
        podToBeReplaced: "Pod",
        nodeForPodPending: "Node" ,
        scheduler: "Scheduler",
        priorityClassOfPendingPod: PriorityClass,
        priorityClassOfPodToBeReplaced: PriorityClass,
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        
        # assert globalVar.block_node_outage_in_progress == False
        assert podPending in scheduler.podQueue
        assert podPending.toNode == nodeForPodPending
        assert nodeForPodPending.isNull == False
        assert podToBeReplaced.atNode == nodeForPodPending
        assert podPending.status == STATUS_POD["Pending"]
        assert priorityClassOfPendingPod == podPending.priorityClass
        assert priorityClassOfPodToBeReplaced ==  podToBeReplaced.priorityClass
        # assert preemptionPolicyOfPendingPod == priorityClassOfPendingPod.preemptionPolicy
        # assert preemptionPolicyOfPodToBeReplaced == priorityClassOfPodToBeReplaced.preemptionPolicy
        # assert priorityClassOfPendingPod.preemptionPolicy == self.constSymbol["PreemptLowerPriority"]
        assert priorityClassOfPendingPod.priority > priorityClassOfPodToBeReplaced.priority
        assert podPending.cpuRequest > nodeForPodPending.cpuCapacity - nodeForPodPending.currentFormalCpuConsumption
        assert podToBeReplaced.status == STATUS_POD["Running"]
        podToBeReplaced.status = STATUS_POD["Killing"]

    @planned(cost=1)
    def Mark_Pod_As_Exceeding_Mem_Limits(self, podTobeKilled: "Pod",nodeOfPod: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podTobeKilled.memLimitsStatus == STATUS_LIM["Limit Met"]
        assert nodeOfPod == podTobeKilled.atNode
        assert podTobeKilled.memLimit <  podTobeKilled.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits += 1
        podTobeKilled.memLimitsStatus = STATUS_LIM["Limit Exceeded"]

        
    @planned(cost=1)
    def Mark_Pod_As_Not_Exceeding_Mem_Limits(self, podTobeReanimated: "Pod",
        nodeOfPod: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimitsStatus == STATUS_LIM["Limit Exceeded"]
        assert nodeOfPod == podTobeReanimated.atNode
        assert podTobeReanimated.memLimit >  podTobeReanimated.currentRealMemConsumption
        nodeOfPod.AmountOfPodsOverwhelmingMemLimits -= 1
        podTobeReanimated.memLimitsStatus = STATUS_LIM["Limit Met"]

    @planned(cost=1)
    def MemoryErrorKillPodExceedingLimits(self,
        nodeOfPod: "Node" ,
        pod1TobeKilled: "Pod",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert pod1TobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert pod1TobeKilled.memLimitsStatus == STATUS_LIM["Limit Exceeded"]
        pod1TobeKilled.status = STATUS_POD["Killing"]

        
    @planned(cost=1)
    def MemoryErrorKillPodNotExceedingLimits(self,
        nodeOfPod: "Node" ,
        podTobeKilled: "Pod",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        assert podTobeKilled.atNode == nodeOfPod
        assert nodeOfPod.memCapacity < nodeOfPod.currentRealMemConsumption
        assert podTobeKilled.memLimitsStatus == STATUS_LIM["Limit Met"]
        podTobeKilled.status = STATUS_POD["Killing"]
    # @planned(cost=1)
    def KillPod(self,
        podBeingKilled : "Pod",
        nodeWithPod : "Node" ,
        serviceOfPod: "Service",
        scheduler: "Scheduler",
        pods_daemonset: DaemonSet,
        pods_deployment: Deployment,
        globalVar: GlobalVar
        ):
        if globalVar.block_node_outage_in_progress == False:
            nodeWithPod.currentFormalMemConsumption -= podBeingKilled.memRequest
            nodeWithPod.currentFormalCpuConsumption -= podBeingKilled.cpuRequest
        if podBeingKilled.hasService == True:
            assert podBeingKilled in serviceOfPod.podList
            serviceOfPod.amountOfActivePods -= 1
            serviceOfPod.amountOfPodsInQueue += 1
        if podBeingKilled.hasDeployment == True:
            assert podBeingKilled in pods_deployment.podList
            pods_deployment.amountOfActivePods -= 1
        if podBeingKilled.hasDaemonset == True:
            assert podBeingKilled in pods_daemonset.podList
            pods_daemonset.amountOfActivePods -= 1
        assert globalVar.block_policy_calculated == False
        assert podBeingKilled.atNode == nodeWithPod
        assert podBeingKilled.status == STATUS_POD["Running"]
        assert podBeingKilled.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert podBeingKilled.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        nodeWithPod.amountOfActivePods -= 1
        nodeWithPod.allocatedPodList.remove(podBeingKilled)
        nodeWithPod.allocatedPodList_length -= 1
        if podBeingKilled in nodeWithPod.directedPodList:
            nodeWithPod.directedPodList.remove(podBeingKilled)
            nodeWithPod.directedPodList_length -= 1
        podBeingKilled.status = STATUS_POD["Pending"]
        scheduler.podQueue.add(podBeingKilled)
        scheduler.status = STATUS_SCHED["Changed"] # commented, solves
        scheduler.queueLength += 1
        podBeingKilled.toNode = Node.NODE_NULL
        podBeingKilled.atNode = Node.NODE_NULL

        # scheduler.debug_var = True # TODO DELETEME
        #TODO: make sure that calculation excude situations that lead to negative number in the result
        ## assert podBeingKilled.amountOfActiveRequests == 0 #For Requests
        ## assert amountOfActivePodsPrev == serviceOfPod.amountOfActivePods

    @planned(cost=1)
    def AddNodeToSelector(self, 
        pod1: "Pod",
        selectedNode: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        # assert globalVar.block_node_outage_in_progress == False
        pod1.nodeSelectorList.add(selectedNode) 

    @planned(cost=1)
    def SelectNode(self, 
        pod1: "Pod",
        selectedNode: "Node",
        globalVar: GlobalVar
         ):
        assert globalVar.block_policy_calculated == False
        assert globalVar.block_node_outage_in_progress == False
        assert pod1.toNode == Node.NODE_NULL
        assert selectedNode in pod1.nodeSelectorList
        pod1.toNode = selectedNode    

    @planned(cost=1) # TODO
    def StartPod(self, 
            podStarted: "Pod",
            node: "Node",
            scheduler: "Scheduler",
            serviceTargetForPod: "mservice.Service",
            pods_deployment: Deployment,
            pods_daemonset: DaemonSet,
            globalVar: GlobalVar
        ):
        if globalVar.nodeSelectorsEnabled == True:
            assert node in podStarted.nodeSelectorList
        if podStarted.hasService == True:
            assert podStarted in serviceTargetForPod.podList
            serviceTargetForPod.amountOfPodsInQueue -= 1
            serviceTargetForPod.amountOfActivePods += 1
            serviceTargetForPod.status = STATUS_SERV["Started"]
        if podStarted.hasDeployment == True:
            assert podStarted in pods_deployment.podList
            pods_deployment.amountOfActivePods += 1
        if podStarted.hasDaemonset == True:
            assert podStarted in pods_daemonset.podList
            pods_daemonset.amountOfActivePods += 1
        # if podStarted.memRequest == -1 and podStarted.memLimit > -1:
        #     podStarted.memRequest = podStarted.memLimit
        # if podStarted.cpuRequest == -1 and podStarted.cpuLimit > -1:
        #     podStarted.cpuRequest = podStarted.cpuLimit

        # if podStarted.memRequest > -1 and podStarted.memLimit == -1:
        #     podStarted.memLimit = node.memCapacity
        # if podStarted.cpuRequest > -1 and podStarted.cpuLimit == -1:
        #     podStarted.cpuLimit = node.cpuCapacity

        # if podStarted.memRequest == -1 and podStarted.memLimit == -1:
        #     podStarted.memLimit = node.memCapacity
        #     podStarted.memRequest = 0
        # if podStarted.cpuRequest == -1 and podStarted.cpuLimit == -1:
        #     podStarted.cpuLimit = node.cpuCapacity
        #     podStarted.cpuRequest = 0
        #todo: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
            # assert globalVar.block_node_outage_in_progress == False
        assert globalVar.block_policy_calculated == False
        assert podStarted in scheduler.podQueue
        if podStarted.toNode != Node.NODE_NULL:
            assert node == podStarted.toNode
        assert node.status == STATUS_NODE["Active"]
        assert podStarted.cpuRequest > -1
        assert podStarted.memRequest > -1
        assert node.currentFormalCpuConsumption + podStarted.cpuRequest <= node.cpuCapacity
        assert node.currentFormalMemConsumption + podStarted.memRequest <= node.memCapacity
        node.currentFormalCpuConsumption += podStarted.cpuRequest
        node.currentFormalMemConsumption += podStarted.memRequest
        podStarted.atNode = node       
        # node.pods.add(podStarted) # for new method
        # for pod in node.pods: # -> (forall (?pod-1 - Pod) ... (and (Node-pods ?node ?pod-1)
        #     assert not podStarted in pod.anti_affinite_with #      (not (Pod-anti_affninite_with ?pod-1 ?podStarted))))
        scheduler.queueLength -= 1
        scheduler.podQueue.remove(podStarted)
        node.amountOfActivePods += 1
        node.allocatedPodList.add(podStarted)
        node.allocatedPodList_length += 1
        podStarted.status = STATUS_POD["Running"]      

    @planned(cost=1)
    def MoveRunningPodToAnotherNode(self,
        pod: "Pod",
        nodeFrom: "Node",
        nodeTo: "Node",
        scheduler: "Scheduler",
        globalVar: GlobalVar,
        deployment: Deployment):
        assert pod in deployment.podList # Only pods with deployments can be moved by kalc 
        assert deployment.amountOfActivePods > 1
        # assert globalVar.block_policy_calculated == False
        assert pod.atNode == nodeFrom
        # assert pod.status == STATUS_POD["Running"]
        assert pod.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert pod.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert nodeTo in pod.nodeSelectorList
        assert nodeTo.status == STATUS_NODE["Active"]
        assert nodeTo.currentFormalCpuConsumption + pod.cpuRequest <= nodeTo.cpuCapacity
        assert nodeTo.currentFormalMemConsumption + pod.memRequest <= nodeTo.memCapacity
        assert pod.antiaffinity_met == False
        assert pod.calc_antiaffinity_pods_list_length == 0

        nodeFrom.currentFormalMemConsumption -= pod.memRequest
        nodeFrom.currentFormalCpuConsumption -= pod.cpuRequest
        nodeFrom.amountOfActivePods -= 1
        nodeFrom.allocatedPodList.remove(pod)
        nodeFrom.allocatedPodList_length -= 1
        nodeTo.currentFormalCpuConsumption += pod.cpuRequest
        nodeTo.currentFormalMemConsumption += pod.memRequest
        pod.atNode = nodeTo
        nodeTo.amountOfActivePods += 1
        nodeTo.allocatedPodList.add(pod)
        nodeTo.allocatedPodList_length += 1

        self.script.append(move_pod_with_deployment_script_simple(pod, nodeTo, self.objectList))

        # if podStarted.memRequest == -1 and podStarted.memLimit > -1:
        #     podStarted.memRequest = podStarted.memLimit
        # if podStarted.cpuRequest == -1 and podStarted.cpuLimit > -1:
        #     podStarted.cpuRequest = podStarted.cpuLimit

        # if podStarted.memRequest > -1 and podStarted.memLimit == -1:
        #     podStarted.memLimit = node.memCapacity
        # if podStarted.cpuRequest > -1 and podStarted.cpuLimit == -1:
        #     podStarted.cpuLimit = node.cpuCapacity

        # if podStarted.memRequest == -1 and podStarted.memLimit == -1:
        #     podStarted.memLimit = node.memCapacity
        #     podStarted.memRequest = 0
        # if podStarted.cpuRequest == -1 and podStarted.cpuLimit == -1:
        #     podStarted.cpuLimit = node.cpuCapacity
        #     podStarted.cpuRequest = 0
        #todo: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
            # assert globalVar.block_node_outage_in_progress == False
    
    @planned(cost=1)
    def restart_move_pod(self,
        pod: "Pod",
        ):
        assert pod.

    @planned(cost=1)
    def clear_node_of_pod(self, 
        pod: "Pod",
        selectedNode: "Node",
        globalVar: GlobalVar):
        assert pod.nodes_acceptable_by_antiaffinity_length == 0
        pod.toNode == Node.NODE_NULL

    @planned(cost=1)
    def clean_lists_for_pod_move(self,
        pod:"Pod",
        node:"Node"):
        assert node in pod.nodes_acceptable_by_antiaffinity
        pod.nodes_acceptable_by_antiaffinity.remove(node)
        pod.nodes_acceptable_by_antiaffinity_lenght -= 1

    @planned(cost=1)
    def check_toNode_for_pod_move_for_this_pod(self,
        this_pod:"Pod",
        pod_a: "Pod"):
        if pod_a not in this_pod.calc_checked_pods_from_point_of_this_pod and\
            pod_a.atNode != this_pod.toNode:
            assert pod_a in this_pod.podsMatchedByAntiaffinity
            pod calc_checked_pods_from_point_of_this_pod.add(pod_a)
            pod.calc_checked_pods_from_point_of_this_pod_lenght += 1
    
    @planned(cost=1)
    def check_toNode_for_pod_move_for_that_pod_with_antiaffinity(self,
        this_pod:"Pod",
        pod_a: "Pod"):
        if pod_a not in this_pod.calc_checked_pods_from_point_of_that_pod and \
            this_pod not in pod_a.podsMatchedByAntiaffinity:
            assert pod_a.atNode == this_pod.toNode
            pod calc_checked_pods_from_point_of_that_pod.add(pod_a)
            pod.calc_checked_pods_from_point_of_that_pod_length += 1
    
    @planned(cost=1)
    def check_toNode_for_pod_move_for_that_pod_without_antiaffinity(self,
        this_pod:"Pod",
        pod_a: "Pod"):
        if pod_a not in this_pod.calc_checked_pods_from_point_of_that_pod:
            assert pod_a.affinity_set == False
            assert pod_a.atNode == this_pod.toNode
            pod calc_checked_pods_from_point_of_that_pod.add(pod_a)
            pod.calc_checked_pods_from_point_of_that_pod_length += 1


    @planned(cost=1)
    def check_node_for_pod_move_finished(self,
        pod:"Pod",
        node:"Node"):
        assert pod.calc_checked_pods_from_point_of_this_pod_lenght == pod.podsMatchedByAntiaffinity_length
        assert pod.calc_checked_pods_from_point_of_that_pod == node.amountOfActivePods
        pod.nodes_acceptable_by_antiaffinity.add(node)
        pod.nodes_acceptable_by_antiaffinity_lenght += 1

    @planned(cost=1)
    def move_pod_recomendation_reason_antiaffinity(self,
        pod: "Pod",
        nodeFrom: "Node",
        nodeTo: "Node",
        scheduler: "Scheduler",
        globalVar: GlobalVar,
        deployment: Deployment): 

        assert pod.cpuRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module
        assert pod.memRequest > -1 #TODO: check that number  should be moved to ariphmetics module from functional module

        ## pod  violates antiaffinity of pod_a on nodeFrom:
        assert nodeFrom == pod.atNode
        assert pod_a.atNode == nodeFrom
        assert pod_a in pod.podsMatchedByAffinity

        ## nodeTo is node that is marked as acceptable for pod
        assert nodeTo in pod.nodes_acceptable_by_antiaffinity
        assert nodeTo == pod.toNode

        assert nodeTo in pod.nodeSelectorList
        assert nodeTo.status == STATUS_NODE["Active"]
        assert nodeTo.currentFormalCpuConsumption + pod.cpuRequest <= nodeTo.cpuCapacity
        assert nodeTo.currentFormalMemConsumption + pod.memRequest <= nodeTo.memCapacity

        assert pod in deployment.podList # Only pods with deployments can be moved by kalc 
        assert deployment.amountOfActivePods > 1

        nodeFrom.currentFormalMemConsumption -= pod.memRequest
        nodeFrom.currentFormalCpuConsumption -= pod.cpuRequest
        nodeFrom.amountOfActivePods -= 1
        nodeFrom.allocatedPodList.remove(pod)
        nodeFrom.allocatedPodList_length -= 1
        nodeTo.currentFormalCpuConsumption += pod.cpuRequest
        nodeTo.currentFormalMemConsumption += pod.memRequest
        pod.atNode = nodeTo
        nodeTo.amountOfActivePods += 1
        nodeTo.allocatedPodList.add(pod)
        nodeTo.allocatedPodList_length += 1

        self.script.append(move_pod_with_deployment_script_simple(pod, nodeTo, self.objectList))

        # if podStarted.memRequest == -1 and podStarted.memLimit > -1:
        #     podStarted.memRequest = podStarted.memLimit
        # if podStarted.cpuRequest == -1 and podStarted.cpuLimit > -1:
        #     podStarted.cpuRequest = podStarted.cpuLimit

        # if podStarted.memRequest > -1 and podStarted.memLimit == -1:
        #     podStarted.memLimit = node.memCapacity
        # if podStarted.cpuRequest > -1 and podStarted.cpuLimit == -1:
        #     podStarted.cpuLimit = node.cpuCapacity

        # if podStarted.memRequest == -1 and podStarted.memLimit == -1:
        #     podStarted.memLimit = node.memCapacity
        #     podStarted.memRequest = 0
        # if podStarted.cpuRequest == -1 and podStarted.cpuLimit == -1:
        #     podStarted.cpuLimit = node.cpuCapacity
        #     podStarted.cpuRequest = 0
        #todo: Soft conditions are not supported yet ( prioritization of nodes :  for example healthy  nodes are selected  rather then non healthy if pod  requests such behavior 
            # assert globalVar.block_node_outage_in_progress == False   
    
    @planned(cost=1)
    def mark_node_as_acceptable_for_pod(self,
        pod_a: "Pod",
        pod_at_nodeB:"Pod"
        node_b: "Node",
        scheduler: "Scheduler",
        globalVar: GlobalVar,
        deployment: Deployment):
        assert pod_at_nodeB.atNode == node_b
        pod_a.nodes



    @planned(cost=1)
    def move_pod_recomendation_step_3_finish_pod_movement(self,
        pod: "Pod",
        nodeFrom: "Node",
        nodeTo: "Node",
        scheduler: "Scheduler",
        globalVar: GlobalVar,
        deployment: Deployment):
        found_amount_of_recomendations += 1


    @planned(cost=1)
    def SchedulerCleaned(self, 
        scheduler: "Scheduler",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == False
        assert  scheduler.queueLength == 0
        assert globalVar.block_policy_calculated == True
        scheduler.status = STATUS_SCHED["Clean"]

    @planned(cost=1)
    def Initiate_node_outage_searched(self,
        node_with_outage: "Node",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == False
        # assert globalVar.amountOfNodesDisrupted < globalVar.limitOfAmountOfNodesDisrupted
        assert globalVar.is_node_disrupted == False # TODO: checking ONE node outage! Need fixing
        assert node_with_outage.searchable == True
        assert node_with_outage.status == STATUS_NODE["Active"]
        assert node_with_outage.isSearched == True
        node_with_outage.status = STATUS_NODE["Killing"]
        globalVar.block_node_outage_in_progress = True
        
    @planned(cost=1)
    def Initiate_killing_of_Pod_because_of_node_outage(self,
        node_with_outage: "Node",
        pod_killed: "podkind.Pod",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == True
        assert pod_killed.status == STATUS_POD["Running"]
        assert pod_killed.atNode == node_with_outage
        assert node_with_outage.status == STATUS_NODE["Killing"]
        pod_killed.status = STATUS_POD["Killing"]
        
    @planned(cost=1)
    def NodeOutageFinished(self,
        node: "Node",
        globalVar: GlobalVar):
        assert globalVar.block_node_outage_in_progress == True
        assert node.amountOfActivePods == 0
        assert node.status == STATUS_NODE["Killing"]
        globalVar.amountOfNodesDisrupted += 1
        node.status = STATUS_NODE["Inactive"]
        globalVar.block_node_outage_in_progress = False
        globalVar.is_node_disrupted = True # TODO: checking ONE node outage! Need fixing
        # TODO make ability to calculate multiple nodes outage
        
    @planned(cost=1)
    def ReplaceNullCpuRequestsWithZero(self,
        pod: "Pod"):
        # assert pod.status == STATUS_POD["Running"]
        assert pod.cpuRequest == -1
        pod.cpuRequest = 0
        
    @planned(cost=1)
    def ReplaceNullMemRequestsWithZero(self,
        pod: "Pod"):
        # assert pod.status == STATUS_POD["Running"]
        assert pod.memRequest == -1
        pod.memRequest = 0

