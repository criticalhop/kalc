import sys
import logging as log

from poodle import * 
from guardctl.model.object.k8s_classes import *
from guardctl.model.problem.problemTemplate import *
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

class KubernitesYAMLLoad(ProblemTemplate):
    name = "Kubernites YAML Loader"
    _path = ""
    
   # 
    def __init__(self, path = ""):
        super().__init__()
        self._path = path

    def loadNodeFromCloud(self):
        nodeList = []
        kubeProxy = []
        config.load_kube_config()
        cj_api = client.CoreV1Api()
        nodes = cj_api.list_node()

        for nodek in nodes.items:
            nodeTmp = self.addObject(Node(nodek.metadata.name))
            nodeTmp.cpuCapacity = PoodleGen.cpuConvert(None, nodek.status.allocatable['cpu'])
            nodeTmp.memCapacity = PoodleGen.memConverter(None, nodek.status.allocatable['memory'])
            nodeTmp.podAmount = int(nodek.status.capacity['pods'])

            kubeProxyTmp = self.addObject(Kubeproxy())
            kubeProxyTmp.atNode = nodeTmp
            kubeProxyTmp.mode = self.constSymbol['modeUsermode']
            
            #for .selectionedPod.add look for "fill pod with corresponding kube-proxy" in pod iterate section

            #append Node and Proxy to node's and Proxy's list (access by self.node[node_num])
            kubeProxy.append(kubeProxyTmp)

            #defaul values
            nodeTmp.state = self.constSymbol['stateNodeActive']
            nodeTmp.status = self.constSymbol['statusNodeActive']
#            nodeTmp.currentFormalCpuConsumption = amount of pods
#            nodeTmp.currentFormalMemConsumption = 
            nodeTmp.currentRealMemConsumption = 0
            nodeTmp.currentRealCpuConsumption = 0
            nodeTmp.AmountOfPodsOverwhelmingMemLimits = 0

            nodeList.append(nodeTmp)

        return nodeList, kubeProxy

    def loadPriority(self):
        kubernetes.config.load_kube_config()
        sh_api = kubernetes.client.SchedulingV1beta1Api()

        priorityList = sh_api.list_priority_class()
        priorityDict = {}
        for priorityItem in priorityList.items:
            priorityDict[priorityItem.metadata.name] = priorityItem.value
        return priorityDict

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
                                    podTmp.status = self.constSymbol["statusPodPending"]
                                    self.pod.append(podTmp)

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
                    if 'replicas' in y['spec']['template']['spec']:
                        daemonSetTmp._replicas = int(y['spec']['template']['spec']['replicas'])
                    else:  
                        daemonSetTmp._replicas = 1
                    for i in range(daemonSetTmp._replicas):
                        podTmp = self.addObject(Pod(label + str(i)))
                        podTmp.podConfig = сontainerConfigTmp
                        podTmp.priority = priorityClassName
                        podTmp.cpuRequest = podCpuRequests
                        podTmp.memRequest = podMemRequests
                        podTmp.cpuLimit = podCpuLimit
                        podTmp.memLimit = podMemLimit
                        podTmp.status = self.constSymbol["statusPodPending"]
                        self.pod.append(podTmp)
    
    def loadYAML(self, path):
        yamlStr = ""
        with open(path, 'r') as stream:
            log.debug("open yaml")
            yamlStr = stream.read()
        return yamlStr

    def superProblem(self):
        super().problem()

    def problem(self):
        
        super().problem()
        
        self.priorityDict = self.loadPriority()
        self.node = self.loadNodeFromCloud()

        yamlStr = self.loadYAML(self._path)
 
        self.loadService(yamlStr,self.priorityDict)
        self.loadDaemonSet(yamlStr,self.priorityDict)


        #self.period1 = Period()
        self.request1 = self.addObject(Request())
        #self.request1.launchPeriod = self.period1
        self.request1.status = self.constSymbol["statusReqAtStart"]
        self.request1.state = self.constSymbol["stateRequestInactive"]

    def goal(self):
        return self.request1.status == self.constSymbol["statusReqRequestFinished"]
