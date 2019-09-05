import sys
from poodle import *
from guardctl.misc.problem import ProblemTemplate
from guardctl.model.kinds.PriorityClass import *
from guardctl.model.kinds.DaemonSet import *
from guardctl.model.kinds.LoadBalancer import *
import guardctl.model.kinds.Service as mservice
import guardctl.model.kinds.Pod as mpod
import guardctl.model.kinds.Node as mnode
import guardctl.model.system.globals as mglobals
import guardctl.model.system.Scheduler as mscheduler
from guardctl.misc.const import *
from guardctl.misc.object_factory import labelFactory
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler

class Problem2(ProblemTemplate): 
    def problem(self):
        # super().problem()
        

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

        self.daemonset1 = self.addObject(DaemonSet('DS1'))

        self.nullLb = self.addObject( LoadBalancer('Null'))


        
        self.service1 = self.addObject(mservice.Service('service1'))
        self.service1.amountOfActivePods = 2
        self.service1.status = STATUS_SERV_STARTED
        self.service.append(self.service1)

        self.service2 = self.addObject(mservice.Service('service2'))
        self.service2.amountOfActivePods = 2
        self.service2.status = STATUS_SERV_STARTED
        self.service.append(self.service2)

        self.service3 = self.addObject(mservice.Service('service3'))
        self.service3.amountOfActivePods = 0
        self.service3.status = STATUS_SERV_PENDING        

        
        self.node1 = self.addObject(mnode.Node('node1'))
        self.node1.status = STATUS_NODE_ACTIVE ##TODO - make Node activation mechanism
        self.node1.cpuCapacity = 3
        self.node1.memCapacity = 3
        self.node1.currentFormalCpuConsumption = 2
        self.node1.currentFormalMemConsumption = 2
        self.node1.currentRealMemConsumption =0
        self.node1.currentRealCpuConsumption =0
        self.node1.AmountOfPodsOverwhelmingMemLimits =0
        self.node.append(self.node1)


        self.node2 = self.addObject(mnode.Node('node2'))
        self.node2.status = STATUS_NODE_ACTIVE
        self.node2.cpuCapacity = 3
        self.node2.memCapacity = 3
        self.node2.memCapacityBarier = 3
        self.node2.currentFormalCpuConsumption = 2
        self.node2.currentFormalMemConsumption = 2
        self.node2.currentRealMemConsumption =0
        self.node2.currentRealCpuConsumption =0
        self.node2.AmountOfPodsOverwhelmingMemLimits =0
        self.node.append(self.node2)

        self.node2.prevNode = self.node1
        self.node1.prevNode = self.node2    
               
        self.pod1 = self.addObject(mpod.Pod('pod1'))
        self.pod1.currentRealCpuConsumption =0
        self.pod1.currentRealMemConsumption =0
        self.pod1.status_phase = STATUS_POD_RUNNING
        self.pod1.memRequest = 2
        self.pod1.cpuRequest = 2
        self.pod1.podNotOverwhelmingLimits = True
        self.pod1.realInitialMemConsumption =0
        self.pod1.realInitialCpuConsumption =0
        self.pod1.memLimit =  1
        self.pod1.cpuLimit =  1
        self.pod1.atNode = self.node2
        self.pod1.toNode = mnode.Node.NODE_NULL
        self.pod1.memLimitsStatus = STATUS_LIM_MET
        self.pod1.amountOfActiveRequests =0
        self.pod1.targetService = self.service1
        self.pod1.priorityClass = self.priorityLow
        self.pod.append(self.pod1)
        
        
        self.pod2 = self.addObject(mpod.Pod('pod2'))
        self.pod2.currentRealCpuConsumption =0
        self.pod2.currentRealMemConsumption =0
        self.pod2.status_phase = STATUS_POD_RUNNING
        self.pod2.memRequest = 2
        self.pod2.cpuRequest = 2
        self.pod2.podNotOverwhelmingLimits = True
        self.pod2.realInitialMemConsumption =0
        self.pod2.realInitialCpuConsumption =0        
        self.pod2.memLimit =  1
        self.pod2.cpuLimit =  1
        self.pod2.atNode = self.node2   
        self.pod2.toNode =  mnode.Node.NODE_NULL
        self.pod2.memLimitsStatus = STATUS_LIM_MET
        ## todo:  for relations  it should give helpful error message when = instead of add.
        self.pod2.amountOfActiveRequests =0
        self.pod2.targetService = self.service1
        self.pod2.priorityClass = self.priorityLow
        self.pod.append(self.pod2)

     
        self.pod3 = self.addObject(mpod.Pod('pod3'))
        self.pod3.currentRealCpuConsumption =0
        self.pod3.currentRealMemConsumption =0
        self.pod3.status_phase = STATUS_POD_RUNNING
        self.pod3.memRequest = 1
        self.pod3.cpuRequest = 1
        self.pod3.podNotOverwhelmingLimits = True
        self.pod3.realInitialMemConsumption =0
        self.pod3.realInitialCpuConsumption =0
        self.pod3.memLimit =  2
        self.pod3.cpuLimit =  2
        self.pod3.atNode = self.node1     
        self.pod3.toNode =  mnode.Node.NODE_NULL
        self.pod3.memLimitsStatus = STATUS_LIM_MET        
        self.pod3.amountOfActiveRequests =0
        self.pod3.targetService = self.service2
        self.pod3.priorityClass = self.priorityLow
        self.pod.append(self.pod3)


        
        self.pod4 = self.addObject(mpod.Pod('pod4'))
        self.pod4.currentRealCpuConsumption =0
        self.pod4.currentRealMemConsumption =0
        self.pod4.status_phase = STATUS_POD_RUNNING
        self.pod4.memRequest = 1
        self.pod4.cpuRequest = 1
        self.pod4.podNotOverwhelmingLimits = True
        self.pod4.realInitialMemConsumption =0
        self.pod4.realInitialCpuConsumption =0
        self.pod4.memLimit =  1
        self.pod4.cpuLimit =   1
        self.pod4.atNode = self.node1
        self.pod4.toNode =  mnode.Node.NODE_NULL
        self.pod4.memLimitsStatus = STATUS_LIM_MET
        self.pod4.amountOfActiveRequests =0
        self.pod4.targetService = self.service3
        self.pod4.priorityClass = self.priorityLow
        self.pod.append(self.pod4)

        self.pod5 = self.addObject(mpod.Pod('pod5'))
        self.pod5.currentRealCpuConsumption =0
        self.pod5.currentRealMemConsumption =0
        self.pod5.status_phase = STATUS_POD_PENDING
        self.pod5.memRequest = 2
        self.pod5.cpuRequest = 2
        self.pod5.podNotOverwhelmingLimits = True
        self.pod5.realInitialMemConsumption =0
        self.pod5.realInitialCpuConsumption =0
        self.pod5.memLimit =   1
        self.pod5.cpuLimit =   1
        self.pod5.atNode =  mnode.Node.NODE_NULL
        self.pod5.toNode =  mnode.Node.NODE_NULL
        self.pod5.memLimitsStatus = STATUS_LIM_MET
        self.pod5.amountOfActiveRequests =0
        self.pod5.targetService = self.service3
        self.pod5.priorityClass = self.priorityHigh
        self.pod.append(self.pod5)



        self.pod6 = self.addObject(mpod.Pod('pod6'))
        self.pod6.currentRealCpuConsumption =0
        self.pod6.currentRealMemConsumption =0
        self.pod6.status_phase = STATUS_POD_PENDING
        self.pod6.memRequest = 2
        self.pod6.cpuRequest = 2
        self.pod6.podNotOverwhelmingLimits = True
        self.pod6.realInitialMemConsumption =0
        self.pod6.realInitialCpuConsumption =0
        self.pod6.memLimit =   1
        self.pod6.cpuLimit =   1
        self.pod6.atNode =  mnode.Node.NODE_NULL
        self.pod6.toNode = self.node1
        self.pod6.memLimitsStatus = STATUS_LIM_MET
        self.pod6.amountOfActiveRequests =0
        self.pod6.targetService = self.service3
        self.daemonset1.podList.add(self.pod6)
        self.pod6.priorityClass = self.priorityHigh
        self.pod.append(self.pod6)


        
        self.pod7 = self.addObject(mpod.Pod('pod7'))
        self.pod7.currentRealCpuConsumption =0
        self.pod7.currentRealMemConsumption =0
        self.pod7.status_phase = STATUS_POD_PENDING
        self.pod7.memRequest = 2
        self.pod7.cpuRequest = 2
        self.pod7.podNotOverwhelmingLimits = True
        self.pod7.realInitialMemConsumption =0
        self.pod7.realInitialCpuConsumption =0
        self.pod7.memLimit =   1
        self.pod7.cpuLimit =   1
        self.pod7.atNode =  mnode.Node.NODE_NULL
        self.pod7.toNode = self.node2
        self.pod7.memLimitsStatus = STATUS_LIM_MET
        self.pod7.amountOfActiveRequests =0
        self.pod7.targetService = self.service3
        self.daemonset1.podList.add(self.pod7)
        self.pod7.priorityClass = self.priorityHigh
        self.pod.append(self.pod7)




        # WARN: can do "optimal skips" of RR chain

        self.pod7.nextPod = self.pod1
        self.pod6.nextPod = self.pod7
        self.pod5.nextPod = self.pod6
        self.pod4.nextPod = self.pod5
        self.pod3.nextPod = self.pod4
        self.pod2.nextPod = self.pod3
        self.pod1.nextPod = self.pod2
        # mpod.Pod.POD_NULL.nextPod = self.pod1       
        
        
        self.globalVar1 = self.addObject(mglobals.GlobalVar('globalVar1'))
        self.globalVar1.numberOfRejectedReq =0
        self.globalVar1.lastPod = self.pod1
        self.globalVar1.memCapacity = 6
        self.globalVar1.cpuCapacity = 6
        self.globalVar1.currentFormalCpuConsumption  = 4
        self.globalVar1.currentFormalMemConsumption  = 4
        self.globalVar1.queueLength =0
        self.globalVar1.amountOfPods = 5
          
        self.scheduler1 = self.addObject(mscheduler.Scheduler('scheduler1'))
        self.scheduler1.podQueue.add(self.pod5)
        self.scheduler1.podQueue.add(self.pod6)
        self.scheduler1.podQueue.add(self.pod7)
        self.scheduler1.status = STATUS_SCHED_CHANGED
        self.scheduler1.queueLength = 3  


