from collections import defaultdict
import yaml
import os
import string
import random
import json
from typing import Dict, List
from dataclasses import dataclass, asdict
from typing import Set
from logzero import logger
TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONET = "./tests/daemonset_eviction/daemonset_create.yaml"

from poodle import *


class Type(Object):
    def __str__(self): return str(self._get_value())

class Status(Object):
    def __str__(self): return str(self._get_value())

class StatusPod(Object):
    def __str__(self): return str(self._get_value())

class StatusNode(Object):
    def __str__(self): return str(self._get_value())

class StatusReq(Object):
    def __str__(self): return str(self._get_value())

class StatusSched(Object):
    def __str__(self): return str(self._get_value())
    
class StatusServ(Object):
    def __str__(self): return str(self._get_value())

class StatusDepl(Object):
    def __str__(self): return str(self._get_value())
    
class StatusLim(Object):
    pass

class Label(Object):
    def __str__(self):
        return str(self._get_value())

class TypePolicy(Object):
    pass

class TypeServ(Object):
    pass


STATUS_POD = {
    "Running" : StatusPod("Running"),
    "Pending" : StatusPod("Pending"),
    "Killing" : StatusPod("Killing"),
    "Failed" : StatusPod("Failed"),
    "Succeeded" : StatusPod("Succeeded")
}

# STATUS_LIM = {
#     "Limit Met" : StatusLim("Limit is met"),
#     "Limit Exceeded" : StatusLim("Limit is exceded")
# }

STATUS_NODE = {
    "Active" : StatusNode("Active"),
    "Inactive" : StatusNode("Inactive")
}

STATUS_SCHED = {
    "Changed" : StatusSched("Changed"),
    "Clean" :  StatusSched("Clean")
}

STATUS_SERV = {
    "Interrupted" : StatusServ("Interrupted"),
    "Pending" : StatusServ("Pending"),
    "Started" : StatusServ("Started")
}
STATUS_DEPL = {
    "Interrupted" : StatusDepl("Interrupted"),
    "Pending" : StatusDepl("Pending"),
    "Started" : StatusDepl("Started")
}
POLICY = {
    "PreemptLowerPriority" : TypePolicy("PreemptLowerPriority"),
    "Never" : TypePolicy("Never")
}


