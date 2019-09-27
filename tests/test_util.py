# from guardctl.misc.util import dget
import yaml
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.system.Scheduler import Scheduler
from guardctl.model.kinds.Deployment import Deployment
from guardctl.model.system.globals import GlobalVar

# def test_dget_ok():
#     d=yaml.load(open("./tests/kube-config/deployments.yaml"))
#     assert dget(d["items"][0], "metadata/name", "NONE") == "redis-master"

# def test_dget_default():
#     d=yaml.load(open("./tests/kube-config/deployments.yaml"))
#     assert dget(d["items"][0], "name", "NONE") == "NONE"
def print_objects(objectList):
    print("<==== Domain Object List =====>")

    pod_loaded_list = filter(lambda x: isinstance(x, Pod), objectList)
    print("----------Pods---------------")
    for poditem in pod_loaded_list:
        print("## Pod:"+ str(poditem.metadata_name._get_value()) + \
        ", Status: " + str(poditem.status._get_value()) + \
        ", Priority_class: " + str(poditem.priorityClass._property_value.metadata_name) + \
        ", ToNode: " + str(poditem.toNode._property_value) + \
        ", AtNode: " + str(poditem.atNode._property_value) + \
        ", CpuRequest: " + str(poditem.cpuRequest._get_value()) + \
        ", MemRequest: " + str(poditem.memRequest._get_value()) + \
        ", CpuLimit: " + str(poditem.cpuLimit._get_value()) + \
        ", MemLimit: " + str(poditem.memLimit._get_value()) + \
        ", TargetService: "+ str(poditem.targetService._property_value) +\
        ", Metadata_labels:" + str([str(x) for x in poditem.metadata_labels._property_value]))
    
    node_loaded_list = filter(lambda x: isinstance(x, Node), objectList)
    print("----------Nodes---------------")
    for nodeitem in node_loaded_list:
        print("## Node:"+ str(nodeitem.metadata_name._get_value()) + \
        ", cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + \
        ", memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
        ", CurrentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
        ", CurrentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
        ", AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
        ", PodAmount: "  + str(nodeitem.podAmount._get_value()) + \
        ", IsNull:"  + str(nodeitem.isNull._get_value()) + \
        ", Status:"  + str(nodeitem.status._get_value()))
    services = filter(lambda x: isinstance(x, Service), objectList)
    print("----------Services---------------")
    for service in services:
        print("## Service: "+str(service.metadata_name)+\
        ", AmountOfActivePods: "+str(service.amountOfActivePods._get_value())+\
        ", Status: " + str(service.status._get_value()) +
        ", Spec_selector: "+str([str(x) for x in service.spec_selector._property_value]))


    prios = filter(lambda x: isinstance(x, PriorityClass), objectList)
    print("----------PriorityClasses---------------")
    for prio in prios:
        print("## PriorityClass: "+str(prio.metadata_name) +" " + str(prio.priority._get_value()))


    scheduler = next(filter(lambda x: isinstance(x, Scheduler), objectList))
    print("----------Shedulers---------------")
    print("## Sheduler: "+str(scheduler.status._get_value()) +\
        " PodList: "+str([str(x) for x in scheduler.podQueue._get_value()]) +\
        " QueueLength: "+str(scheduler.queueLength._get_value()))

    deployments_loaded_list = filter(lambda x: isinstance(x, Deployment), objectList)
    print("----------Deployments------------")
    for deployment in deployments_loaded_list:
        print("## Deployment: "+str(deployment.metadata_name._get_value()) +\
        " Replicas: "+ str(deployment.spec_replicas._get_value()) +\
        " Namespace: " + str(deployment.metadata_namespace._get_value())+\
        " AmountOfActivePods: " + str(deployment.amountOfActivePods._get_value())+\
        " Status: " + str(deployment.status._get_value())+\
        " PodList: " + str([str(x) for x in deployment.podList._get_value()])+\
        " PriorityClassName: " + str(deployment.spec_template_spec_priorityClassName._property_value))#+\
        # " Metadata_labels: " + str([str(x) for x in deployment.template_metadata_labels._property_value]))
    
    globalvar_loaded_list = filter(lambda x: isinstance(x, GlobalVar), objectList)
    print("----------GlobalVar------------")
    list_of_objects_output =['']
    for globalvar_item in globalvar_loaded_list:
        list_of_objects_output.extend(['is_service_interrupted',str(globalvar_item.is_service_interrupted._get_value())])
        list_of_objects_output.extend(['is_depl_interrupted',str(globalvar_item.is_depl_interrupted._get_value())])
    print(list_of_objects_output)