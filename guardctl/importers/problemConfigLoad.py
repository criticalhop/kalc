import sys
import logging as log
from  guardctl.misc.status import * 

from poodle import * 
from guardctl.misc.const import *
from guardctl.model.object.k8s_classes import *
from guardctl.model.action.scheduler import * 
from guardctl.model.action.eviction import *
from guardctl.model.action.default_limits import *
from guardctl.model.action.goalActions import *
from guardctl.model.action.oom_kill import *
from guardctl.misc.problem import ProblemTemplate
from guardctl.importers.poodleGen import PoodleGen

import yaml
import os
import kubernetes

jsonFile = None
yamlFile = None
try:
    yamlFile = os.environ['YAMLFILE']
except:
    pass

try:
    jsonFile = os.environ['JSONFILE']
except:
    pass

class KubernetesYAMLLoad(ProblemTemplate):
    def __init__(self, path = "", coreV1_api_list_node=None, coreV1_api_list_pod_for_all_namespaces=None, coreV1_list_service_for_all_namespaces=None,shV1beta1_api_list_priority_class=None):
        super().__init__()
        self._path = path
        self.coreV1_api_list_node = coreV1_api_list_node
        self.coreV1_api_list_pod_for_all_namespaces = coreV1_api_list_pod_for_all_namespaces
        self.coreV1_list_service_for_all_namespaces = coreV1_list_service_for_all_namespaces
        self.shV1beta1_api_list_priority_class = shV1beta1_api_list_priority_class
        # print(self.shV1beta1_api_list_priority_class)

    def cloudQuery(self):
        kubernetes.config.load_kube_config()
        self.coreV1_api = kubernetes.client.CoreV1Api()

        self.shV1beta1_api = kubernetes.client.SchedulingV1beta1Api()
        kubernetes.config.load_kube_config()

    def loadAsDictFromFile(self):
        pass
    
    def loadNodeAsDictFromCloud(self, dumpFile=None):
        if self.coreV1_api_list_node != None:
            yamlStr = self.loadYAML(self.coreV1_api_list_node)
            nodes = yaml.safe_load(yamlStr)
        else:
            nodes = self.coreV1_api.list_node().to_dict()
        if dumpFile != None:
            with open(dumpFile, 'w') as outfile:
                yaml.dump(nodes, outfile, default_flow_style=False)
        return nodes

    def loadPodAsDictFromCloud(self, dumpFile=None):
        if self.coreV1_api_list_pod_for_all_namespaces != None:
            yamlStr = self.loadYAML(self.coreV1_api_list_pod_for_all_namespaces)
            pods = yaml.safe_load(yamlStr)
        else:
            pods = self.coreV1_api.list_pod_for_all_namespaces().to_dict()
        if dumpFile != None:
            with open(dumpFile, 'w') as outfile:
                yaml.dump(pods, outfile, default_flow_style=False)
        return pods

    def loadServiceAsDictFromCloud(self, dumpFile=None):
        if self.coreV1_list_service_for_all_namespaces != None:
            yamlStr = self.loadYAML(self.coreV1_list_service_for_all_namespaces)
            services = yaml.safe_load(yamlStr)
        else:
            services = self.coreV1_api.list_service_for_all_namespaces().to_dict()
        if dumpFile != None:
            with open(dumpFile, 'w') as outfile:
                yaml.dump(services, outfile, default_flow_style=False)
        return services

    def loadPriorityAsDictFromCloud(self, dumpFile=None):
        # print("dump file", self.shV1beta1_api_list_priority_class)
        if self.shV1beta1_api_list_priority_class != None:
            yamlStr = self.loadYAML(self.shV1beta1_api_list_priority_class)
            priorityList = yaml.safe_load(yamlStr)
            # print("priorytylist", priorityList)
        else:
            priorityList = self.shV1beta1_api.list_priority_class().to_dict()
        if dumpFile != None:
            with open(dumpFile, 'w') as outfile:
                yaml.dump(priorityList, outfile, default_flow_style=False)
        return priorityList

    def loadNodeFromCloud(self):
        nodeList = []
        kubeProxy = []
        nodes = self.loadNodeAsDictFromCloud()

        for n in nodes["items"]:
            nodeList.append(self._loadNodeFromDict(n))
        return nodeList, kubeProxy

    def _loadNodeFromDict(self, nodek):
        nodeTmp = self.addObject(Node(nodek['metadata']['name']))
        nodeTmp.cpuCapacity = PoodleGen.cpuConvert(None, nodek['status']['allocatable']['cpu'])
        nodeTmp.memCapacity = PoodleGen.memConverter(None, nodek['status']['allocatable']['memory'])
        nodeTmp.podAmount = int(nodek['status']['capacity']['pods'])

        #defaul values
        nodeTmp.state = STATE_NODE_ACTIVE 
        nodeTmp.status = STATUS_NODE_ACTIVE
