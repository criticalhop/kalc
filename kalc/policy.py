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
# Now import all policies from policies folder

import kalc.policies
import pkgutil, inspect

policies_collection = {}

for importer, modname, ispkg in pkgutil.iter_modules(
        path=kalc.policies.__path__,
        prefix=kalc.policies.__name__+'.'):
    module = __import__(modname, fromlist="dummy") # importing should be enough
    # for n in dir(module):
    #     c = getattr(module, n)
    #     if inspect.isclass(c) and issubclass(c, Object) and not c is Object:
    #         kinds_collection[c.__name__] = c


    