import pytest

from poodle import * 
pytestmark = pytest.mark.skip("all tests still WIP")


daemonYAMLPath = "./tests/kube-config/daemon-set-custom.yaml"
serviceYAMLPath = "./tests/kube-config/guestbook-all-in-one.yaml"

@pytest.mark.skip(reason="no way of currently testing this")
def test_loadPriority():
    prio = ['high-priority','system-cluster-critical','system-node-critical']
    priorityDict = {}
    ky = KubernetesYAMLLoad()
    ky.cloudQuery()
    priorityDict = ky.loadPriority()
    for key in priorityDict:
        assert(key in prio)

@pytest.mark.skip(reason="no way of currently testing this")
def test_loadYAML():
    KubernetesYAMLLoad().loadYAML(serviceYAMLPath)
    KubernetesYAMLLoad().loadYAML(daemonYAMLPath)

@pytest.mark.skip(reason="no way of currently testing this")
def test_loadService():
                    #app+role+tier
    serviceLabel=['redismasterbackend','redisslavebackend','guestbookfrontend','redisslave-unlimitbackend']
    ky = KubernetesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()
    yamlStr = ky.loadYAML(serviceYAMLPath)
    priorityDict = ky.loadPriority()
    ky.loadNodeFromCloud()
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
    
@pytest.mark.skip(reason="no way of currently testing this")
def test_loadDaemonSet():
    ky = KubernetesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()
    yamlStr = ky.loadYAML(daemonYAMLPath)

    priorityDict = ky.loadPriority()
    ky.loadNodeFromCloud()
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

@pytest.mark.skip(reason="no way of currently testing this")
def test_loadNodeFromCloud():
    ky = KubernetesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()    
    node, kproxy = ky.loadNodeFromCloud()
    for n in node:
        assert(n.state == ky.constSymbol['stateNodeActive'])

@pytest.mark.skip(reason="no way of currently testing this")
def test_loadServiceFromCloud():
    ky = KubernetesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()  
    ky.loadServiceFromCloud()
    ky.loadPodFromCloud()
#def test_problemRawCall():
#    KubernetesYAMLLoad().problem()
    

@pytest.mark.skip(reason="no way of currently testing this")
def test_emuFile():
    ky = KubernetesYAMLLoad()
    ky.superProblem()
    ky.cloudQuery()
    ky.loadNodeAsDictFromCloud("/home/andrey/coreV1_api_list_node.yaml")
    ky.loadPodAsDictFromCloud("/home/andrey/coreV1_api_list_pod_for_all_namespaces.yaml")
    ky.loadServiceAsDictFromCloud("/home/andrey/coreV1_list_service_for_all_namespaces.yaml")
    ky.loadPriorityAsDictFromCloud("/home/andrey/shV1beta1_api_list_priority_class")
#     ky = KubernetesYAMLLoad(None, )

def test_loadAllFromFiles():
    dumpList = [daemonYAMLPath, './examples/currentCloud/coreV1_api_list_node.yaml', './examples/currentCloud/coreV1_api_list_pod_for_all_namespaces.yaml',  './examples/currentCloud/coreV1_list_service_for_all_namespaces.yaml','./examples/currentCloud/shV1beta1_api_list_priority_class.yaml']
    ky = KubernetesYAMLLoad(*dumpList)
    ky.superProblem()
    yamlStr = ky.loadYAML(daemonYAMLPath)

    priorityDict = ky.loadPriority()
    ky.loadNodeFromCloud()
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

def test_problemAllFromFile():
    dumpList = [daemonYAMLPath, './examples/currentCloud/coreV1_api_list_node.yaml', './examples/currentCloud/coreV1_api_list_pod_for_all_namespaces.yaml',  './examples/currentCloud/coreV1_list_service_for_all_namespaces.yaml','./examples/currentCloud/shV1beta1_api_list_priority_class.yaml']
    ky = KubernetesYAMLLoad(*dumpList)
    ky.problem()