class HasLimitsRequests(Object):
    """A mixin class to implement Limts/Requests loading and initialiaztion"""
    memRequest: int
    cpuRequest: int
    memLimit: int
    memLimitsStatus: StatusLim
    """Status to set if the limit is reached"""
    cpuLimit: int
    cpuLimitsStatus: StatusLim
    """Status to set if the limit is reached"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cpuLimit = -1
        self.memLimit = -1
        self.cpuRequest = -1
        self.memRequest = -1
        # self.memLimitsStatus = STATUS_LIM["Limit Met"]
        # self.cpuLimitsStatus = STATUS_LIM["Limit Met"]

from poodle import schedule, xschedule
from poodle.schedule import SchedulingError

class HasLabel(Object):
    metadata_labels: Set[Label]
    metadata_name: str
class Controller(HasLabel):
    "Kubernetes controller base class"
    pass
class ReplicaSet(Controller, HasLimitsRequests):
    metadata_name: str
    metadata_namespace: str
    apiVersion: str
    metadata_ownerReferences__kind: str
    metadata_ownerReferences__name: str
   
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        #TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
        self.hash = "superhash"


    def hook_after_create(self, object_space):
        pass

    def hook_after_load(self, object_space):
        print("replicaset kind {1} name {0}".format(self.metadata_ownerReferences__name, self.metadata_ownerReferences__kind))
class Service(HasLabel):
    spec_selector: Set[Label]
    lastPod: "Pod"
    atNode: "Node"
    amountOfActivePods: int
    status: StatusServ
    metadata_name: str
    searchable: bool
    
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.amountOfActivePods = 0
        self.status = STATUS_SERV["Pending"]
        self.searchable = True
 

    # def __repr__(self):
    #     return 'Servicename : ' + str(self._get_value()) 

Service.SERVICE_NULL = Service("NULL")

class ProblemTemplate:
    def __init__(self, objectList=None):
        if objectList is None: self.objectList = []
        else: self.objectList = objectList
        self.plan = None
        self.pod = []
        self.node = []
        self.kubeProxy = []
        self.loadbalancer = []
        self.service = []
        self.controller = []
        self.request = []
        self.containerConfig = []
        self.priorityDict = {}
    
    def problem(self):
        pass
        
    def addObject(self, obj):
        self.objectList.append(obj)
        return obj

    # fill object with corresponding list (list instance in lower case)
    def fillObjectLists(self):
        requiredObject = ['Pod', "Node", "Service", "LoadBalancer", "DaemonSet", "Deployment"]
        for obj in self.objectList:
            if obj.__class__.__name__ in requiredObject:
                try:
                    getattr(self, obj.__class__.__name__.lower()).append(obj)
                except:
                    pass

    def run(self, timeout=30, sessionName=None, schedule=schedule, raise_=False):
        if not sessionName: sessionName = self.__class__.__name__
        self.problem()
        self_methods = [getattr(self,m) for m in dir(self) if callable(getattr(self,m)) and hasattr(getattr(self, m), "_planned")]
        model_methods = []
        methods_scanned = set()
        for obj in self.objectList:
            if not obj.__class__.__name__ in methods_scanned:
                methods_scanned.add(obj.__class__.__name__)
                for m in dir(obj):
                    if callable(getattr(obj, m)) and hasattr(getattr(obj, m), "_planned"):
                        model_methods.append(getattr(obj, m))
        try:
            self.plan = schedule(
                methods=self_methods + list(model_methods), 
                space=list(self.__dict__.values())+self.objectList,
                goal=lambda:(self.goal()),
                timeout=timeout,
                sessionName=sessionName
                #exit=self.exit
            )
        except SchedulingError:
            if raise_:
                raise SchedulingError("Can't solve")
            else:
                pass
    
    def xrun(self, timeout=30, sessionName=None):
        "Run and execute plan"
        self.run(timeout, sessionName, schedule=xschedule, raise_=True)

    def goal(self):
        pass


def cpuConvertToAbstractProblem(cpuParot):
    #log.debug("cpuParot", cpuParot)
    cpu = 0
    if cpuParot[len(cpuParot)-1] == 'm':
        cpu = int(cpuParot[:-1])
    else:
        cpu = int(cpuParot)*1000
    # log.debug("cpuParot ", cpuParot, " ret ", cpuAdd)
    cpu = int(cpu / 100)
    if cpu == 0:
        cpu = 1
    return int(cpu)

def memConvertToAbstractProblem(mem):
    ret = 0
    if mem[len(mem)-2:] == 'Gi':
        ret = int(mem[:-2])*1000
    elif mem[len(mem)-2:] == 'Mi':
        ret = int(mem[:-2])
    elif mem[len(mem)-2:] == 'Ki':
        ret = int(int(mem[:-2])/1000)
    else:
        ret = int(int(mem)/1000000)
    ret = int(ret / 250)
    if ret == 0:
        ret = 1
    return int(ret)
class Node(HasLabel):
    # k8s attributes
    metadata_ownerReferences__name: str
    metadata_name: str
    spec_priorityClassName: str
    labels: Set[Label]
    cpuCapacity: int
    memCapacity: int
    currentFormalCpuConsumption: int
    currentFormalMemConsumption: int
    currentRealMemConsumption: int
    currentRealCpuConsumption: int
    AmountOfPodsOverwhelmingMemLimits: int
    podAmount: int
    isNull: bool
    status: StatusNode

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.AmountOfPodsOverwhelmingMemLimits = 0
        self.currentFormalCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentRealCpuConsumption = 0
        self.currentRealMemConsumption = 0
        self.cpuCapacity = 0
        self.memCapacity = 0
        self.isNull = False
    
    @property
    def status_allocatable_memory(self):
        pass
    @status_allocatable_memory.setter
    def status_allocatable_memory(self, value):
        self.memCapacity = memConvertToAbstractProblem(value)

    @property
    def status_allocatable_cpu(self):
        pass
    @status_allocatable_cpu.setter
    def status_allocatable_cpu(self, value):
        self.cpuCapacity = cpuConvertToAbstractProblem(value)

    def __str__(self):
        if self.metadata_name._get_value() is None:
            return "<unnamed node>"
        return str(self.metadata_name)
    # def __repr__(self):
    #     return 'Nodename : ' + str(self._get_value()) 


Node.NODE_NULL = Node("NULL")
Node.NODE_NULL.isNull = True

from poodle import Object
from guardctl.model.system.primitives import TypePolicy
from guardctl.misc.const import *


class PriorityClass(Object):
    metadata_name: str

    priority: int
    preemptionPolicy: TypePolicy

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.preemptionPolicy = POLICY["PreemptLowerPriority"]
        self.priority = 0

    @property
    def value(self):
        pass
    @value.setter 
    def value(self, value):
        if value > 1000: value = 1000
        self.priority = value

zeroPriorityClass = PriorityClass("ZERO")
zeroPriorityClass.metadata_name = "Normal-zero"



class Pod(HasLabel, HasLimitsRequests):
    # k8s attributes
    metadata_ownerReferences__name: str
    spec_priorityClassName: str
    metadata_name: str

    # internal model attributes
    ownerReferences: Controller
    TARGET_SERVICE_NULL = Service.SERVICE_NULL
    targetService: Service
    atNode: "Node"
    toNode: "Node"
    realInitialMemConsumption: int
    realInitialCpuConsumption: int
    currentRealCpuConsumption: int
    currentRealMemConsumption: int
    spec_nodeName: str
    priorityClass: PriorityClass
    status: StatusPod
    isNull: bool
    # amountOfActiveRequests: int # For requests

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = 0
        self.spec_priorityClassName = "KUBECTL-VAL-NONE"
        self.priorityClass = zeroPriorityClass
        # self.targetService = self.TARGET_SERVICE_NULL
        self.toNode = Node.NODE_NULL
        self.atNode = Node.NODE_NULL
        self.status = STATUS_POD["Pending"]
        self.isNull = True
        self.realInitialMemConsumption = 0
        self.realInitialCpuConsumption = 0
        self.currentFormalMemConsumption = 0
        self.currentFormalCpuConsumption = 0
        # self.amountOfActiveRequests = 0 # For Requests

    def hook_after_load(self, object_space, _ignore_orphan=False):
        pass

    @property
    def spec_containers__resources_requests_cpu(self):
        pass
    @spec_containers__resources_requests_cpu.setter
    def spec_containers__resources_requests_cpu(self, res):
        if self.cpuRequest == -1: self.cpuRequest = 0
        self.cpuRequest += cpuConvertToAbstractProblem(res)

    @property
    def spec_containers__resources_requests_memory(self):
        pass
    @spec_containers__resources_requests_memory.setter
    def spec_containers__resources_requests_memory(self, res):
        if self.memRequest == -1: self.memRequest = 0
        self.memRequest += memConvertToAbstractProblem(res)

    @property
    def status_phase(self):
        pass
    @status_phase.setter
    def status_phase(self, res):
        self.status = STATUS_POD[res]

    def __str__(self): return str(self.metadata_name)

ALL_STATE = None
class Scheduler(Object):
    queueLength: int
    status: StatusSched
    podQueue: Set["Pod"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queueLength = 0

class GlobalVar(Object):
    is_service_interrupted: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_service_interrupted = False

kinds_collection = {}

try:
    from six import string_types, iteritems
except ImportError:
    string_types = (str, ) if str is bytes else (str, bytes)
    iteritems = lambda mapping: getattr(mapping, 'iteritems', mapping.items)()
    
import logzero
logzero.logfile("./test.log", disableStderrLogger=False)

def objwalk(obj, path=(), memo=None):
    if memo is None:
        memo = set()
    if isinstance(obj, Mapping):
        if id(obj) not in memo:
            memo.add(id(obj)) 
            for key, value in iteritems(obj):
                for child in objwalk(value, path + (key,), memo):
                    yield child
    elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, string_types):
        if id(obj) not in memo:
            memo.add(id(obj))
            for index, value in enumerate(obj):
                for child in objwalk(value, path + (index,), memo):
                    yield child
    else:
        yield path, obj
class _LabelFactory:
    def __init__(self):
        self.labels = {}
    def get(self, name, value):
        lbl = f"{name}:{value}"
        if not lbl in self.labels:
            self.labels[lbl] = Label(lbl)
        return self.labels[lbl]

labelFactory = _LabelFactory()

def find_property(obj, p):
    path = p[0]
    val = p[1]
    if len(path) == 1:
        if hasattr(obj, path[0]):
            return path[0], val
    
    for i in range(len(path), 1, -1):
        try_path = path[:i]
        spath = "_".join([x if isinstance(x, str) else "" for x in try_path])
        # print("Trying ", spath)
        if hasattr(obj, spath) and i==len(path):
            # print("FOUND1")
            return spath, val
        elif hasattr(obj, spath) and i==len(path)-1:
            # print("FOUND2")
            return spath, {path[-1]: val}
    return None, None

def k8s_to_domain_object(obj):
    try_int = False
    try:
        int(obj)
        try_int = True
    except:
        pass
    if isinstance(obj, int):
        return obj
    elif isinstance(obj, dict) and len(obj) == 1:
        k,v=list(obj.items())[0]
        return labelFactory.get(k,v)
    elif isinstance(obj, str) and obj[0] in string.digits+"-" and not obj[-1] in string.digits:
        # pass on, probably someone will take care
        return obj
    elif isinstance(obj, str) and try_int:
        return int(obj)
    elif isinstance(obj, str) and not obj[0] in string.digits+"-":
        return obj
    else:
        raise ValueError("Value type not suported: %s" % repr(obj))

class KubernetesCluster:
    def __init__(self):
        self.dict_states = defaultdict(list)
        self._reset()

    def _reset(self):
        "Reset object states and require a rebuild with _bulid_state"
        self.state_objects = [Scheduler(), GlobalVar()]

    def load_dir(self, dir_path):
        for root, dirs, files in os.walk(dir_path):
            for fn in files:
                self.load(open(os.path.join(root, fn)).read())

    def load(self, str_, create=False):
        for doc in yaml.load_all(str_, Loader=yaml.FullLoader):
            if "items" in doc:
                for item in doc["items"]: self.load_item(item, create)
            else: self.load_item(doc, create)

    def load_item(self, item, create=False):
        assert isinstance(item, dict), item
        item["__created"] = create
        self.dict_states[item["kind"]].append(item)

    def _build_item(self, item):
        obj = kinds_collection[item["kind"]]()
        create = item["__created"]
        obj.kubeguard_created = create # special property to distinguish "created"
        for prop in objwalk(item):
            p, val = find_property(obj, prop)
            if p is None: continue
            val = k8s_to_domain_object(val)
            if isinstance(getattr(obj, p), Relation):
                getattr(obj, p).add(val)
            elif isinstance(getattr(obj, p), Property):
                setattr(obj, p, val)
            else:
                # means has setter
                setattr(obj, p, val)
        if create and hasattr(obj, "hook_after_create"):
            obj.hook_after_create(self.state_objects)
        if not create and hasattr(obj, "hook_after_load"):
            obj.hook_after_load(self.state_objects)
        self.state_objects.append(obj)

    def _build_state(self):
        KINDS_LOAD_ORDER = ["PriorityClass", "Service", "Node", "Pod", "ReplicaSet"]
        collected = self.dict_states.copy()
        for k in KINDS_LOAD_ORDER:
            if not k in collected: continue
            for item in collected[k]:
                self._build_item(item)
            del collected[k]
        for k,v in collected.items():
            for item in v:
                self._build_item(item)

    def create_resource(self, res: str):
        self.load(res, create=True)

    def fetch_state_default(self):
        "Fetch state from cluster using default method"
        raise NotImplementedError()

    def run(self):
        if len(self.state_objects) < 3: self._build_state()
        k = K8ServiceInterruptSearch(self.state_objects)
        k.run()
        self.plan = k.plan
        return self.plan
 
def print_objects(objectList):
    print("=====>")
    pod_loaded_list = filter(lambda x: isinstance(x, "Pod"), objectList)
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
class Deployment(Controller, HasLimitsRequests):
    spec_replicas: int
    metadata_name: str
    metadata_namespace: str
    apiVersion: str
    lastPod: "Pod"
    amountOfActivePods: int
    status: StatusDepl
    podList: Set["Pod"]
    spec_template_spec_priorityClassName: str
    hash: str
    searchable: bool

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        #TODO fill pod-template-hash with https://github.com/kubernetes/kubernetes/blob/0541d0bb79537431421774465721f33fd3b053bc/pkg/controller/controller_utils.go#L1024
        self.hash = ''.join(random.choice("0123456789abcdef") for i in range(8))

    
class Scenario:
    def __init__(self, plan=None):
        self.steps = []
        if plan:
            for a in plan:
                self.step(a())
    def step(self, step):
        self.steps.append(step)
    def asjson(self):
        return json.dumps([asdict(x) for x in self.steps])
    def asyaml(self):
        if not self.steps:
            return "# Empty scenario"
        probability = 1
        for s in self.steps:
            probability = probability * s.probability
        return yaml.dump({
                "probability": probability,
                "steps": [dict_rename(asdict(x),"name","actionName") for x in self.steps]
                })

    def hook_after_create(self, object_space):
        deployments = filter(lambda x: isinstance(x, Deployment), object_space)
        for deploymentController in deployments:
            if str(deploymentController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): deployments.{0} \"{1}\" already exists".format(str(self.apiVersion).split("/")[0], self.metadata_name)
                logger.error(message)
                raise AssertionError(message)
        self.create_pods(object_space, self.spec_replicas._get_value())
    
    def dict_rename(d, nfrom, nto):
        d[nto] = d[nfrom]
        del d[nfrom]
        return d

    def create_pods(self, object_space, replicas, start_from=0):
        scheduler = next(filter(lambda x: isinstance(x, Scheduler), object_space))
        for replicaNum in range(replicas):
            new_pod = Pod()
            hash1 = self.hash
            hash2 = str(replicaNum+start_from)
            new_pod.metadata_name = "{0}-{1}-{2}".format(str(self.metadata_name),hash1,hash2)
            for label in self.spec_selector_matchLabels._get_value():
                if not (label in  new_pod.metadata_labels._get_value()):
                    new_pod.metadata_labels.add(label)
            new_pod.metadata_labels.add(Label("pod-template-hash:{0}".format(hash1)))
            new_pod.cpuRequest = self.cpuRequest
            new_pod.memRequest = self.memRequest
            new_pod.cpuLimit = self.cpuLimit
            new_pod.memLimit = self.memLimit
            new_pod.status = STATUS_POD["Pending"]
            new_pod.hook_after_load(object_space, _ignore_orphan=True) # for service<>pod link
            try:
                new_pod.priorityClass = \
                    next(filter(\
                        lambda x: \
                            isinstance(x, PriorityClass) and \
                            str(x.metadata_name) == str(self.spec_template_spec_priorityClassName),\
                        object_space))
            except StopIteration:
                logger.warning("Could not reference priority class")
            self.podList.add(new_pod)
            self.check_pod(new_pod, object_space)
            object_space.append(new_pod)
            scheduler.podQueue.add(new_pod)
            scheduler.queueLength += 1
            scheduler.status = STATUS_SCHED["Changed"]

def objRemoveByName(objList, metadata_name):
    br = True
    while br:
        br = False
        for obj in objList:
            if obj.metadata_name._get_value() == metadata_name :
                objList.remove(obj)
                br = True
                break

    def hook_after_load(self, object_space):
        deployments = filter(lambda x: isinstance(x, Deployment), object_space)
        for deploymentController in deployments:
            if deploymentController != self and str(deploymentController.metadata_name) == str(self.metadata_name):
                message = "Error from server (AlreadyExists): deployments.{0} \"{1}\" already exists".format(str(self.apiVersion).split("/")[0], self.metadata_name)
                logger.error(message)
                raise AssertionError(message)
        pods = filter(lambda x: isinstance(x, Pod), object_space)
        replicasets = filter(lambda x: isinstance(x, ReplicaSet), object_space)
        #look for ReplicaSet with corresonding owner reference
        for replicaset in replicasets:
            br=False
            if replicaset.metadata_ownerReferences__name == self.metadata_name:
                for pod_template_hash in list(replicaset.metadata_labels._get_value()):
                    if str(pod_template_hash).split(":")[0] == "pod-template-hash":
                        self.hash = str(pod_template_hash).split(":")[1]
                        br = True
                        break
            if br: break

        for pod in pods:
            br = False
            # look for right pod-template-hash
            for pod_template_hash in list(pod.metadata_labels._get_value()):
                if str(pod_template_hash).split(":")[0] == "pod-template-hash" and str(pod_template_hash).split(":")[1] == self.hash :
                    self.podList.add(pod)
                    self.check_pod(pod, object_space)

    def hook_scale_before_create(self, object_space, new_replicas):
        self.spec_replicas = new_replicas

    def hook_after_apply(self, object_space):
        deployments = filter(lambda x: isinstance(x, Deployment), object_space)
        old_deployment = self
        for deploymentController in deployments:
            if deploymentController != self and str(deploymentController.metadata_name) == str(self.metadata_name):
                old_deployment = deploymentController
                break
        # if old DEployment not found
        if old_deployment == self:
            self.hook_after_create(object_space)
        else:
            self.podList = old_deployment.podList # copy pods
            self.hook_scale_after_load(object_space, old_deployment.spec_replicas._get_value()) # extend or trimm pods
            object_space.remove(old_deployment) # delete old Deployment

    #Call me only atfter loading this Controller
    def hook_scale_after_load(self, object_space, old_replicas):
        diff_replicas = self.spec_replicas._get_value() - old_replicas
        if diff_replicas == 0:
            logger.warning("Nothing to scale. You try to scale deployment {0} for the same replicas value {1}".format(self.metadata_name, self.spec_replicas))
        if diff_replicas < 0:
            #remove pods
            for _ in range(diff_replicas * -1):
                pod = self.podList._get_value().pop(-1)
                object_space.remove(pod)
                objRemoveByName(self.podList._get_value(), pod.metadata_name)
        if diff_replicas > 0:
            self.create_pods(object_space, diff_replicas, self.spec_replicas._get_value())

    def check_pod(self, new_pod, object_space):
        for pod in filter(lambda x: isinstance(x, Pod), object_space):
            pod1 = [x for x in list(pod.metadata_labels._get_value()) if str(x).split(":")[0] != "pod-template-hash"]
            pod2 = [x for x in list(new_pod.metadata_labels._get_value()) if str(x).split(":")[0] != "pod-template-hash"]
            if set(pod1) == set(pod2):
                logger.warning("Pods have the same label")

def test_anyservice_interrupted_fromfiles():
    k = KubernetesCluster()
    @planned
    def KillPod_IF_service_notnull_deployment_notnull(podBeingKilled : "Pod",
            nodeWithPod : Node ,
            amountOfActivePodsPrev: int,
            deployment_of_pod: "Deployment"
         ):
        assert podBeingKilled in deployment_of_pod.podList
        deployment_of_pod.amountOfActivePods -= 1

    p = AnyServiceInterrupted(k.state_objects)
    p.KillPod_IF_service_notnull_deployment_notnull = KillPod_IF_service_notnull_deployment_notnull

    # print_objects(k.state_objects)
    p.run(timeout=360, sessionName="test_anyservice_interrupted_fromfiles")
    if not p.plan:
        raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())


class KubernetesModel(ProblemTemplate):
    def problem(self):
        self.scheduler = next(filter(lambda x: isinstance(x, Scheduler), self.objectList))
        self.globalVar = next(filter(lambda x: isinstance(x, GlobalVar), self.objectList))

class K8ServiceInterruptSearch(KubernetesModel):
    pass
class AnyServiceInterrupted(K8ServiceInterruptSearch):

    goal = lambda self: self.globalVar.is_service_interrupted == True and \
            self.scheduler.status == STATUS_SCHED["Clean"]