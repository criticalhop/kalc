# from kalc.misc.util import dget
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.ReplicaSet import ReplicaSet
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.kinds.PriorityClass import PriorityClass
from kalc.model.system.Scheduler import Scheduler
from kalc.model.kinds.Deployment import Deployment
from kalc.model.kinds.DaemonSet import DaemonSet
from kalc.model.kinds.ReplicaSet import ReplicaSet
from kalc.model.system.globals import GlobalVar

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
        ", CpuRequest: " + str(poditem.cpuRequest._get_value()) + \
        ", MemRequest: " + str(poditem.memRequest._get_value()) + \
        ", CpuLimit: " + str(poditem.cpuLimit._get_value()) + \
        ", MemLimit: " + str(poditem.memLimit._get_value()) + \
        ", ToNode: " + str(poditem.toNode._property_value) + \
        ", AtNode: " + str(poditem.atNode._property_value) + \
        ", Metadata_labels:" + str([str(x) for x in poditem.metadata_labels._property_value]) + \
        ", hasService: " + str(poditem.hasService._get_value()) + \
        ", hasDeployment: " + str(poditem.hasDeployment._get_value()) + \
        ", hasDaemonset: " + str(poditem.hasDaemonset._get_value()) + \
        ", nodeSelectorSet:" + str(poditem.nodeSelectorSet) + \
        ", nodeSelectorList: " +  str([str(x) for x in poditem.nodeSelectorList._get_value()]) + \
        ", AffinitySet:" + str(poditem.affinity_set._get_value()) + \
        ", podsMatchedByAffinity: " +  str([str(x) for x in poditem.podsMatchedByAffinity._get_value()]) + \
        ", antiaffinity_set:" + str(poditem.antiaffinity_set._get_value()) + \
        ", podsMatchedByAntiaffinity: " +  str([str(x) for x in poditem.podsMatchedByAntiaffinity._get_value()])+\
        ", calc_cantmatch_antiaffinity: " + str(poditem.antiaffinity_set._get_value()) + \
        ", antiaffinity_preferred_set:" + str(poditem.antiaffinity_preferred_set._get_value()) + \
        ", target_number_of_antiaffinity_pods: "+ str(poditem.target_number_of_antiaffinity_pods._get_value()) +\
        ", nodesThatCantAllocateThisPod_length: "+ str(poditem.nodesThatCantAllocateThisPod_length._get_value()))
    
    

    node_loaded_list = filter(lambda x: isinstance(x, Node), objectList)
    print("----------Nodes---------------")
    for nodeitem in node_loaded_list:
        print("## Node:"+ str(nodeitem.metadata_name._get_value()) + \
        ", cpuCapacity: " + str(nodeitem.cpuCapacity._get_value()) + \
        ", memCapacity: " + str(nodeitem.memCapacity._get_value()) + \
        ", CurrentFormalCpuConsumption: "  + str(nodeitem.currentFormalCpuConsumption._get_value()) + \
        ", CurrentFormalMemConsumption: " + str(nodeitem.currentFormalMemConsumption._get_value()) + \
        ", AmountOfPodsOverwhelmingMemLimits: " + str(nodeitem.AmountOfPodsOverwhelmingMemLimits._get_value()) + \
        ", IsNull:"  + str(nodeitem.isNull._get_value()) + \
        ", Status:"  + str(nodeitem.status._get_value()) +\
        ", AmountOfActivePods: " + str(nodeitem.amountOfActivePods._get_value()) +\
        ", Searchable: " + str(nodeitem.searchable._get_value())+\
        ", IsSearched: ", str(nodeitem.isSearched._get_value())+\
        ", different_than: ", str([str(x) for x in nodeitem.different_than._get_value()]) +\
        ", allocatedPodList: ", str([str(x) for x in nodeitem.allocatedPodList._get_value()]) +\
        ", allocatedPodList_length: " + str(nodeitem.allocatedPodList_length._get_value())+\
        ", directedPodList: ", str([str(x) for x in nodeitem.directedPodList._get_value()]) +\
        ", directedPodList_length: " + str(nodeitem.directedPodList_length._get_value()))
    services = filter(lambda x: isinstance(x, Service), objectList)
    print("----------Services---------------")
    for service in services:
        print("## Service: "+str(service.metadata_name)+\
        ", AmountOfActivePods: "+str(service.amountOfActivePods._get_value())+\
        ", Status: " + str(service.status._get_value()) +
        ", Spec_selector: "+str([str(x) for x in service.spec_selector._property_value])+\
        ", Pod_List: "+str([str(x) for x in service.podList._get_value()])+\
        ", IsSearched: ", str(service.isSearched._get_value())+\
        ", amountOfPodsOnDifferentNodes: "+str(service.amountOfPodsOnDifferentNodes._get_value())+\
        ", targetAmountOfPodsOnDifferentNodes: "+str(service.targetAmountOfPodsOnDifferentNodes._get_value())+\
        ", policy_antiaffinity_prefered: "+str(service.policy_antiaffinity_prefered._get_value())+\
        ", antiaffinity_prefered_policy_met: "+str(service.antiaffinity_prefered_policy_met._get_value()))


    prios = filter(lambda x: isinstance(x, PriorityClass), objectList)
    print("----------PriorityClasses---------------")
    for prio in prios:
        print("## PriorityClass: "+str(prio.metadata_name) +" " + str(prio.priority._get_value()))


    scheduler = next(filter(lambda x: isinstance(x, Scheduler), objectList))
    print("----------Shedulers---------------")
    print("## Sheduler: "+str(scheduler.status._get_value()) +\
        " PodList: "+str([str(x) for x in scheduler.podQueue._get_value()]) +\
        " QueueLength: "+str(scheduler.queueLength._get_value()) +\
        " podQueue_excluded_pods: "+str([str(x) for x in scheduler.podQueue_excluded_pods._get_value()]) +\
        " podQueue_excluded_pods_length: "+str(scheduler.podQueue_excluded_pods_length._get_value()))

    deployments_loaded_list = filter(lambda x: isinstance(x, Deployment), objectList)
    print("----------Deployments------------")
    for deployment in deployments_loaded_list:
        print("## Deployment: "+str(deployment.metadata_name._get_value()) +\
        " Spec_replicas: "+ str(deployment.spec_replicas._get_value()) +\
        " Namespace: " + str(deployment.metadata_namespace._get_value())+\
        " AmountOfActivePods: " + str(deployment.amountOfActivePods._get_value())+\
        " Status: " + str(deployment.status._get_value())+\
        " PodList: " + str([str(x) for x in deployment.podList._get_value()])+\
        " PriorityClassName: " + str(deployment.spec_template_spec_priorityClassName._property_value) + \
        " Searchable:" + str(deployment.searchable)+\
        " NumberOfPodsOnSameNodeForDeployment: " + str(deployment.NumberOfPodsOnSameNodeForDeployment._get_value()))
        # " Metadata_labels: " + str([str(x) for x in deployment.template_metadata_labels._property_value]))
    
    daemonsets_loaded_list = filter(lambda x: isinstance(x, DaemonSet), objectList)
    print("----------DaemonSets------------")
    for daemonset in daemonsets_loaded_list:
        print("## DaemonSet: "+str(daemonset.metadata_name._get_value()) +\
        " AmountOfActivePods: " + str(daemonset.amountOfActivePods._get_value())+\
        " Status: " + str(daemonset.status._get_value())+\
        " PodList: " + str([str(x) for x in daemonset.podList._get_value()])+\
        " PriorityClassName: " + str(daemonset.spec_template_spec_priorityClassName._property_value) + \
        " Searchable:" + str(daemonset.searchable))
        # " Metadata_labels: " + str([str(x) for x in deployment.template_metadata_labels._property_value]))

    replicasets_loaded_list = filter(lambda x: isinstance(x, ReplicaSet), objectList)
    print("----------ReplicaSets------------")
    for replicaset in replicasets_loaded_list:
        print("## Replicaset: "+str(replicaset.metadata_name._get_value()) +\
        " hash: " + str(replicaset.hash)+\
        " spec_replicas: " + str(replicaset.spec_replicas._get_value())+\
        " metadata_ownerReferences__kind: " + str(replicaset.metadata_ownerReferences__name._property_value)+\
        " metadata_ownerReferences__name: " + str(replicaset.metadata_ownerReferences__name._property_value))

    globalvar_loaded_list = filter(lambda x: isinstance(x, GlobalVar), objectList)
    print("----------GlobalVar------------")
    list_of_objects_output =['']
    for globalvar_item in globalvar_loaded_list:
        list_of_objects_output.extend(['is_service_disrupted',str(globalvar_item.is_service_disrupted._get_value())])
        list_of_objects_output.extend(['is_deployment_disrupted',str(globalvar_item.is_deployment_disrupted._get_value())])
        list_of_objects_output.extend(['is_daemonset_disrupted',str(globalvar_item.is_daemonset_disrupted._get_value())])
        list_of_objects_output.extend(['is_node_disrupted',str(globalvar_item.is_node_disrupted._get_value())])
        list_of_objects_output.extend(['amountOfNodes',str(globalvar_item.amountOfNodes._get_value())])
        list_of_objects_output.extend(['amountOfNodes_limit',str(globalvar_item.amountOfNodes_limit._get_value())])
        list_of_objects_output.extend(['target_DeploymentsWithAntiaffinity_length',str(globalvar_item.target_DeploymentsWithAntiaffinity_length._get_value())])
        list_of_objects_output.extend(['maxNumberOfPodsOnSameNodeForDeployment',str(globalvar_item.maxNumberOfPodsOnSameNodeForDeployment._get_value())])
        list_of_objects_output.extend(['target_amountOfPodsWithAntiaffinity',str(globalvar_item.target_amountOfPodsWithAntiaffinity._get_value())])
        list_of_objects_output.extend(['target_amount_of_recomendations',str(globalvar_item.target_amount_of_recomendations._get_value())])
    
    print(list_of_objects_output)
