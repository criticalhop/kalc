from poodle import * 

from guardctl.importers.poodleGen import *
from guardctl.importers.problemConfigLoad import *

daemonYAMLPath = "./tests/kube-config/daemon-set-custom.yaml"
serviceYAMLPath = "./tests/kube-config/guestbook-all-in-one.yaml"

def test_loadPriority():
    prio = ['high-priority','system-cluster-critical','system-node-critical']
    priorityDict = {}
    ky = KubernitesYAMLLoad()
    ky.cloudQuery()
    priorityDict = ky.loadPriority()
    for key in priorityDict:
        assert(key in prio)


def test_loadYAML():
    KubernitesYAMLLoad().loadYAML(serviceYAMLPath)
    KubernitesYAMLLoad().loadYAML(daemonYAMLPath)

def test_loadService():
                    #app+role+tier
    serviceLabel=['redismasterbackend','redisslavebackend','guestbookfrontend','redisslave-unlimitbackend']
    ky = KubernitesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()
    yamlStr = ky.loadYAML(serviceYAMLPath)
    priorityDict = ky.loadPriority()
    ky.loadService(yamlStr, priorityDict)
    for s in ky.service:
        assert(s._label in serviceLabel)
    for p in ky.pod:
        if p.value == 'redismasterbackend0':
            assert(p.priority == priorityDict['high-priority'])
        if p.value =='redisslavebackend0':
            #requests:
            #  cpu: 100m
            #  memory: 100Mi
            assert(p.cpuRequest == PoodleGen.cpuConvert(None, '100m') * 2)
            assert(p.memRequest == PoodleGen.memConverter(None, '100Mi') * 2)
    
def test_loadDaemonSet():
    ky = KubernitesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()
    yamlStr = ky.loadYAML(daemonYAMLPath)

    priorityDict = ky.loadPriority()
    ky.loadDaemonSet(yamlStr, priorityDict)
    for p in ky.pod:
        if p.value == 'fluentd-logging0':
            assert(p.priority == priorityDict['high-priority'])
            assert(p.cpuRequest == PoodleGen.cpuConvert(None, '200m'))
            assert(p.memRequest == PoodleGen.memConverter(None, '200Mi'))
            # assert(p.cpuLimit == 0)
            assert(p.memLimit == PoodleGen.memConverter(None, '200Mi'))
        # resources:
        #   limits:
        #     memory: 200Mi
        #   requests:
        #     cpu: 200m
        #     memory: 200Mi

def test_loadNodeFromCloud():
    ky = KubernitesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()    
    node, kproxy = ky.loadNodeFromCloud()
    for n in node:
        assert(n.state == ky.constSymbol['stateNodeActive'])
        
#def test_problemRawCall():
#    KubernitesYAMLLoad().problem()
    