#            nodeTmp.currentFormalCpuConsumption = amount of pods
#            nodeTmp.currentFormalMemConsumption = 
        nodeTmp.currentRealMemConsumption = 0
        nodeTmp.currentRealCpuConsumption = 0
        nodeTmp.AmountOfPodsOverwhelmingMemLimits = 0
        return nodeTmp

    def loadPriority(self):
        priorityList = self.loadPriorityAsDictFromCloud()
        priorityDict = {}
        # print(priorityList)
        for priorityItem in priorityList['items']:
            priorityDict[priorityItem['metadata']['name']] = priorityItem['value']
        return priorityDict

#call me only after loadNodeFromCloud
    def loadPodFromCloud(self):
        
        pods = self.loadPodAsDictFromCloud()
        for p in pods["items"]:
            self._loadPodFromDict(p)

    def _loadPodFromDict(self, podk):
        #log.debug(podk.metadata.name)
        #exit(0)
        podTmp = self.addObject(Pod(podk['metadata']['name']))
        #load label
        if 'app' in podk['metadata']['labels']:
            podTmp._label = podk['metadata']['labels']['app']
            if 'role' in  podk['metadata']['labels']:
                podTmp._label = podTmp._label + podk['metadata']['labels']['role']
            if 'tier' in  podk['metadata']['labels']:
                podTmp._label = podTmp._label + podk['metadata']['labels']['tier']
        
        #containerCOnfig
        сontainerConfigTmp = ContainerConfig()
        for serviceI in self.service:
            if serviceI._label == podTmp._label:
                сontainerConfigTmp.service = serviceI
        podTmp.podConfig = сontainerConfigTmp
        self.containerConfig.append(self.addObject(сontainerConfigTmp))

        if str(podk['status']['phase']) == "Running":
            sym = STATE_POD_PENDING
        elif str(podk['status']['phase']) == "Inactive":
            sym = STATE_POD_INACTIVE 
        elif str(podk['status']['phase']) == "Pending":
            sym = STATE_POD_PENDING
        elif str(podk['status']['phase']) == "Succeeded":
            sym = STATE_POD_SUCCEEDED
        else:
            raise NotImplementedError("Unsupported pod phase %s" % str(podk['status']['phase']))
        # log.debug("object is ", sym)

        podTmp.state = sym

        podCpuLimit = -1
        podCpuRequests = -1
        podMemLimit = -1
        podMemRequests = -1
        for container in podk['spec']['containers']:
            if 'limits' in container['resources'] and container['resources']['limits'] != None:
                if 'cpu' in container['resources']['limits']:
                    if podCpuLimit < 0 : podCpuLimit=0
                    podCpuLimit += PoodleGen.cpuConvert(None, container['resources']['limits']['cpu'])
                if 'memory' in container['resources']['limits']:
                    if podMemLimit < 0 : podMemLimit=0
                    podMemLimit += PoodleGen.memConverter(None, container['resources']['limits']['memory'])
            if 'requests' in container['resources'] and container['resources']['requests'] != None:
                if 'cpu' in container['resources']['requests']:
                    if podCpuRequests < 0 : podCpuRequests=0
                    podCpuRequests += PoodleGen.cpuConvert(None, container['resources']['requests']['cpu'])
                if 'memory' in container['resources']['requests']:
                    if podMemRequests < 0 : podMemRequests=0
                    podMemRequests += PoodleGen.memConverter(None, container['resources']['requests']['memory'])
            # log.debug("container resources limit cpu {cpu}m  mem {mem}Mi".format(cpu=podCpuLimit, mem=podMemLimit))
            # log.debug("container resources Requests cpu {cpu}m  mem {mem}Mi".format(cpu=podCpuRequests, mem=podMemRequests))
        if podCpuRequests < 0:
            podTmp.requestedCpu = -1
        else:
            podTmp.requestedCpu = podCpuRequests
        if podMemRequests < 0:
            podTmp.requestedMem = -1
        else:
            podTmp.requestedMem = podMemRequests
        
        
        #default values
        podTmp.currentRealCpuConsumption = 0
        podTmp.currentRealMemConsumption = 0
        podTmp.status = STATUS_POD_ATCONFIG 
        podTmp.podNotOverwhelmingLimits = True
        podTmp.realInitialMemConsumption = 1
        podTmp.realInitialCpuConsumption = 1
        podTmp.type = TYPE_PERSISTENT
        podTmp.memLimit =  3
        podTmp.cpuLimit =  3
        
        podTmp.priority =  1
        
        #fill pod with corresponding kube-proxy
        for idx, nodeTmp in enumerate(self.node):
            if nodeTmp.value == podk['spec']['node_name']:
                #self.kubeProxy[idx].selectionedPod.add(podTmp)
                podTmp.atNode = nodeTmp
        
        podTmp.status
        
        log.debug("pod name {0} status {1} ".format(podk['metadata']['name'], podk['status']['phase']))
        #append pod to pod's list
        self.pod.append(podTmp)
        return podTmp

    def loadServiceFromCloud(self):
        services = self.loadServiceAsDictFromCloud()
        pods = self.loadPodAsDictFromCloud()

        for servicek in services['items']:
            serviceTmp = self.addObject(Service())
                    #count active pods (need for services)
            amountOfActivePods = 0
            for podk in pods['items']:
                owner_find = 0
                ##not working yet!! poodle non type
            #    for own_item in podk.metadata.owner_references :
            #        if own_item.uid == servicek.metadata.uid :
            #            owner_find = 1
            #            break
            #    if owner_find == 1 and str(podk.status.phase) == 'Running' :
            #        amountOfActivePods += 1
            serviceTmp.amountOfActivePods = amountOfActivePods
            #load label
            if 'app' in servicek['metadata']['labels']:
                serviceTmp._label = servicek['metadata']['labels']['app']
                if 'role' in servicek['metadata']['labels']:
                    serviceTmp._label = serviceTmp._label + servicek['metadata']['labels']['role']
                if 'tier' in servicek['metadata']['labels']:
                    serviceTmp._label = serviceTmp._label + servicek['metadata']['labels']['tier']
            
            # todo load LoadBalancer type
            # if servicek.spec.type == 'LoadBalancer':
  
            #     newLb = self.addObject(Loadbalancer())
            #     newLb._ipAndName = servicek.status.load_balancer.ingress # .ip - ip addr  .name - domain
            #     newLb.selectionedService.add(serviceTmp)
            #     self.loadbalancer.append(newLb)

            self.service.append(serviceTmp)


    def loadService(self, yamlStr, priorityDict):
        for y in yaml.safe_load_all(yamlStr):
            # log.debug(y)
        #      log.debug(y['metadata']['name'])
            if y['kind'] == 'Service':
                # log.debug("service {0}".format(y['metadata']['name']))
                l = y['metadata']['labels']
                label = None
                if 'app' in l:
                    label = l['app']
                    if 'role' in l:
                        label = label + l['role']
                    if 'tier' in l:
                        label = label + l['tier']
                serviceTmp = self.addObject(Service(label))
                self.service.append(serviceTmp)
                serviceTmp._label = label
                serviceTmp._replicas = 1 # can be replaced in future
                
                #Deployment controller stub in according to  https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
                for d in yaml.safe_load_all(yamlStr):
