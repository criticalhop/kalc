import sys
from poodle import *
from guardctl.misc.problem import ProblemTemplate
from guardctl.model.kinds.PriorityClass import *
from guardctl.model.kinds.DaemonSet import *
from guardctl.model.kinds.LoadBalancer import *

class Problem2(ProblemTemplate): 
    def problem(self):
        super().problem()
        

        self.priorityHigh = self.addObject(PriorityClass('HighPreemptive'))
        self.priorityHigh.priority = 5
        self.priorityHigh.preemtionPolicy = TYPE_POLICY_PreemptLowerPriority

        self.priorityHighNoPreem = self.addObject(PriorityClass('HighNoPreemptive'))
        self.priorityHighNoPreem.priority = 5
        self.priorityHighNoPreem.preemtionPolicy = TYPE_POLICY_NEVER
        

        self.priorityLow = self.addObject(PriorityClass('Low'))
        self.priorityLow.priority = 1
        self.priorityLow.preemtionPolicy = TYPE_POLICY_NEVER
        
        self.priorityUndefined = self.addObject(PriorityClass('Undefined'))
        self.priorityUndefined.priority =0
        self.priorityUndefined.preemtionPolicy = TYPE_POLICY_NEVER

        self.daemonset1 = self.addObject(Daemonset('DS1'))

        self.nullLb = self.addObject( Loadbalancer('Null'))


        self.service1 = self.addObject(Service('service1'))
        self.service1.amountOfActivePods = 2
        self.service1.status = self.constSymbol["statusServStarted"]
        
        self.service2 = self.addObject(Service('service2'))
        self.service2.amountOfActivePods = 2
        self.service2.status = self.constSymbol["statusServStarted"]
        
        self.service3 = self.addObject(Service('service3'))
        self.service3.amountOfActivePods = 0
        self.service3.status = self.constSymbol["statusServPending"]        

        self.nodeNull = self.addObject(Node('Null'))
        self.nodeNull.state = self.constSymbol["stateNodeInactive"]
        self.nodeNull.type =  self.constSymbol["Null"]

        
        self.node1 = self.addObject(Node('node1'))
        self.node1.state = self.constSymbol["stateNodeActive"]
        self.node1.status = self.constSymbol["statusNodeActive"] ##TODO - make Node activation mechanism
        self.node1.cpuCapacity = 3
        self.node1.memCapacity = 3
        self.node1.currentFormalCpuConsumption = 2
        self.node1.currentFormalMemConsumption = 2
        self.node1.currentRealMemConsumption =0
        self.node1.currentRealCpuConsumption =0
        self.node1.AmountOfPodsOverwhelmingMemLimits =0


        self.node2 = self.addObject(Node('node2'))
        self.node2.state = self.constSymbol["stateNodeActive"]
        self.node2.status = self.constSymbol["statusNodeActive"]
        self.node2.cpuCapacity = 3
        self.node2.memCapacity = 3
        self.node2.memCapacityBarier = 3
        self.node2.currentFormalCpuConsumption = 2
        self.node2.currentFormalMemConsumption = 2
        self.node2.currentRealMemConsumption =0
        self.node2.currentRealCpuConsumption =0
        self.node2.AmountOfPodsOverwhelmingMemLimits =0

        self.node2.prevNode = self.node1
        self.node1.prevNode = self.node2    
        
        
        self.podNull = self.addObject(Pod('podNull'))
        self.podNull.type =  self.constSymbol["Null"]
        
        self.pod1 = self.addObject(Pod('pod1'))
        self.pod1.currentRealCpuConsumption =0
        self.pod1.currentRealMemConsumption =0
        self.pod1.status = self.constSymbol["statusPodActive"]
        self.pod1.memRequest = 1
        self.pod1.cpuRequest = 1
        self.pod1.podNotOverwhelmingLimits = True
        self.pod1.realInitialMemConsumption =0
        self.pod1.realInitialCpuConsumption =0
        self.pod1.type = self.constSymbol["typeTemporary"]
        self.pod1.memLimit =  1
        self.pod1.cpuLimit =  1
        self.pod1.atNode = self.node2
        self.pod1.toNode = self.nodeNull
        self.pod1.memLimitsStatus = self.constSymbol["statusLimMet"]
        self.pod1.amountOfActiveRequests =0
        self.pod1.targetService = self.service1
        self.pod1.priorityClass = self.priorityLow
        
        
        self.pod2 = self.addObject(Pod('pod2'))
        self.pod2.currentRealCpuConsumption =0
        self.pod2.currentRealMemConsumption =0
        self.pod2.status = self.constSymbol["statusPodActive"]
        self.pod2.memRequest = 1
        self.pod2.cpuRequest = 1
        self.pod2.podNotOverwhelmingLimits = True
        self.pod2.realInitialMemConsumption =0
        self.pod2.realInitialCpuConsumption =0        
        self.pod2.type = self.constSymbol["typePersistent"]
        self.pod2.memLimit =  1
        self.pod2.cpuLimit =  1
        self.pod2.atNode = self.node2   
        self.pod2.toNode = self.nodeNull
        self.pod2.memLimitsStatus = self.constSymbol["statusLimMet"]
        ## todo:  for relations  it should give helpful error message when = instead of add.
        self.pod2.amountOfActiveRequests =0
        self.pod2.targetService = self.service1
        self.pod2.priorityClass = self.priorityLow
     
        self.pod3 = self.addObject(Pod('pod3'))
        self.pod3.currentRealCpuConsumption =0
        self.pod3.currentRealMemConsumption =0
        self.pod3.status = self.constSymbol["statusPodActive"]
        self.pod3.memRequest = 1
        self.pod3.cpuRequest = 1
        self.pod3.podNotOverwhelmingLimits = True
        self.pod3.realInitialMemConsumption =0
        self.pod3.realInitialCpuConsumption =0
        self.pod3.type = self.constSymbol["typePersistent"]
        self.pod3.memLimit =  2
        self.pod3.cpuLimit =  2
        self.pod3.atNode = self.node1     
        self.pod3.toNode = self.nodeNull
        self.pod3.memLimitsStatus = self.constSymbol["statusLimMet"]        
        self.pod3.amountOfActiveRequests =0
        self.pod3.targetService = self.service2
        self.pod3.priorityClass = self.priorityLow

        
        self.pod4 = self.addObject(Pod('pod4'))
        self.pod4.currentRealCpuConsumption =0
        self.pod4.currentRealMemConsumption =0
        self.pod4.status = self.constSymbol["statusPodActive"]
        self.pod4.memRequest = 1
        self.pod4.cpuRequest = 1
        self.pod4.podNotOverwhelmingLimits = True
        self.pod4.realInitialMemConsumption =0
        self.pod4.realInitialCpuConsumption =0
        self.pod4.type = self.constSymbol["typeTemporary"]
        self.pod4.memLimit =  1
        self.pod4.cpuLimit =   1
        self.pod4.atNode = self.node1
        self.pod4.toNode = self.nodeNull
        self.pod4.memLimitsStatus = self.constSymbol["statusLimMet"]
        self.pod4.amountOfActiveRequests =0
        self.pod4.targetService = self.service3
        self.pod4.priorityClass = self.priorityLow




        self.pod5 = self.addObject(Pod('pod5'))
        self.pod5.currentRealCpuConsumption =0
        self.pod5.currentRealMemConsumption =0
        self.pod5.status = self.constSymbol["statusPodPending"]
        self.pod5.state = self.constSymbol["statePodInactive"]
        self.pod5.memRequest = 1
        self.pod5.cpuRequest = 1
        self.pod5.podNotOverwhelmingLimits = True
        self.pod5.realInitialMemConsumption =0
        self.pod5.realInitialCpuConsumption =0
        self.pod5.type = self.constSymbol["typeTemporary"]
        self.pod5.memLimit =   1
        self.pod5.cpuLimit =   1
        self.pod5.atNode = self.nodeNull
        self.pod5.toNode = self.nodeNull
        self.pod5.memLimitsStatus = self.constSymbol["statusLimMet"]
        self.pod5.amountOfActiveRequests =0
        self.pod5.targetService = self.service3
        self.pod5.priorityClass = self.priorityHigh


        self.pod6 = self.addObject(Pod('pod6'))
        self.pod6.currentRealCpuConsumption =0
        self.pod6.currentRealMemConsumption =0
        self.pod6.status = self.constSymbol["statusPodPending"]
        self.pod6.state = self.constSymbol["statePodInactive"]
        self.pod6.memRequest = 1
        self.pod6.cpuRequest = 1
        self.pod6.podNotOverwhelmingLimits = True
        self.pod6.realInitialMemConsumption =0
        self.pod6.realInitialCpuConsumption =0
        self.pod6.type = self.constSymbol["typeTemporary"]
        self.pod6.memLimit =   1
        self.pod6.cpuLimit =   1
        self.pod6.atNode = self.nodeNull
        self.pod6.toNode = self.node1
        self.pod6.memLimitsStatus = self.constSymbol["statusLimMet"]
        self.pod6.amountOfActiveRequests =0
        self.pod6.targetService = self.service3
        self.daemonset1.podList.add(self.pod6)
        self.pod6.priorityClass = self.priorityHigh

        
        self.pod7 = self.addObject(Pod('pod7'))
        self.pod7.currentRealCpuConsumption =0
        self.pod7.currentRealMemConsumption =0
        self.pod7.status = self.constSymbol["statusPodPending"]
        self.pod7.state = self.constSymbol["statePodInactive"]
        self.pod7.memRequest = 1
        self.pod7.cpuRequest = 1
        self.pod7.podNotOverwhelmingLimits = True
        self.pod7.realInitialMemConsumption =0
        self.pod7.realInitialCpuConsumption =0
        self.pod7.type = self.constSymbol["typeTemporary"]
        self.pod7.memLimit =   1
        self.pod7.cpuLimit =   1
        self.pod7.atNode = self.nodeNull
        self.pod7.toNode = self.node2
        self.pod7.memLimitsStatus = self.constSymbol["statusLimMet"]
        self.pod7.amountOfActiveRequests =0
        self.pod7.targetService = self.service3
        self.daemonset1.podList.add(self.pod7)
        self.pod7.priorityClass = self.priorityHigh



        # WARN: can do "optimal skips" of RR chain

        self.pod7.nextPod = self.pod1
        self.pod6.nextPod = self.pod7
        self.pod5.nextPod = self.pod6
        self.pod4.nextPod = self.pod5
        self.pod3.nextPod = self.pod4
        self.pod2.nextPod = self.pod3
        self.pod1.nextPod = self.pod2
        self.podNull.nextPod = self.pod1       
        
        
        self.globalVar1 = self.addObject(GlobalVar('globalVar1'))
        self.globalVar1.numberOfRejectedReq =0
        self.globalVar1.lastPod = self.pod1
        self.globalVar1.memCapacity = 6
        self.globalVar1.cpuCapacity = 6
        self.globalVar1.currentFormalCpuConsumption  = 4
        self.globalVar1.currentFormalMemConsumption  = 4
        self.globalVar1.queueLength =0
        self.globalVar1.amountOfPods = 5
          
        self.scheduler1 = self.addObject(Scheduler('scheduler1'))
        self.scheduler1.podQueue.add(self.pod5)
        self.scheduler1.podQueue.add(self.pod6)
        self.scheduler1.podQueue.add(self.pod7)
        self.scheduler1.status = self.constSymbol["statusSchedChanged"]
        self.scheduler1.queueLength = 3  
        