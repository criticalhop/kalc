from kalc.model.full import kinds_collection
from collections import defaultdict

class PolicyImplementer:
    def __init__(self, obj, all_policies, state_objects):
        self._target_object = obj
        self._all_policies = all_policies
        self._state_objects = state_objects
        self._instantiated_policies = {}
        self._sealed = False
        for p_name, p_class in all_policies.items():
            p_obj = p_class(obj, state_objects)
            self._instantiated_policies[p_name] = p_obj
            setattr(self, p_name, p_obj)
        self._sealed = True
    
    def __setattr__(self, name, val):
        if not self._sealed or name.startswith("_"): return super().__setattr__(name, val)
        if name in self._instantiated_policies and self._instantiated_policies[name].TYPE == "property":
            self._instantiated_policies[name]._set(val)
        return super().__setattr__(name, val)
    
    def __getattr__(self, name):
        if not self._sealed or name.startswith("_"): return super().__getattr__(name)
        if name in self._instantiated_policies and self._instantiated_policies[name].TYPE == "property":
            self._instantiated_policies[name]._get()
        return super().__getattr__(name)


class PolicyEngineClass:
    def __init__(self):
        self.registered_engines = defaultdict(dict)
        self.state_objects = []

    def register_state_objects(self, state_objects):
        self.state_objects = state_objects

    def register(self, kind_name, policy_name, policy_class):
        self.registered_engines[kind_name][policy_name] = policy_class
    
    def get(self, obj):
        return PolicyImplementer(self.registered_engines[obj.__class__.__name__])
        return self.registered_engines[obj.__class__.__name__](obj, self.state_objects)

policy_engine = PolicyEngineClass()

for kind_name, kind_class in kinds_collection.items():
    kind_class.policy = "STUB"
    old_getattr = kind_class.__getattr__
    def _get_policy_getattr(self, name):
        if name == "policy":
            return policy_engine.get(self)
        return old_getattr(self, name)
    kind_class.__getattr__ = _get_policy_getattr

# WARNING this whole thing looks too cryptic and must be re-implemented

class BasePolicy:
    TYPE = "function"
    def __init__(self, obj):
        self.target_object = obj
    
    def _set(self, val):
        return self.set(val)
    
    def _get(self):
        return self.get()
    
    def set(self, val):
        raise NotImplementedError("Author has not implemented set() for this policy")

    def get(self):
        raise NotImplementedError("Author has not implemented get() for this policy")

#########################################################################

from typing import Set
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.misc.const import *