#                    log.debug("{0} {1}".format(d['kind'], d['metadata']['name']))
                    if d['kind'] == 'Deployment':
                        l = d['spec']['selector']['matchLabels']
                        dlabel = None
                        if 'app' in l:
                            dlabel = l['app']
                            if 'role' in l:
                                dlabel = dlabel + l['role']
                            if 'tier' in l:
                                dlabel = dlabel + l['tier']
                        #containerConfig
                        сontainerConfigTmp = ContainerConfig(label)
                        сontainerConfigTmp.service = serviceTmp        
                        self.containerConfig.append(self.addObject(сontainerConfigTmp))
                        
                        podCpuLimit = -1
                        podCpuRequests = -1
                        podMemLimit = -1
                        podMemRequests = -1
                        # sum cpu and mem of all containers
                        for c in d['spec']['template']['spec']['containers']:
                            if 'limits' in c['resources'] and c['resources']['limits'] != None:
                                if 'cpu' in c['resources']['limits']:
                                    if podCpuLimit < 0 : podCpuLimit=0
                                    podCpuLimit += PoodleGen.cpuConvert(None, c['resources']['limits']['cpu'])
                                if 'memory' in c['resources']['limits']:
                                    if podMemLimit < 0 : podMemLimit=0
                                    podMemLimit += PoodleGen.memConverter(None, c['resources']['limits']['memory'])
                            if 'requests' in c['resources'] and c['resources']['requests'] != None:
                                if 'cpu' in c['resources']['requests']:
                                    if podCpuRequests < 0 : podCpuRequests=0
                                    podCpuRequests += PoodleGen.cpuConvert(None, c['resources']['requests']['cpu'])
                                if 'memory' in c['resources']['requests']:
                                    if podMemRequests < 0 : podMemRequests=0
                                    podMemRequests += PoodleGen.memConverter(None, c['resources']['requests']['memory'])
                        
                        # log.debug("container resources limit cpu {cpu}m  mem {mem}Mi".format(cpu=podCpuLimit, mem=podMemLimit))
                        # log.debug("container resources Requests cpu {cpu}m  mem {mem}Mi".format(cpu=podCpuRequests, mem=podMemRequests))

                        priorityClassName = 0        
                        if 'priorityClassName' in d['spec']['template']['spec']:
                            priorityClassName = int(priorityDict[d['spec']['template']['spec']['priorityClassName']])

                        if label != None and label == dlabel:
                                log.debug("Deployment {0}".format(d['metadata']['name']))
                                if 'replicas' in d['spec']:
                                    serviceTmp._replicas = int(d['spec']['replicas'])
                                for i in range(serviceTmp._replicas):
                                    podTmp = self.addObject(Pod(label + str(i)))
                                    podTmp.podConfig = сontainerConfigTmp
                                    podTmp.priority = priorityClassName
                                    podTmp.cpuRequest = podCpuRequests
                                    podTmp.memRequest = podMemRequests
                                    podTmp.cpuLimit = podCpuLimit
                                    podTmp.memLimit = podMemLimit
                                    podTmp.status =  STATUS_POD_PENDING
                                    self.pod.append(podTmp)