class ProblemAutoLink(ProblemTemplate): 
    def problem(self):
        # super().problem()
        

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

        self.daemonset1 = self.addObject(DaemonSet('DS1'))

        self.nullLb = self.addObject( LoadBalancer('Null'))


        
        self.service1 = self.addObject(mservice.Service('service1'))
        self.service1.amountOfActivePods = 0
        self.service1.status = STATUS_SERV_PENDING
        self.service1.spec_selector.add(labelFactory.get("test","test"))
        self.service.append(self.service1)

        self.service2 = self.addObject(mservice.Service('service2'))
        self.service2.amountOfActivePods = 0
        self.service2.status = STATUS_SERV_PENDING
        self.service2.spec_selector.add(labelFactory.get("test2","test2"))
        self.service.append(self.service2)

        self.service3 = self.addObject(mservice.Service('service3'))
        self.service3.amountOfActivePods = 0
        self.service3.spec_selector.add(labelFactory.get("test3","test3"))
        self.service3.status = STATUS_SERV_PENDING        

        
        self.node1 = self.addObject(mnode.Node('node1'))
        self.node1.status = STATUS_NODE_ACTIVE ##TODO - make Node activation mechanism
        self.node1.cpuCapacity = 3
        self.node1.memCapacity = 3
        self.node1.currentFormalCpuConsumption = 2
        self.node1.currentFormalMemConsumption = 2
        self.node1.currentRealMemConsumption =0
        self.node1.currentRealCpuConsumption =0
        self.node1.AmountOfPodsOverwhelmingMemLimits =0
        self.node.append(self.node1)


        self.node2 = self.addObject(mnode.Node('node2'))
        self.node2.status = STATUS_NODE_ACTIVE
        self.node2.cpuCapacity = 3
        self.node2.memCapacity = 3
        self.node2.memCapacityBarier = 3
        self.node2.currentFormalCpuConsumption = 2
        self.node2.currentFormalMemConsumption = 2
        self.node2.currentRealMemConsumption =0
        self.node2.currentRealCpuConsumption =0
        self.node2.AmountOfPodsOverwhelmingMemLimits =0
        self.node.append(self.node2)

        self.node2.prevNode = self.node1
        self.node1.prevNode = self.node2    
               
        self.pod1 = self.addObject(mpod.Pod('pod1'))
        self.pod1.currentRealCpuConsumption =0
        self.pod1.currentRealMemConsumption =0
        self.pod1.status_phase = STATUS_POD_RUNNING
        self.pod1.memRequest = 2
        self.pod1.cpuRequest = 2
        self.pod1.podNotOverwhelmingLimits = True
        self.pod1.realInitialMemConsumption =0
        self.pod1.realInitialCpuConsumption =0
        self.pod1.memLimit =  1
        self.pod1.cpuLimit =  1
        self.pod1.atNode = self.node2
        self.pod1.toNode = mnode.Node.NODE_NULL
        self.pod1.memLimitsStatus = STATUS_LIM_MET
        self.pod1.amountOfActiveRequests =0
        # self.pod1.targetService = self.service1
        self.pod1.metadata_labels.add(labelFactory.get("test","test"))
        self.pod1.priorityClass = self.priorityLow
        self.pod.append(self.pod1)
        
        
        self.pod2 = self.addObject(mpod.Pod('pod2'))
        self.pod2.currentRealCpuConsumption =0
        self.pod2.currentRealMemConsumption =0
        self.pod2.status_phase = STATUS_POD_RUNNING
        self.pod2.memRequest = 2
        self.pod2.cpuRequest = 2
        self.pod2.podNotOverwhelmingLimits = True
        self.pod2.realInitialMemConsumption =0
        self.pod2.realInitialCpuConsumption =0        
        self.pod2.memLimit =  1
        self.pod2.cpuLimit =  1
        self.pod2.atNode = self.node2   
        self.pod2.toNode =  mnode.Node.NODE_NULL
        self.pod2.memLimitsStatus = STATUS_LIM_MET
        ## todo:  for relations  it should give helpful error message when = instead of add.
        self.pod2.amountOfActiveRequests =0
        # self.pod2.targetService = self.service1
        self.pod2.metadata_labels.add(labelFactory.get("test","test"))
        self.pod2.priorityClass = self.priorityLow
        self.pod.append(self.pod2)

     
        self.pod3 = self.addObject(mpod.Pod('pod3'))
        self.pod3.currentRealCpuConsumption =0
        self.pod3.currentRealMemConsumption =0
        self.pod3.status_phase = STATUS_POD_RUNNING
        self.pod3.memRequest = 1
        self.pod3.cpuRequest = 1
        self.pod3.podNotOverwhelmingLimits = True
        self.pod3.realInitialMemConsumption =0
        self.pod3.realInitialCpuConsumption =0
        self.pod3.memLimit =  2
        self.pod3.cpuLimit =  2
        self.pod3.atNode = self.node1     
        self.pod3.toNode =  mnode.Node.NODE_NULL
        self.pod3.memLimitsStatus = STATUS_LIM_MET        
        self.pod3.amountOfActiveRequests =0
        # self.pod3.targetService = self.service2
        self.pod3.metadata_labels.add(labelFactory.get("test2","test2"))
        self.pod3.priorityClass = self.priorityLow
        self.pod.append(self.pod3)


        
        self.pod4 = self.addObject(mpod.Pod('pod4'))
        self.pod4.currentRealCpuConsumption =0
        self.pod4.currentRealMemConsumption =0
        self.pod4.status_phase = STATUS_POD_RUNNING
        self.pod4.memRequest = 1
        self.pod4.cpuRequest = 1
        self.pod4.podNotOverwhelmingLimits = True
        self.pod4.realInitialMemConsumption =0
        self.pod4.realInitialCpuConsumption =0
        self.pod4.memLimit =  1
        self.pod4.cpuLimit =   1
        self.pod4.atNode = self.node1
        self.pod4.toNode =  mnode.Node.NODE_NULL
        self.pod4.memLimitsStatus = STATUS_LIM_MET
        self.pod4.amountOfActiveRequests =0
        # self.pod4.targetService = self.service3
        self.pod4.metadata_labels.add(labelFactory.get("test3","test3"))
        self.pod4.priorityClass = self.priorityLow
        self.pod.append(self.pod4)

        self.pod5 = self.addObject(mpod.Pod('pod5'))
        self.pod5.currentRealCpuConsumption =0
        self.pod5.currentRealMemConsumption =0
        self.pod5.status_phase = STATUS_POD_PENDING
        self.pod5.memRequest = 2
        self.pod5.cpuRequest = 2
        self.pod5.podNotOverwhelmingLimits = True
        self.pod5.realInitialMemConsumption =0
        self.pod5.realInitialCpuConsumption =0
        self.pod5.memLimit =   1
        self.pod5.cpuLimit =   1
        self.pod5.atNode =  mnode.Node.NODE_NULL
        self.pod5.toNode =  mnode.Node.NODE_NULL
        self.pod5.memLimitsStatus = STATUS_LIM_MET
        self.pod5.amountOfActiveRequests =0
        # self.pod5.targetService = self.service3
        self.pod5.metadata_labels.add(labelFactory.get("test3","test3"))
        self.pod5.priorityClass = self.priorityHigh
        self.pod.append(self.pod5)



        self.pod6 = self.addObject(mpod.Pod('pod6'))
        self.pod6.currentRealCpuConsumption =0
        self.pod6.currentRealMemConsumption =0
        self.pod6.status_phase = STATUS_POD_PENDING
        self.pod6.memRequest = 2
        self.pod6.cpuRequest = 2
        self.pod6.podNotOverwhelmingLimits = True
        self.pod6.realInitialMemConsumption =0
        self.pod6.realInitialCpuConsumption =0
        self.pod6.memLimit =   1
        self.pod6.cpuLimit =   1
        self.pod6.atNode =  mnode.Node.NODE_NULL
        self.pod6.toNode = self.node1
        self.pod6.memLimitsStatus = STATUS_LIM_MET
        self.pod6.amountOfActiveRequests =0
        # self.pod6.targetService = self.service3
        self.pod6.metadata_labels.add(labelFactory.get("test3","test3"))
        self.daemonset1.podList.add(self.pod6)
        self.pod6.priorityClass = self.priorityHigh
        self.pod.append(self.pod6)


        
        self.pod7 = self.addObject(mpod.Pod('pod7'))
        self.pod7.currentRealCpuConsumption =0
        self.pod7.currentRealMemConsumption =0
        self.pod7.status_phase = STATUS_POD_PENDING
        self.pod7.memRequest = 2
        self.pod7.cpuRequest = 2
        self.pod7.podNotOverwhelmingLimits = True
        self.pod7.realInitialMemConsumption =0
        self.pod7.realInitialCpuConsumption =0
        self.pod7.memLimit =   1
        self.pod7.cpuLimit =   1
        self.pod7.atNode =  mnode.Node.NODE_NULL
        self.pod7.toNode = self.node2
        self.pod7.memLimitsStatus = STATUS_LIM_MET
        self.pod7.amountOfActiveRequests =0
        # self.pod7.targetService = self.service3
        self.pod7.metadata_labels.add(labelFactory.get("test3","test3"))
        self.daemonset1.podList.add(self.pod7)
        self.pod7.priorityClass = self.priorityHigh
        self.pod.append(self.pod7)




        # WARN: can do "optimal skips" of RR chain

        self.pod7.nextPod = self.pod1
        self.pod6.nextPod = self.pod7
        self.pod5.nextPod = self.pod6
        self.pod4.nextPod = self.pod5
        self.pod3.nextPod = self.pod4
        self.pod2.nextPod = self.pod3
        self.pod1.nextPod = self.pod2
        # mpod.Pod.POD_NULL.nextPod = self.pod1       
        
        
        self.globalVar1 = self.addObject(mglobals.GlobalVar('globalVar1'))
        self.globalVar1.numberOfRejectedReq =0
        self.globalVar1.lastPod = self.pod1
        self.globalVar1.memCapacity = 6
        self.globalVar1.cpuCapacity = 6
        self.globalVar1.currentFormalCpuConsumption  = 4
        self.globalVar1.currentFormalMemConsumption  = 4
        self.globalVar1.queueLength =0
        self.globalVar1.amountOfPods = 5
          
        self.scheduler1 = self.addObject(mscheduler.Scheduler('scheduler1'))
        self.scheduler1.podQueue.add(self.pod5)
        self.scheduler1.podQueue.add(self.pod6)
        self.scheduler1.podQueue.add(self.pod7)
        self.scheduler1.status = STATUS_SCHED_CHANGED
        self.scheduler1.queueLength = 3  
    
    def print_objects(self):
        print("=====>")
        pod_loaded_list = filter(lambda x: isinstance(x, Pod), self.objectList)
        for poditem in pod_loaded_list:
            print("pod:"+ str(poditem.metadata_name._get_value()) + \
                " status_phase: " + str(poditem.status_phase) + \
                " priority_class: " + str(poditem.priorityClass._property_value.metadata_name) + \
                " toNode: " + str(poditem.toNode._property_value) + \
                " atNode: " + str(poditem.atNode._property_value) + \
                " cpuRequest: " + str(poditem.cpuRequest._get_value()) + " memRequest: " + str(poditem.memRequest._get_value()) + \
                " cpuLimit: " + str(poditem.cpuLimit._get_value()) + " memLimit: " + str(poditem.memLimit._get_value()) + \
                " targetService: "+ str(poditem.targetService._property_value) +\
                " metadata_labels:" + str([str(x) for x in poditem.metadata_labels._property_value]))
        node_loaded_list = filter(lambda x: isinstance(x, Node), self.objectList)
        for nodeitem in node_loaded_list:
            print("node:"+ str(nodeitem.metadata_name._get_value()) + " cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + " memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
            " currentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
            " currentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
            " AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
            " podAmount: "  + str(nodeitem.podAmount._get_value()) + \
            " isNull:"  + str(nodeitem.isNull._get_value()) + \
            " status:"  + str(nodeitem.status._get_value()))
        services = filter(lambda x: isinstance(x, Service), self.objectList)
        for service in services:
            print("service: "+str(service.metadata_name)+\
                " amountOfActivePods: "+str(service.amountOfActivePods._get_value())+\
                " status: "+str(service.status._get_value()) + 
                " spec_selector: "+str([str(x) for x in service.spec_selector._property_value]))
        
        prios = filter(lambda x: isinstance(x, PriorityClass), self.objectList)
        for prio in prios:
            print("priorityClass: "+str(prio.metadata_name)+" "+str(prio.priority._get_value()))