class PreferredSelfAntiAffinityPolicy(BasePolicy):
    TYPE = "property"
    KIND = Service

    def register(self):
        Service.register_property(name="antiaffinity", type=bool, defaul=False) # TODO
        Service.register_property(name="antiaffinity_prefered_policy_met", type=bool, defaul=False)
        Pod.register_property(name="not_on_same_node", type=Set[Pod], default=[])

    def set(self, val: bool):
        assert isinstance(val, bool), "Can only accept True or False"

        if val:
            # enable
            pods_count = len(list(self.target_object.podList))

            assert pods_count <= 5, "We currently support up to 5 pods"

            def hypothesis_1():
                self.target_object.antiaffinity = True
                self.target_object.targetAmountOfPodsOnDifferentNodes = pods_count
                self.register_goal(self.target_object.antiaffinity_prefered_policy_met, True) # TODO
            
            self.register_hypothesis("All pods required done", hypothesis_1) # TODO
        else:
            # disable
            pass

    @planned(cost=1)
    def mark_antiaffinity_prefered_policy_met(self,
        service: Service,
        globalVar: GlobalVar):
        assert service.amountOfPodsOnDifferentNodes == service.targetAmountOfPodsOnDifferentNodes
        assert service.isSearched == True
        assert service.antiaffinity == True
        service.antiaffinity_prefered_policy_met = True

    @planned(cost=1)
    def manually_initiate_killing_of_pod(self,
        node_with_outage: Node,
        pod_killed: Pod,
        globalVar: GlobalVar
        ):
        assert pod_killed.status == STATUS_POD["Running"]
        pod_killed.status = STATUS_POD["Killing"]

    @planned(cost=1)
    def mark_2_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            service: Service,
            scheduler: Scheduler):
        assert node_of_pod2 == pod2.atNode
        assert pod1.atNode in node_of_pod2.different_than
        assert pod1 in service.podList
        assert pod2 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        pod1.not_on_same_node.add(pod2)
        service.amountOfPodsOnDifferentNodes = 2

    @planned(cost=1)
    def mark_3_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            pod3: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            node_of_pod3: Node,
            service: Service,
            scheduler: Scheduler):
        
        assert node_of_pod1 == pod1.atNode
        assert node_of_pod2 == pod2.atNode
        assert node_of_pod3 == pod3.atNode
        assert node_of_pod1 in node_of_pod2.different_than
        assert node_of_pod1 in node_of_pod3.different_than
        assert node_of_pod2 in node_of_pod3.different_than
        assert pod1 in service.podList
        assert pod2 in service.podList
        assert pod3 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        service.amountOfPodsOnDifferentNodes = 3

    @planned(cost=1)
    def mark_4_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            pod3: Pod,
            pod4: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            node_of_pod3: Node,
            node_of_pod4: Node,
            service: Service,
            scheduler: Scheduler):
        
        assert node_of_pod1 == pod1.atNode
        assert node_of_pod2 == pod2.atNode
        assert node_of_pod3 == pod3.atNode
        assert node_of_pod4 == pod4.atNode
        assert node_of_pod1 in node_of_pod2.different_than
        assert node_of_pod1 in node_of_pod3.different_than
        assert node_of_pod1 in node_of_pod4.different_than
        assert node_of_pod2 in node_of_pod3.different_than
        assert node_of_pod2 in node_of_pod4.different_than
        assert node_of_pod3 in node_of_pod4.different_than
        assert pod1 in service.podList
        assert pod2 in service.podList
        assert pod3 in service.podList
        assert pod4 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        service.amountOfPodsOnDifferentNodes = 4

    @planned(cost=1)
    def mark_5_pods_of_service_as_not_at_same_node(self,
            pod1: Pod,
            pod2: Pod,
            pod3: Pod,
            pod4: Pod,
            pod5: Pod,
            node_of_pod1: Node,
            node_of_pod2: Node,
            node_of_pod3: Node,
            node_of_pod4: Node,
            node_of_pod5: Node,
            service: Service,
            scheduler: Scheduler):
        
        assert node_of_pod1 == pod1.atNode
        assert node_of_pod2 == pod2.atNode
        assert node_of_pod3 == pod3.atNode
        assert node_of_pod4 == pod4.atNode
        assert node_of_pod5 == pod5.atNode
        assert node_of_pod1 in node_of_pod2.different_than
        assert node_of_pod1 in node_of_pod3.different_than
        assert node_of_pod1 in node_of_pod4.different_than
        assert node_of_pod1 in node_of_pod5.different_than
        assert node_of_pod2 in node_of_pod3.different_than
        assert node_of_pod2 in node_of_pod4.different_than
        assert node_of_pod2 in node_of_pod5.different_than
        assert node_of_pod3 in node_of_pod4.different_than
        assert node_of_pod3 in node_of_pod5.different_than
        assert node_of_pod4 in node_of_pod5.different_than

        assert pod1 in service.podList
        assert pod2 in service.podList
        assert pod3 in service.podList
        assert pod4 in service.podList
        assert pod5 in service.podList
        assert scheduler.status == STATUS_SCHED["Clean"]
        service.amountOfPodsOnDifferentNodes = 5

policy_engine.register(Service, "self_antiaffinity", PreferredSelfAntiAffinityPolicy)