#call only after loadNodeFromCloud
    def loadDaemonSet(self, yamlStr, priorityDict):
        for y in yaml.safe_load_all(yamlStr):
            if y['kind'] == 'DaemonSet':
                # log.debug("service {0}".format(y['metadata']['name']))
                l = y['metadata']['labels']
                label = None
                if 'k8s-app' in l:
                    label = l['k8s-app']
                    if 'role' in l:
                        label = label + l['role']
                    if 'tier' in l:
                        label = label + l['tier']

                podCpuLimit = -1
                podCpuRequests = -1
                podMemLimit = -1
                podMemRequests = -1
                # sum cpu and mem of all containers
                for c in y['spec']['template']['spec']['containers']:
                    if 'limits' in c['resources'] and c['resources']['limits'] != None:
                        if 'cpu' in c['resources']['limits']:
                            if podCpuLimit < 0 : podCpuLimit=0
                            podCpuLimit += PoodleGen.cpuConvert(None, c['resources']['limits']['cpu'])
                        if 'memory' in c['resources']['limits']:
                            if podMemLimit < 0 : podMemLimit=0
                            podMemLimit += PoodleGen.memConverter(None, c['resources']['limits']['memory'])
                    if 'requests' in c['resources'] and c['resources']['requests'] != None:
                        if 'cpu' in c['resources']['requests']:
                            if podCpuRequests < 0 : podCpuRequests=0
                            podCpuRequests += PoodleGen.cpuConvert(None, c['resources']['requests']['cpu'])
                        if 'memory' in c['resources']['requests']:
                            if podMemRequests < 0 : podMemRequests=0
                            podMemRequests += PoodleGen.memConverter(None, c['resources']['requests']['memory'])
                        
                priorityClassName = 0      
                if 'priorityClassName' in y['spec']['template']['spec'] :
                    priorityClassName = int(priorityDict[y['spec']['template']['spec']['priorityClassName']])
                daemonSetTmp = self.addObject(DaemonSet(label))
                self.daemonSet.append(daemonSetTmp)
                daemonSetTmp._label = label
                сontainerConfigTmp = ContainerConfig(label)
                сontainerConfigTmp.daemonSet = daemonSetTmp  
                #Deployment controller stub in according to  https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
                for c in y['spec']['template']['spec']['containers'] : 
#                   log.debug("{0} {1}".format(d['kind'], d['metadata']['name']))
                    log.debug("daemonSetTmp {0}".format(c['name']))
                    for myNode in self.node:
                        podTmp = self.addObject(Pod(label + str(i)))
                        podTmp.podConfig = сontainerConfigTmp
                        podTmp.priority = priorityClassName
                        podTmp.cpuRequest = podCpuRequests
                        podTmp.memRequest = podMemRequests
                        podTmp.cpuLimit = podCpuLimit
                        podTmp.memLimit = podMemLimit
                        podTmp.status = STATUS_POD_PENDING
                        podTmp.atNode = myNode
                        self.pod.append(podTmp)
    
    def loadYAML(self, path):
        yamlStr = ""
        with open(path, 'r') as stream:
            log.debug("open yaml")
            yamlStr = stream.read()
        return yamlStr

    def superProblem(self):
        super().problem()

        # dumpList = [daemonYAMLPath, './examples/currentCloud/coreV1_api_list_node.yaml', './examples/currentCloud/coreV1_api_list_pod_for_all_namespaces.yaml',  './examples/currentCloud/coreV1_list_service_for_all_namespaces.yaml','./examples/currentCloud/shV1beta1_api_list_priority_class.yaml']
    def problem(self):
        
        super().problem()

        yamlStr = self.loadYAML(self._path)

        priorityDict = self.loadPriority()
        self.loadNodeFromCloud()
        self.loadPodFromCloud()
        self.loadServiceAsDictFromCloud()
        self.loadDaemonSet(yamlStr, priorityDict)



