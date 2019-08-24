from action.pydlKubeAction import *  
from object.commonObject import *
from object.addedNumbers10 import *
import poodle.problem

class ProblemTemplate(poodle.problem.Problem):
    constSymbol = {}
    pod = []
    node = []
    kubeProxy = []
    loadbalancer = []
    service = []
    daemonSet = []
    request = []
    containerConfig = []
    priorityDict = {}
    
    def constFactory(self, statusNameList, objType):
        for statusName in statusNameList:
            self.constSymbol[statusName] = self.addObject(objType(statusName))

    def problem(self):
        statusList = ["statusReqAtStart",
        "statusReqAtLoadbalancer",
        "statusReqAtKubeproxy",
        "statusReqAtPodInput",
        "statusReqMemResourceConsumed",
        "statusReqCpuResourceConsumed",
        "statusReqResourcesConsumed",
        "statusReqDirectedToPod",
        "statusReqRequestPIDToBeEnded",
        "statusReqCpuResourceReleased",
        "statusReqMemResourceReleased",
        "statusReqResourcesReleased",
        "statusReqRequestTerminated",
        "statusReqRequestFinished",
        "statusPodAtConfig",
        "statusPodReadyToStart",
        "statusPodActive",
        "statusPodPending",
        "statusPodAtManualCreation",
        "statusPodDirectedToNode",
        "statusPodCpuConsumed",
        "statusPodResourceFormalConsumptionFailed",
        "statusPodFailedToStart",
        "statusPodReadyToStart2",
        "statusPodMemConsumed",
        "statusPodMemConsumedFailed",
        "statusPodBindedToNode",
        "statusPodRunning",
        "statusPodSucceeded", # may be lost be careful
        "statusPodKilling",
        "statusPodFailed",
        "statusNodeRunning",
        "statusNodeSucceded",
        "statusPodPending",
        "statusNodeDeleted",
        "statusPodInactive",
        "statusNodeActive",
        "statusNodeInactive",
        "statusReqDirectedToNode",
        "statusReqNodeCapacityOverwhelmed",
        "statusLimMet",
        "statusLimOverwhelmed",
        "test",
        "statusPodToBeTerminated",
        "statusPodTerminated",
        "statusServPending",
        "statusServStarted",
        "statusServInterrupted",
        "statusReqRunning",
        "statusPodInitialConReleased",
        "statusPodGlobalMemConsumed",
        "statusPodGlobalCpuConsumed",
        "statusPodFormalConReleased",
        "statusSchedClean",
        "statusSchedChanged",
        "statusPodReadyToStart",
        "statusPodFinishedPlacement"]
        self.constFactory(statusList, Status)

        stateList = [
        "statePodSucceeded",
        "statePodRunning",
        "statePodPending",
        "statePodActive",
        "statePodInactive",
        "stateReqStarted",
        "stateRequestActive",
        "stateRequestInactive",
        "stateNodeActive",
        "stateNodeInactive"]
        self.constFactory(stateList, State)

        typeList = ["typeTemporary","typePersistent","Null","notNull","Issue01","PreemptLowerPriority","Never"]
        self.constFactory(typeList, Type)
        
        modeList = ["modeUsermode","modeIptables"]
        self.constFactory(modeList, Mode)

        self.constSymbol["statusReqAtStart"].sequence =  1
        self.constSymbol["statusReqAtLoadbalancer"].sequence =  2
        self.constSymbol["statusReqAtKubeproxy"].sequence =  3
        self.constSymbol["statusReqDirectedToPod"].sequence =  4
        self.constSymbol["statusReqAtPodInput"].sequence =  5
        self.constSymbol["statusReqCpuResourceConsumed"].sequence =  6
        self.constSymbol["statusReqMemResourceConsumed"].sequence =  7
        self.constSymbol["statusReqResourcesConsumed"].sequence =  8
        self.constSymbol["statusReqRequestPIDToBeEnded"].sequence =  9
        self.constSymbol["statusReqCpuResourceReleased"].sequence =  10
        self.constSymbol["statusReqMemResourceReleased"].sequence =  11
        self.constSymbol["statusReqResourcesReleased"].sequence =  12
        self.constSymbol["statusReqRequestTerminated"].sequence =  13
        self.constSymbol["statusReqRequestFinished"].sequence =  20