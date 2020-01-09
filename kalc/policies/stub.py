from typing import Set
from kalc.model.kinds.Pod import Pod
from kalc.model.kinds.Node import Node
from kalc.model.kinds.Service import Service
from kalc.model.system.Scheduler import Scheduler
from kalc.model.system.globals import GlobalVar
from kalc.misc.const import *
from poodle import planned

class StubPolicy(BasePolicy):
    TYPE = "property"

    def register(self):
        GlobalVar.register_property(name="stub", type=bool, default=False)

    def set(self, val: bool):
        assert isinstance(val, bool), "Can only accept True or False"

        if val:
            # enable

            def hypothesis_1():
                # TODO: hypotheses can not work in parallel this way: will modify main object
                self.target_object.stub = False
                self.register_goal(self.target_object.stub, "==", True)
            
            self.register_hypothesis("Stub worked", hypothesis_1, order=1)
        else:
            # disable
            pass

    @planned(cost=1)
    def do_nothing(self,
            service: Service,
            globalVar: GlobalVar):
        assert globalVar.stub == False
        globalVar.stub = True

policy_engine.register(GlobalVar, "stub", StubPolicy)


