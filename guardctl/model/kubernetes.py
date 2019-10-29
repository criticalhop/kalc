import yaml
import os, click
from collections import defaultdict
from guardctl.misc.object_factory import labelFactory
from poodle import planned, Property, Relation
from guardctl.misc.util import objwalk, find_property, k8s_to_domain_object, POODLE_MAXLIN, getint, split_yamldumps
from guardctl.misc.util import cpuConvertToNorm, memConvertToNorm
from guardctl.model.full import kinds_collection
from guardctl.model.search import K8ServiceInterruptSearch
from guardctl.model.system.globals import GlobalVar
from guardctl.model.system.Scheduler import Scheduler
import guardctl.misc.util

KINDS_LOAD_ORDER = ["PriorityClass", "Service", "Node", "Pod", "ReplicaSet"]

class KubernetesCluster:
    CREATE_MODE = "create"
    LOAD_MODE = "load"
    SCALE_MODE = "scale"
    APPLY_MODE = "apply"
    REPLACE_MODE = "replace"
    REMOVE_MODE = "remove"

    def __init__(self):
        self.dict_states = defaultdict(list)
        self._reset()

    def _reset(self):
        "Reset object states and require a rebuild with _bulid_state"
        self.scheduler = Scheduler()
        self.globalvar = GlobalVar()
        self.state_objects = [self.scheduler, self.globalvar]

    def load_dir(self, dir_path):
        for root, dirs, files in os.walk(dir_path):
            for fn in files:
                for ys in split_yamldumps(open(os.path.join(root, fn)).read()):
                    self.load(ys, self.LOAD_MODE)

    # load - load from dump , scale/apply/replace/remove/create - are modes from kubernetes
    def load(self, str_, mode=LOAD_MODE):
        for doc in yaml.load_all(str_, Loader=yaml.FullLoader):
            if len(str(doc)) < 100:
                click.echo(f"# WARNING  doc - {doc} to short!!!!")
            if "items" in doc:
                for item in doc["items"]: self.load_item(item, mode)
            else: self.load_item(doc, mode)


    def scale(self, replicas, str_):
        print("scale {0}".format(str_))
        # type = str_.split(".")[0] # e.g. Deployment 
        # for k,v in dict_states.items():
        #     for item in v:

    def load_item(self, item, mode=LOAD_MODE):
        assert isinstance(item, dict), item
        create = False
        if mode == self.CREATE_MODE : create = True
        item["__created"] = create
        item["__mode"] = mode
        item["__scale_replicas"] = 5
        self.dict_states[item["kind"]].append(item)

    def _build_item(self, item):
        obj = kinds_collection[item["kind"]]()
        create = item["__created"]
        mode = item["__mode"]
        replicas = item["__scale_replicas"]
        obj.kubeguard_created = create # special property to distinguish "created"
        for prop in objwalk(item):
            p, val = find_property(obj, prop)
            if p is None: continue
            val = k8s_to_domain_object(val)
            if isinstance(getattr(obj, p), Relation):
                getattr(obj, p).add(val)
            elif isinstance(getattr(obj, p), Property):
                setattr(obj, p, val)
            else:
                # means has setter
                setattr(obj, p, val)
        if mode == self.CREATE_MODE and hasattr(obj, "hook_after_create"):
            obj.hook_after_create(self.state_objects)
        if mode == self.LOAD_MODE and hasattr(obj, "hook_after_load"):
            obj.hook_after_load(self.state_objects)
        if mode == self.APPLY_MODE and hasattr(obj, "hook_after_apply"):
            obj.hook_after_apply(self.state_objects)
        # if mode == self.SCALE_MODE and hasattr(obj, "hook_scale"):
        #     obj.hook_scale(self.state_objects, replicas)
        self.state_objects.append(obj)

    def _normalize_mappings(self):
        max_ram = 0
        max_cpu = 0
        priorities = []
        for k,v in self.dict_states.items():
            for item in v:
                if k == "Pod":
                    for cnt in item["spec"]["containers"]:
                        try:
                            ram = memConvertToNorm(cnt["resources"]["requests"]["memory"])
                            if max_ram < ram: max_ram = ram
                        except KeyError:
                            pass
                        try:
                            cpu = cpuConvertToNorm(cnt["resources"]["requests"]["cpu"])
                            if max_cpu < cpu: max_cpu = cpu
                        except KeyError:
                            pass
                    # TODO: check limits too
                if k == "Node":
                    try:
                        ram = memConvertToNorm(item["status"]["allocatable"]["memory"])
                        if max_ram < ram: max_ram = ram
                        cpu = cpuConvertToNorm(item["status"]["allocatable"]["cpu"])
                        if max_cpu < cpu: max_cpu = cpu
                    except KeyError:
                        pass
                if k == "PriorityClass":
                    priorities.append(int(item["value"]))
        if max_cpu > 0:
            guardctl.misc.util.CPU_DIVISOR = int(max_cpu / (guardctl.misc.util.POODLE_MAXLIN / 2))
        if max_ram > 0:
            guardctl.misc.util.MEM_DIVISOR = int(max_ram / (guardctl.misc.util.POODLE_MAXLIN / 2))
        if len(priorities):
            pri_map = {}
            i = 1
            for p in sorted(priorities):
                pri_map[p] = i
                i+=1
            guardctl.misc.util.PRIO_MAPPING = pri_map
            assert i <= guardctl.misc.util.POODLE_MAXLIN, "Too many different priorities"

    def _build_state(self):
        self._normalize_mappings()
        collected = self.dict_states.copy()
        for k in KINDS_LOAD_ORDER:
            if not k in collected: continue
            for item in collected[k]:
                self._build_item(item)
            del collected[k]
        for k,v in collected.items():
            for item in v:
                self._build_item(item)
        self._check()

    def _check(self):
        "Run internal checks"
        assert getint(self.scheduler.queueLength) < POODLE_MAXLIN, "Queue length overflow"

    def create_resource(self, res: str):
        self.load(res, mode=self.CREATE_MODE)

    def apply_resource(self, res: str):
        self.load(res, mode=self.APPLY_MODE)

    def fetch_state_default(self):
        "Fetch state from cluster using default method"
        raise NotImplementedError()

    def run(self):
        if len(self.state_objects) < 3: self._build_state()
        k = K8ServiceInterruptSearch(self.state_objects)
        k.run()
        self.plan = k.plan
        return self.plan
        # TODO: represent plan

