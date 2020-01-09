from kalc.model.full import kinds_collection
from collections import defaultdict
from kalc.model.search import KubernetesModel

class PolicyImplementer:
    def __init__(self, obj, all_policies, state_objects):
        self._target_object = obj
        self._all_policies = all_policies
        self._state_objects = state_objects
        self._instantiated_policies = {}
        self._sealed = False
        for p_name, p_class in all_policies.items():
            # print("Adding policy")
            p_obj = p_class(obj, state_objects)
            self._instantiated_policies[p_name] = p_obj
            setattr(self, p_name, p_obj)
        self._sealed = True
    
    def __setattr__(self, name, val):
        if name.startswith("_") or not self._sealed: return super().__setattr__(name, val)
        if name in self._instantiated_policies and self._instantiated_policies[name].TYPE == "property":
            self._instantiated_policies[name]._set(val)
        return super().__setattr__(name, val)
    
    def __getattr__(self, name):
        if name.startswith("_") or not self._sealed: return super().__getattr__(name)
        if name in self._instantiated_policies and self._instantiated_policies[name].TYPE == "property":
            self._instantiated_policies[name]._get()
        return super().__getattr__(name)
    
    def apply(self, kube: KubernetesModel):
        print("AAA trying to activate policy", self._instantiated_policies)
        for pname, pobject in self._instantiated_policies.items():
            print("AAA checking ", pname)
            if pobject.activated:
                print("AAA found activated policy")
                for hname, hval in pobject.hypotheses.items():
                    print("AAA Adding hypothesis goal")
                    pobject.clear_goal()
                    hval()
                    kube.add_goal_eq(pobject.get_goal_eq())
                    kube.add_goal_in(pobject.get_goal_in())
                for name in dir(pobject):
                    if callable(getattr(pobject, name)) and hasattr(getattr(pobject, name), "_planned"):
                        print("AAA Adding planned method from policy", name)
                        kube.add_external_method(getattr(pobject, name))


class PolicyEngineClass:
    def __init__(self):
        self.registered_engines = defaultdict(dict)
        self.state_objects = []
        self._cache = {}

    def register_state_objects(self, state_objects):
        self.state_objects = state_objects

    def register(self, kind_name, policy_name, policy_class):
        self.registered_engines[kind_name.__name__][policy_name] = policy_class
        # print("Registered policy", self.registered_engines)
    
    def get(self, obj):
        if not obj in self._cache:
            self._cache[obj] = PolicyImplementer(obj, self.registered_engines[obj.__class__.__name__], self.state_objects)
        return self._cache[obj]

policy_engine = PolicyEngineClass()

for kind_name, kind_class in kinds_collection.items():
    kind_class.policy = "STUB"
    kind_class.policy_engine = policy_engine
    # if hasattr(kind_class, "__getattr__"):
    #     old_getattr = kind_class.__getattr__
    #     _getattr = True
    # else:
    #     old_getattr = kind_class.__getattribute__
    #     _getattr = False
    # def _get_policy_getattr(self, name):
    #     if name == "policy":
    #         return policy_engine.get(self)
    #     return old_getattr(self, name)
    # if _getattr: kind_class.__getattr__ = _get_policy_getattr
    # else: kind_class.__getattribute__ = _get_policy_getattr

# WARNING this whole thing looks too cryptic and must be re-implemented

class BasePolicy:
    TYPE = "function"
    ACTIVATED = False
    def __init__(self, obj, state_objects):
        self.target_object = obj
        self.goal_eq_list = []
        self.goal_in_list = []
        self.hypotheses = {}
        self.state_objects = state_objects
    
    def register_goal(self, f1, operator, f2):
        assert operator == "==" or operator == "in", "operator must be == or in"
        if operator == "==":
            self.goal_eq_list.append([f1, f2])
        else:
            self.goal_in_list.append([f1, f2])

    def register_hypothesis(self, name, func):
        self.hypotheses[name] = func
    
    def clear_goal(self):
        self.goal_eq_list = []
        self.goal_in_list = []
    
    def get_goal_in(self):
        return self.goal_in_list

    def get_goal_eq(self):
        return self.goal_eq_list
    
    def _set(self, val):
        if not self.ACTIVATED:
            self.ACTIVATED = True
            self.register()
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
from poodle import planned

class PreferredSelfAntiAffinityPolicy(BasePolicy):
    TYPE = "property"
    KIND = Service

    def register(self):
        Service.register_property(name="antiaffinity", type=bool, default=False)
        Service.register_property(name="antiaffinity_prefered_policy_met", type=bool, default=False)
        Service.register_property(name="targetAmountOfPodsOnDifferentNodes", type=int, default=-1)
        Pod.register_property(name="not_on_same_node", type=Set[Pod], default=None)

    def set(self, val: bool):
        assert isinstance(val, bool), "Can only accept True or False"

        if val:
            # enable
            pods_count = len(list(self.target_object.podList))

            assert pods_count <= 5, "We currently support up to 5 pods"

            def hypothesis_1():
                # TODO: hypotheses can not work in parallel this way: will modify main object
                self.target_object.antiaffinity = True
                self.target_object.targetAmountOfPodsOnDifferentNodes = pods_count
                self.register_goal(self.target_object.antiaffinity_prefered_policy_met, "==", True)
            
            self.register_hypothesis("All pods required done", hypothesis_1)
        else:
            # disable
            pass

    @planned(cost=1)
    def mark_antiaffinity_prefered_policy_met(self,
        service: Service,
        globalVar: GlobalVar):
        assert service.amountOfPodsOnDifferentNodes == service.targetAmountOfPodsOnDifferentNodes
        assert service.antiaffinity == True
        service.antiaffinity_prefered_policy_met = True

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

