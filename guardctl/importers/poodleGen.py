import sys
import logging as log

from poodle import * 
from guardctl.model.object.k8s_classes import *
from guardctl.model.action.scheduler import *
from guardctl.model.action.eviction import *
from guardctl.model.action.oom_kill import *


from guardctl.model.problem.problemTemplate import ProblemTemplate

from kubernetes import client, config
import croniter, datetime
import random


class StatusFactory:
    status = {}

    def add(self, statusName):
        if statusName in self.status:
            return self.status[statusName]
        else:
            self.status[statusName] = pyKube.Status()
            return self.status[statusName]

class PoodleGen(ProblemTemplate):
    name = "Basic generator"
    
    def cpuConvert(self, cpuParot):
        #log.debug("cpuParot", cpuParot)
        cpu = 0
        if cpuParot[len(cpuParot)-1] == 'm':
            cpu = int(cpuParot[:-1])
        else:
            cpu = int(cpuParot)*1000
        # log.debug("cpuParot ", cpuParot, " ret ", cpuAdd)
        cpu = cpu / 20
        if cpu == 0:
            cpu = 1
        return int(cpu)

    def memConverter(self, mem):
        ret = 0
        if mem[len(mem)-2:] == 'Gi':
            ret = int(mem[:-2])*1000
        elif mem[len(mem)-2:] == 'Mi':
            ret = int(mem[:-2])
        elif mem[len(mem)-2:] == 'Ki':
            ret = int(int(mem[:-2])/1000)
        else:
            ret = int(int(mem)/1000000)
        ret = ret / 20
        if ret == 0:
            ret = 1
        return int(ret)
    
    def deepNumbers(self, v, max_value, max_new_value):    
        return int(v * max_new_value / max_value)
            

    podsFromCloud = []

    def problem(self):
        super().problem()
        # Kubernites query
        config.load_kube_config()
        cj_api = client.CoreV1Api()
   
        
        pods = cj_api.list_pod_for_all_namespaces()
        nodes = cj_api.list_node()
        services = cj_api.list_service_for_all_namespaces()
        
        # log.debug("podss")
        # log.debug(pods)
        # log.debug("podssend")
#        log.debug("services ", services)
        
        #self.period1 = self.addObject(Period()) ## todo may be move to the dict
        
        #calulate cpu in range (1, 10)
        CPUs = {}
        for nodek in nodes.items:
            CPUs[nodek.status.allocatable['cpu']] = self.cpuConvert(nodek.status.allocatable['cpu'])
        for i in CPUs.keys() :
            CPUs[i] = self.deepNumbers(CPUs[i], max(CPUs.values()), 9)
        
        #calulate memory in range (1, 10)
        MEMs = {}
        for nodek in nodes.items:
            MEMs[nodek.status.allocatable['memory']] = self.memConverter(nodek.status.allocatable['memory'])
        for i in MEMs.keys() :
            MEMs[i] = self.deepNumbers(MEMs[i], max(MEMs.values()), 9)
            
        for nodek in nodes.items:
            
            nodeTmp = self.addObject(Node(nodek.metadata.name))
            nodeTmp.cpuCapacity = self.cpuConvert(nodek.status.capacity['cpu'])
            nodeTmp.memCapacity = self.memConverter(nodek.status.capacity['memory'])
            nodeTmp.podAmount = int(nodek.status.capacity['pods'])
