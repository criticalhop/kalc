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
from kalc.misc.problem import ProblemTemplate
from kalc.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from kalc.model.search import Check_services, Check_deployments, Check_daemonsets, OptimisticRun, CheckNodeOutage, Check_node_outage_and_service_restart


class DebuggingCheckNodeOutage(CheckNodeOutage):
    @planned(cost=100)
    def BrakeNodeOutageGoal(self,
        globalVar: GlobalVar,
        node: Node,
        node_amountOfActivePods: int):
        assert node.amountOfActivePods == 0
        assert node.isNull == False 
        globalVar.is_node_disrupted = True

    @planned(cost=2000)
    def BrakeKillPod(self,
        globalVar: GlobalVar,
        node: Node):
        assert node.isNull == False 
        node.amountOfActivePods -= 1