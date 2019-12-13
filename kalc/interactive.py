import subprocess
import json
from poodle import Object
from kalc.model.full import kinds_collection
from kalc.misc.kind_filter import FilterByLabelKey, FilterByName, KindPlaceholder
from kalc.model.kubernetes import KubernetesCluster
import kalc.policy 
from kalc.model.search import KubernetesModel
from kalc.model.kinds.Deployment import YAMLable, Deployment
from pygments import highlight
from pygments.lexers.diff import DiffLexer
from pygments.formatters.terminal import TerminalFormatter
import random

kalc_state_objects = []
kind = KindPlaceholder

kalc.policy.policy_engine.register_state_objects(kalc_state_objects)

for k, v in kinds_collection.items():
    v.by_name = FilterByName(k, kalc_state_objects)
    v.by_label = FilterByLabelKey(k, kalc_state_objects)
    globals()[k] = v
    setattr(kind, k, v)

def update():
    "Fetch information from currently selected ccluster"
    k = KubernetesCluster()
    result = subprocess.run(['kubectl', 'get', 'all', '-o=json'], stdout=subprocess.PIPE)
    if len(result.stdout) < 100:
        raise SystemError("Error using kubectl. Make sure `kubectl get pods` is working.")
    data = json.loads(result.stdout.decode("utf-8"))
    for item in data["items"]:
        k.load_item(item)

    result = subprocess.run(['kubectl', 'get', 'node', '-o=json'], stdout=subprocess.PIPE)
    if len(result.stdout) < 100:
        raise SystemError("Error using kubectl. Make sure `kubectl get pods` is working.")
    data = json.loads(result.stdout.decode("utf-8"))
    for item in data["items"]:
        k.load_item(item)
    
    k._build_state()
    global kalc_state_objects
    kalc_state_objects.clear()
    kalc_state_objects.extend(k.state_objects)

def run():
    kube = KubernetesModel(kalc_state_objects)
    policy_added = False
    for ob in kalc_state_objects:
        if isinstance(ob.policy, str): continue # STUB. find and fix
        for pname, pobject in ob.policy._instantiated_policies.items():
            if pobject.activated:
                policy_added = True
                for hname, hval in pobject.hypotheses.items():
                    # print("Adding hypothesis goal")
                    pobject.clear_goal()
                    hval()
                    kube.add_goal_eq(pobject.get_goal_eq())
                    kube.add_goal_in(pobject.get_goal_in())
                for name in dir(pobject):
                    if callable(getattr(pobject, name)) and hasattr(getattr(pobject, name), "_planned"):
                        # print("Adding planned method from policy", name)
                        kube.add_external_method(getattr(pobject, name))
                        # setattr(kube, name, getattr(pobject, name))
    kube.run(timeout=999000, sessionName="kalc")
    # TODO. STUB
    # TODO example hanlers and patches
    for obj in kalc_state_objects:
        if isinstance(obj, Deployment):
            if "redis-slave" in str(obj.metadata_name):
                obj.affinity_required_handler()
                # obj.scale_replicas_handler(random.randint(4,10))

    if policy_added: patch()
    for a in kube.plan:
        print(a)
        r = a()
        if isinstance(r, dict) and "kubectl" in r:
            print(">>", r["kubectl"])
    # print summary

def patch():
    for obj in kalc_state_objects:
        if isinstance(obj, Deployment):
            # print("patch for ", obj.metadata_name)
            print(highlight(obj.get_patch(), DiffLexer(), TerminalFormatter()))

def apply():
    pass


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
        ", hasDaemonset: " + str(poditem.hasDaemonset._get_value()))
    
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
        ", Status:"  + str(nodeitem.status._get_value()) +\
        ", AmountOfActivePods: " + str(nodeitem.amountOfActivePods._get_value()) +\
        ", Searchable: " + str(nodeitem.searchable._get_value())+\
        ", IsSearched: ", str(nodeitem.isSearched._get_value())+\
        ", different_than: ", str([str(x) for x in nodeitem.different_than._get_value()]))
    services = filter(lambda x: isinstance(x, Service), objectList)
    print("----------Services---------------")
    for service in services:
        print("## Service: "+str(service.metadata_name)+\
        ", AmountOfActivePods: "+str(service.amountOfActivePods._get_value())+\
        ", Status: " + str(service.status._get_value()) +
        ", Spec_selector: "+str([str(x) for x in service.spec_selector._property_value])+\
        ", Pod_List: "+str([str(x) for x in service.podList._get_value()])+\
        ", IsSearched: ", str(service.isSearched._get_value()))


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
        " Spec_replicas: "+ str(deployment.spec_replicas._get_value()) +\
        " Namespace: " + str(deployment.metadata_namespace._get_value())+\
        " AmountOfActivePods: " + str(deployment.amountOfActivePods._get_value())+\
        " Status: " + str(deployment.status._get_value())+\
        " PodList: " + str([str(x) for x in deployment.podList._get_value()])+\
        " PriorityClassName: " + str(deployment.spec_template_spec_priorityClassName._property_value) + \
        " Searchable:" + str(deployment.searchable))
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
    print(list_of_objects_output)