#            log.debug("node name {name} pods {pod} capacity cpu {cpu} mem {mem}".format(name = nodek.metadata.name, cpu=nodeTmp.cpuCapacity, mem=nodeTmp.memCapacity, pod=nodeTmp.podAmount))
            
            kubeProxyTmp = self.addObject(Kubeproxy())
            kubeProxyTmp.atNode = nodeTmp
            kubeProxyTmp.mode = self.constSymbol['modeUsermode']
            
            #for .selectionedPod.add look for "fill pod with corresponding kube-proxy" in pod iterate section

            #append Node and Proxy to node's and Proxy's list (access by self.node[node_num])
            self.kubeProxy.append(kubeProxyTmp)

            #defaul values
            nodeTmp.state = self.constSymbol['stateNodeActive']
            nodeTmp.status = self.constSymbol['statusNodeActive']
            nodeTmp.currentFormalCpuConsumption = CPUs[nodek.status.allocatable['cpu']]
            nodeTmp.currentFormalMemConsumption = MEMs[nodek.status.allocatable['memory']]
            nodeTmp.currentRealMemConsumption = 0
            nodeTmp.currentRealCpuConsumption = 0
            nodeTmp.AmountOfPodsOverwhelmingMemLimits = 0

            self.node.append(nodeTmp)

        for servicek in services.items:
            serviceTmp = self.addObject(Service())
                    #count active pods (need for services)
            amountOfActivePods = 0
            for podk in pods.items:
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
            if 'app' in servicek.metadata.labels:
                serviceTmp._label = servicek.metadata.labels['app']
                if 'role' in servicek.metadata.labels:
                    serviceTmp._label = serviceTmp._label + servicek.metadata.labels['role']
                if 'tier' in servicek.metadata.labels:
                    serviceTmp._label = serviceTmp._label + servicek.metadata.labels['tier']
            
            if servicek.spec.type == 'LoadBalancer':
  
                newLb = self.addObject(Loadbalancer())
                newLb._ipAndName = servicek.status.load_balancer.ingress # .ip - ip addr  .name - domain
                newLb.selectionedService.add(serviceTmp)
                self.loadbalancer.append(newLb)

            self.service.append(serviceTmp)
        log.debug("load balancer" , self.loadbalancer)

        for podk in pods.items:
            #log.debug(podk.metadata.name)
            #exit(0)
            podTmp = self.addObject(Pod(podk.metadata.name))
            #load label
            if 'app' in podk.metadata.labels:
                podTmp._label = podk.metadata.labels['app']
                if 'role' in  podk.metadata.labels:
                    podTmp._label = podTmp._label + podk.metadata.labels['role']
                if 'tier' in  podk.metadata.labels:
                    podTmp._label = podTmp._label + podk.metadata.labels['tier']
            
            #containerCOnfig
            сontainerConfigTmp = ContainerConfig()
            for serviceI in self.service:
                if serviceI._label == podTmp._label:
                    сontainerConfigTmp.service = serviceI
            podTmp.podConfig = сontainerConfigTmp
            self.containerConfig.append(self.addObject(сontainerConfigTmp))

            sym = self.constSymbol["statePod" + str(podk.status.phase)]
            # log.debug("object is ", sym)

            podTmp.state = sym

            podCpuLimit = -1
            podCpuRequests = -1
            podMemLimit = -1
            podMemRequests = -1
            for container in podk.spec.containers:
                if container.resources.limits != None and 'cpu' in container.resources.limits:
                    if podCpuLimit < 0 : podCpuLimit=0
                    podCpuLimit += self.cpuConvert(container.resources.limits['cpu'])
                if container.resources.limits != None and 'memory' in container.resources.limits:
                    if podMemLimit < 0 : podMemLimit=0
                    podMemLimit += self.memConverter(container.resources.limits['memory'])
                if container.resources.requests != None and 'cpu' in container.resources.requests:
                    if podCpuRequests < 0 : podCpuRequests=0
                    podCpuRequests += self.cpuConvert(container.resources.requests['cpu'])
                if container.resources.requests != None and 'memory' in container.resources.requests:
                    if podMemRequests < 0 : podMemRequests=0
                    podMemRequests += self.memConverter(container.resources.requests['memory'])
                # log.debug("container resources limit cpu {cpu}m  mem {mem}Mi".format(cpu=podCpuLimit, mem=podMemLimit))
                # log.debug("container resources Requests cpu {cpu}m  mem {mem}Mi".format(cpu=podCpuRequests, mem=podMemRequests))
            if podCpuRequests < 0:
                podTmp.requestedCpu = "null"
            else:
                podTmp.requestedCpu = podCpuRequests
            if podMemRequests < 0:
                podTmp.requestedMem = "null"
            else:
                podTmp.requestedMem = podMemRequests
            
            
            #default values
            podTmp.currentRealCpuConsumption = 0
            podTmp.currentRealMemConsumption = 0
            podTmp.status = self.constSymbol['statusPodAtConfig']
            podTmp.podNotOverwhelmingLimits = True
            podTmp.realInitialMemConsumption = 1
            podTmp.realInitialCpuConsumption = 1
            podTmp.type = self.constSymbol['typePersistent']
            podTmp.memLimit =  3
            podTmp.cpuLimit =  3
            
            podTmp.priority =  1
            
            #fill pod with corresponding kube-proxy
            for idx, nodeTmp in enumerate(self.node):
                if nodeTmp.value == podk.spec.node_name:
                    #self.kubeProxy[idx].selectionedPod.add(podTmp)
                    podTmp.atNode = nodeTmp
            
            podTmp.status
            
            log.debug("pod name {0} status {1} ".format(podk.metadata.name, podk.status.phase))
            #append pod to pod's list
            self.pod.append(podTmp)




        #generate random requests
        for reqNum in range(0, 10):
            req = Request()
          #  req.launchPeriod = self.period1
            req.status = self.constSymbol['statusReqAtStart']
            req.state = self.constSymbol['stateRequestInactive']
            req.targetService = self.service[random.randint(0,len(self.service)-1)] # get random service
            req.cpuRequest = 1
            req.memRequest = 1
            req.type = self.constSymbol['typeTemporary']
            self.request.append(self.addObject(req))

    def goal(self):
        #generate goal

        ret = True
        for req in self.request:
            ret = ret and (req.status == self.constSymbol['statusReqRequestFinished'])


if __name__ == '__main__':
    PoodleGen().problem()