from poodle import planned
from object.kubeObject import *
# kubernetes scheduler module

class K8DefaultLimits:
    @planned
    def SetDefaultMemRequestForPod(self,
        pod1: Pod,
        memLimit: int
        ):
            assert pod1.memRequest == -1
            assert pod1.memLimit > -1
            assert memLimit == pod1.memLimit
            
            pod1.memRequest = memLimit

    @planned
    def SetDefaultCpuRequestForPod(self,
        pod1: Pod,
        cpuLimit: int
        ):
            assert pod1.cpuLimit > -1
            assert pod1.cpuRequest == -1
            assert cpuLimit == pod1.cpuLimit 
            
            pod1.cpuRequest = cpuLimit
    
    @planned
    def SetDefaultMemLimitForPod(self,
        pod1: Pod,
        node1: Node,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert node1 == pod1.atNode
            assert memCapacity == node1.memCapacity
            pod1.memLimit = memCapacity
            
    @planned
    def SetDefaultCpuLimitForPod(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int
        ):
            assert pod1.cpuLimit == -1
            assert node1 == pod1.atNode
            assert cpuCapacity == node1.cpuCapacity
            
            pod1.cpuLimit = cpuCapacity   
    @planned
    def SetDefaultMemLimitForPodBeforeNodeAssignment(self,
        pod1: Pod,
        node1: Node,
        memCapacity: int
        ):
            assert pod1.memLimit == -1
            assert memCapacity == node1.memCapacity
            pod1.toNode = node1
            pod1.memLimit = memCapacity
            
    @planned
    def SetDefaultCpuLimitForPodBeforeNodeAssignment(self,
        pod1: Pod,
        node1: Node,
        cpuCapacity: int):
            assert pod1.cpuLimit == -1
            assert cpuCapacity == node1.cpuCapacity
            pod1.toNode = node1
            pod1.cpuLimit = cpuCapacity

    @planned
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