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
from guardctl.misc.problem import ProblemTemplate
from guardctl.misc.util import cpuConvertToAbstractProblem, memConvertToAbstractProblem
from guardctl.model.search import Check_services, Check_deployments, Check_daemonsets, OptimisticRun, CheckNodeOutage, Check_node_outage_and_service_restart


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