class Scenario:
    def __init__(self, name):
        self.severity_level = SEVERITY_HINT # 1 - max severity
        self.check = None # type: Check
        self._affected = []
        self.steps = []
        self.name = name
    def step(self, step):
        self.steps.append(step)
    def affected(self, aff):
        if aff["kind"] in [ "Cluster" ]:
            self.severity_level = SEVERITY_MAX
        self._affected.append(aff)
    def __repr__(self):
        ret = "Scenario: %s\n" % self.name
        ret += "Severity: %s\n" % self.severity_level
        ret += "Affected: %s\n" % repr(self._affected)
        i = 1
        for step in self.steps:
            ret += " - " + str(i) + ": " + str(step) + "\n"
            i += 1
        return ret