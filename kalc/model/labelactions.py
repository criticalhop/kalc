import sys
from poodle import planned
from logzero import logger
from kalc.model.system.base import HasLimitsRequests, HasLabel
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
from kalc.misc.problem import ProblemTemplate
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem

class LabelsModel(ProblemTemplate):
    def add_goal_in(self, goal_entry):
        self.goals_in.extend(goal_entry)

    def add_goal_eq(self, goal_entry):
        self.goals_eq.extend(goal_entry)

    def generate_goal(self):
        self.add_goal_in([[self.pod1, pod2.podsMatchedByAntiaffinity]])

    def goal(self):
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
    def add_label_to_pod(self,
        pod: Pod,
        label: Label):
        pod.metadata_labels.add(label)

    @planned(cost=1)
    def add_antiaffinity_label_to_pod(self,
        pod: Pod,
        label: Label):
        pod.antiaffinity_labels.add(label)
        pod.antiaffinity_labels_length += 1
    @planned(cost=1)
    def remove_label_from_pod(self,
        pod: Pod,
        label: Label):
        pod.metadata_labels.add(label)

    @planned(cost=1)
    def remove_antiaffinity_label_from_pod(self,
        pod: Pod,
        label: Label):
        pod.antiaffinity_labels.add(label)
        pod.antiaffinity_labels_length += 1
    
    @planned(cost=1)
    def add_label_to_label_connection_with_antiaffinity(self,
        pod_source: Pod,
        pod_target: Pod,
        label: Label,
        label_connection: Label_connection):
        assert pod_source.is_checked_as_source_for_labels == True
        assert pod_target.is_checked_as_target_for_labels == True
        assert pod_source == label_connection.pod_source
        assert pod_target == label_connection.pod_target
        assert label in pod_source.antiaffinity_labels
        assert label in pod_target.metadata_labels
        assert label in label_connection.matching_labels_candidates        

        label_connection.matching_labels_candidates.remove(label)
        label_connection.Label_connection.add(label)
        label_connection.Label_connection_lenth += 1

    @planned(cost=1)
    def Mark_pod_as_matching(self,
                service1: Service,
                scheduler: "Scheduler",
                globalVar: GlobalVar,
                pod_source: Pod,
                pod_target: Pod,
                label_connection: Label_connection
         ):
        assert pod_source.is_checked_as_source_for_labels == True
        assert pod_target.is_checked_as_target_for_labels == True
        assert pod_source == label_connection.pod_source
        assert pod_target == label_connection.pod_target
        assert label_connection.Label_connection_lenth == pod_source.antiaffinity_labels_length
        pod_source.antiaffinity_pods_list.add(pod_target)

        