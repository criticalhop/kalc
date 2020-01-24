import re


class SupportCheckResult:
    def __init__(self, check_name, value, state: bool, description=""):
        self.name = check_name
        self.check_calue = value
        self.support_status = state
        self.description = description
    
    def __str__(self):
        return f"{self.name}, {self.value}, {self.support_status}, {self.description}"

    def isOK(self):
        return self.support_status


class SupportChecker:    
    def check(self):
        ret = []
        for c in dir(self):
            if not c.startswith("check_"):
                continue
            self.ok = None
            self.value = None
            self.description = None
            getattr(self, c)(self.yaml_str)
            assert not self.ok is None 
            assert not self.value is None
            assert not self.description is None
            ret.append(SupportCheckResult(c.replace("check_", ""), self.value, self.ok, self.description))
        return ret


class ModelSupportChecker(SupportChecker):
    def __init__(self, state_objects: list):
        self.state_objects = state_objects

class YAMLStrSupportChecker(SupportChecker):
    def __init__(self, yaml_str: str):
        self.yaml_str = yaml_str

    def check_LimitRanges(self):
        val = len(re.findall("LimitRange", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val
    
    def check_ResourceQuota(self):
        val = len(re.findall("ResourceQuota", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_AdmissionConfiguration(self):
        val = len(re.findall("AdmissionConfiguration", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_matchExpressions(self):
        val = len(re.findall("matchExpressions", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val
    
    def check_matchScopes(self):
        val = len(re.findall("matchScopes", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_required_anti_affinity(self):
        val = len(re.findall("requiredDuringSchedulingIgnoredDuringExecution", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_preferred_anti_affinity(self):
        val = len(re.findall("preferredDuringSchedulingIgnoredDuringExecution", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_podAffinity(self):
        val = len(re.findall("podAffinity", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_podAntiAffinity(self):
        val = len(re.findall("podAntiAffinity", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_nodeAffinity(self):
        val = len(re.findall("nodeAffinity", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_affinity_weights(self):
        val = len(re.findall("weight:", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_existential_selectors(self):
        val = len(re.findall("Exists", self.yaml_str))
        val2 = len(re.findall("DoesNotExist", self.yaml_str))
        self.ok = (val+val2 == 0)
        self.description = ""
        self.value = val+val2
    
    def check_tolerations(self):
        val = len(re.findall("tolerations:", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_NoSchedule(self):
        val = len(re.findall("NoSchedule", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_NoExecute(self):
        val = len(re.findall("NoExecute", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val

    def check_PreferNoSchedule(self):
        val = len(re.findall("PreferNoSchedule", self.yaml_str))
        self.ok = (val == 0)
        self.description = ""
        self.value = val
























