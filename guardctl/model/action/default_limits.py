from poodle import planned
from guardctl.model.object.k8s_classes import *

class K8DefaultLimits:
    @planned(cost=100)
    def SetDefaultMemRequestForPod(self,
        pod1: Pod,
        memLimit: int
        ):
            assert pod1.memRequest == -1
            assert pod1.memLimit > -1
            assert memLimit == pod1.memLimit
            
            pod1.memRequest = memLimit

    @planned(cost=100)
    def SetDefaultCpuRequestForPod(self,
        pod1: Pod,
        cpuLimit: int
        ):
            assert pod1.cpuLimit > -1
            assert pod1.cpuRequest == -1
            assert cpuLimit == pod1.cpuLimit 
            
            pod1.cpuRequest = cpuLimit
    
    @planned(cost=100)
    def SetDefaultMemLimitForPod(self,
        pod1: Pod,
        node1: Node,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert node1 == pod1.atNode
            assert memCapacity == node1.memCapacity
            pod1.memLimit = memCapacity
            
    @planned(cost=100)
    def SetDefaultCpuLimitForPod(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int
        ):
            assert pod1.cpuLimit == -1
            assert node1 == pod1.atNode
            assert cpuCapacity == node1.cpuCapacity
            
            pod1.cpuLimit = cpuCapacity   
    @planned(cost=100)
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: Pod,
        node1: Node,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert memCapacity == node1.memCapacity
            pod1.toNode = node1
            pod1.memLimit = memCapacity
            
    @planned(cost=100)
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity

    @planned(cost=100)
    def SetDefaultCpuLimitPerLimitRange(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int,
        nameSpace1: NameSpace
        ):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity