# from guardctl.misc.util import dget
import yaml
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
# def test_dget_ok():
#     d=yaml.load(open("./tests/kube-config/deployments.yaml"))
#     assert dget(d["items"][0], "metadata/name", "NONE") == "redis-master"

# def test_dget_default():
#     d=yaml.load(open("./tests/kube-config/deployments.yaml"))
#     assert dget(d["items"][0], "name", "NONE") == "NONE"

def print_objects(objectList):
    print("=====>")
    pod_loaded_list = filter(lambda x: isinstance(x, Pod), objectList)
    for poditem in pod_loaded_list:
        print("pod:"+ str(poditem.metadata_name._get_value()) + \
            " status: " + str(poditem.status) + \
            " priority_class: " + str(poditem.priorityClass._property_value.metadata_name) + \
            " toNode: " + str(poditem.toNode._property_value) + \
            " atNode: " + str(poditem.atNode._property_value) + \
            " cpuRequest: " + str(poditem.cpuRequest._get_value()) + " memRequest: " + str(poditem.memRequest._get_value()) + \
            " cpuLimit: " + str(poditem.cpuLimit._get_value()) + " memLimit: " + str(poditem.memLimit._get_value()) + \
            " targetService: "+ str(poditem.targetService._property_value) +\
            " metadata_labels:" + str([str(x) for x in poditem.metadata_labels._property_value]))
    node_loaded_list = filter(lambda x: isinstance(x, Node), objectList)
    for nodeitem in node_loaded_list:
        print("node:"+ str(nodeitem.metadata_name._get_value()) + " cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + " memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
        " currentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
        " currentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
        " AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
        " podAmount: "  + str(nodeitem.podAmount._get_value()) + \
        " isNull:"  + str(nodeitem.isNull._get_value()) + \
        " status:"  + str(nodeitem.status._get_value()))
    services = filter(lambda x: isinstance(x, Service), objectList)
    for service in services:
        print("service: "+str(service.metadata_name)+\
            " amountOfActivePods: "+str(service.amountOfActivePods._get_value())+\
            " status: "+str(service.status._get_value()) +
            " spec_selector: "+str([str(x) for x in service.spec_selector._property_value]))

    prios = filter(lambda x: isinstance(x, PriorityClass), objectList)
    for prio in prios:
        print("priorityClass: "+str(prio.metadata_name)+" "+str(prio.priority._get_value()))


    scheduler = next(filter(lambda x: isinstance(x, Scheduler), objectList))