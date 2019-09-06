import sys
from poodle import * 
from guardctl.misc.const import *
from tests.problem.kubeproblem1 import * 
from guardctl.model.search import *



class Test_case_1(Problem2,K8ServiceInterruptSearch ):
    def goal(self):
        self.pod[0].status == STATUS_POD["Running"]

class Test_case_2(Problem2,K8ServiceInterruptSearch ):
    def goal(self):
        self.pod[1].status == STATUS_POD["Pending"]

class Test_case_3(Problem2,K8ServiceInterruptSearch ):
    def goal(self):
        self.pod[0].status == STATUS_POD["Killing"]

class TestServiceInterrupted(Problem2,K8ServiceInterruptSearch ):
    def goal(self):
        self.service[0].status == STATUS_SERV["Interrupted"]


class TestServiceInterruptedAutoLink(ProblemAutoLink,K8ServiceInterruptSearch ):
    def goal(self):
        self.service[0].status == STATUS_SERV["Interrupted"]


class Test_case_4_service_connected_to_pod(K8ServiceInterruptSearch ):
    def goal(self):
        pod_loaded_list = filter(lambda x: isinstance(x, Pod), self.objectList)
        for poditem in pod_loaded_list:
            if poditem.metadata_labels._get_value() is None:
                labels = "NONE"
            else:
                labels = str([str(x) for x in poditem.metadata_labels._get_value()])
            print("pod:"+ str(poditem.metadata_name._get_value()) + " status: " + str(poditem.status) + " spec_nodeName: " + str(poditem.spec_nodeName._get_value()) + " cpuRequest: " + str(poditem.cpuRequest._get_value()) + " memRequest: " + str(poditem.memRequest._get_value()) + \
                " cpuLimit: " + str(poditem.cpuLimit._get_value()) + " memLimit: " + str(poditem.memLimit._get_value())+ \
                "metadata_labels:" + labels)
        node_loaded_list = filter(lambda x: isinstance(x, Node), self.objectList)
        for nodeitem in node_loaded_list:
            print("node:"+ str(nodeitem.metadata_name._get_value()) + " cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + " memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
            " currentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
            " currentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
            " AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
            " podAmount: "  + str(nodeitem.podAmount._get_value()) + \
            " isNull:"  + str(nodeitem.isNull._get_value()) + \
            " status:"  + str(nodeitem.status._get_value()))
        service_loaded_list = filter(lambda x: isinstance(x, Service), self.objectList)
        for serviceitem in service_loaded_list:
            if serviceitem.spec_selector._get_value() is None:
                labels = "NONE"
            else:
                labels = str([str(x) for x in serviceitem.spec_selector._get_value()])
         
            print(" service:" + str(serviceitem.metadata_name._get_value())  + \
                    " spec_selector: " + labels + \
                    " lastPod: " + str(serviceitem.lastPod._get_value()) + \
                    " amountOfActivePods: " + str(serviceitem.amountOfActivePods._get_value()) + \
                    " status: " +  str(serviceitem.status._get_value())) 

        self.service_one = next(filter(lambda x: isinstance(x, Service), self.objectList))
        self.service_one == STATUS_SERV["Started"]
