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
            probability = probability * s.probability
        return yaml.dump({
                "probability": probability,
                "steps": [asdict(x) for x in self.steps]
                })

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