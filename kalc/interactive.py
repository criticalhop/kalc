import subprocess
import json
from poodle import Object
from kalc.model.full import kinds_collection
from kalc.misc.kind_filter import FilterByLabelKey, FilterByName, KindPlaceholder
from kalc.model.kubernetes import KubernetesCluster
import kalc.policy 
from kalc.model.search import KubernetesModel
from kalc.model.kinds.Deployment import YAMLable, Deployment
from pygments import highlight
from pygments.lexers.diff import DiffLexer
from pygments.formatters.terminal import TerminalFormatter
import random
import io
import kalc.misc.util
import pkg_resources
import yaml
import kalc.misc.support_check
from kalc.misc.metrics import Metric
from logzero import logger


__version__ = pkg_resources.get_distribution("kalc").version


ALL_RESOURCES = [ "all", "node", "pc", "limitranges", "resourcequotas", "poddisruptionbudgets", "hpa"]

cluster_md5_sh = 'kubectl get pods -o wide --all-namespaces -o=custom-columns=NAME:.metadata.name,NODE:.spec.nodeName --sort-by="{.metadata.name}" | md5sum'

kalc_state_objects = []
kind = KindPlaceholder
cluster = None

md5_cluster = ""

kalc.policy.policy_engine.register_state_objects(kalc_state_objects)

for k, v in kinds_collection.items():
    v.by_name = FilterByName(k, kalc_state_objects)
    v.by_label = FilterByLabelKey(k, kalc_state_objects)
    globals()[k] = v
    setattr(kind, k, v)

def update(data=None):
    "Fetch information from currently selected cluster"
    if isinstance(data, io.IOBase):
        data = data.read()
    k = KubernetesCluster()
    all_data = []
    all_support_checks = []
    if not data:
        global md5_cluster
        result = subprocess.Popen(cluster_md5_sh, shell=True, stdout=subprocess.PIPE, executable='/bin/bash')
        md5_cluster = result.stdout.read().decode('ascii').split()[0]
        assert len(md5_cluster) == 32, "md5_cluster sum wrong len({0}) not is 32".format(md5_cluster)


        for res in ALL_RESOURCES:
            result = subprocess.run(['kubectl', 'get', res, '--all-namespaces', '-o=json'], stdout=subprocess.PIPE)
            if len(result.stdout) < 100:
                print(result.stdout)
                raise SystemError("Error using kubectl. Make sure `kubectl get pods` is working.")
            data = json.loads(result.stdout.decode("utf-8"))
            y_data = yaml.dump(data, default_flow_style=False)
            sc = kalc.misc.support_check.YAMLStrSupportChecker(yaml_str=y_data)
            all_support_checks.extend(sc.check())
            all_data.append(data)
        
        for result in all_support_checks:
            if not result.isOK(): logger.warning("Unsupported feature: %s" % str(result))
            else: logger.debug(str(result))
        
        for d in all_data:
            for item in d["items"]:
                k.load_item(item)

    else:
        # TODO: make sure "data" is in YAML format
        sc = kalc.misc.support_check.YAMLStrSupportChecker(yaml_str=data)
        for result in sc.check():
            if not result.isOK(): logger.warning("Unsupported feature: %s" % str(result))
            else: logger.debug(str(result))

        for ys in kalc.misc.util.split_yamldumps(data):
            k.load(ys)
    
    k._build_state()
    global kalc_state_objects
    kalc_state_objects.clear()
    kalc_state_objects.extend(k.state_objects)
    global cluster
    cluster = next(filter(lambda x: isinstance(x, GlobalVar), k.state_objects)) # pylint: disable=undefined-variable

def run():
    # TODO HERE: copy state_objects!
    # as we will be running multiple times, we need to store original state
    # or we actually don't! we can continue computing on top of previous...?
    # for now it is ok..
    kube = KubernetesModel(kalc_state_objects)
    policy_added = False
    hypotheses = []
    for ob in kalc_state_objects:
        if isinstance(ob.policy, str): continue # STUB. find and fix
        hypotheses.append(ob.policy.apply(kube))
    # TODO HERE: generate different combinations of hypotheses
    kube.run(timeout=999000, sessionName="kalc")
    # TODO. STUB
    # TODO example hanlers and patches
    for obj in kalc_state_objects:
        if isinstance(obj, Deployment):
            if "redis-slave" in str(obj.metadata_name):
                obj.affinity_required_handler()
                # obj.scale_replicas_handler(random.randint(4,10))

    if policy_added: patch()
    for a in kube.plan:
        print(a)
        r = a()
        if isinstance(r, dict) and "kubectl" in r:
            print(">>", r["kubectl"])
    # print summary

def patch():
    for obj in kalc_state_objects:
        if isinstance(obj, Deployment):
            # print("patch for ", obj.metadata_name)
            print(highlight(obj.get_patch(), DiffLexer(), TerminalFormatter()))

def apply():
    pass