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