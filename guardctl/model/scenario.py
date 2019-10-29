import json
import yaml
from typing import Dict, List
from dataclasses import dataclass, asdict

class Scenario:
    def __init__(self, plan=None):
        self.steps = []
        if plan:
            for a in plan:
                self.step(a())
    def step(self, step):
        self.steps.append(step)
    def asjson(self):
        return json.dumps([asdict(x) for x in self.steps])
    def asyaml(self):
        if not self.steps:
            return "# Empty scenario"
        probability = 1
        for s in self.steps:
            if s is None: continue
            probability = probability * s.probability
        jsteps = []
        for x in self.steps:
            if x is None: continue
            try:
                d = asdict(x)
            except TypeError:
                raise TypeError("Can't interpret step %s" % repr(x))
            d = dict_rename(d, "name", "actionName")
            jsteps.append(d)

        return yaml.dump({
                "probability": probability,
                # "steps": [dict_rename(asdict(x),"name","actionName") for x in self.steps]
                "steps": jsteps 
                })

def dict_rename(d, nfrom, nto):
    d[nto] = d[nfrom]
    del d[nfrom]
    return d

@dataclass
class ScenarioStep:
    name: str
    subsystem: str
    description: str
    parameters: Dict
    probability: float
    affected: List

def describe(obj):
    if hasattr(obj, "metadata_name"):
        name = str(obj.metadata_name)
    else:
        name = "no_name"
    return {"kind": obj.__class__.__name__, "metadata": {"name": name}}