import pytest
import yaml
import sys
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.kinds.Pod import Pod
from guardctl.model.kinds.Node import Node
from guardctl.model.kinds.Service import Service
from guardctl.model.kinds.PriorityClass import PriorityClass
from guardctl.model.search import OptimisticRun
from guardctl.model.system.Scheduler import Scheduler
from guardctl.misc.const import *
from guardctl.misc.object_factory import labelFactory
from poodle import debug_plan
from poodle.schedule import EmptyPlanError
from guardctl.model.scenario import Scenario
import guardctl.model.kinds.Service as mservice
from tests.test_util import print_objects
import guardctl.model.kinds.Pod as mpod
from guardctl.cli import run
import click
from click.testing import CliRunner
from poodle import planned
from guardctl.model.scenario import ScenarioStep, describe
from guardctl.model.system.globals import GlobalVar

import logging
import logzero
from logzero import logger

# This log message goes to the console
logger.debug("hello")
# Set a minimum log level
logzero.loglevel(logging.INFO)
# Set a minimum log level
logzero.loglevel(logging.INFO)

# You can also set a different loglevel for the file handler
logzero.logfile("./logs/log.log")
logzero.logfile("./logs/loginfo.log", loglevel=logging.INFO)
logzero.logfile("./logs/loginfo.log", loglevel=logging.ERROR)

# Set a custom formatter
formatter = logging.Formatter('%(name)s - %(asctime)-15s - %(levelname)s: %(message)s');
logzero.formatter(formatter)

# Log some variables
# print("var1: %s, var2: %s", var1, var2)

TEST_CLUSTER_FOLDER = "./tests/daemonset_eviction/cluster_dump"
TEST_DAEMONSET = "./tests/daemonset_eviction/daemonset_create.yaml"


daemonset1_100_100_h = "./tests/test-scenario/test_data/daemonset1_100_100_h.yaml"
daemonset1_500_1000_h = "./tests/test-scenario/test_data/daemonset1_500_1000_h.yaml"
daemonset3_500_1000_z = "./tests/test-scenario/test_data/daemonset3_500_1000_z.yaml"
daemonset4_300_300_h = "./tests/test-scenario/test_data/daemonset4_300_300_h.yaml"

deployment1_5_100_100_h = "./tests/test-scenario/test_data/deployment1_5_100_100_h.yaml"
deployment2_5_100_100_z = "./tests/test-scenario/test_data/deployment2_5_100_100_z.yaml"
deployment3_5_100_100_z = "./tests/test-scenario/test_data/deployment3_5_100_100_z_s3.yaml"

node1_3200_3200 = "./tests/test-scenario/test_data/node1_3200_3200.yaml"
node2_3200_3200 = "./tests/test-scenario/test_data/node2_3200_3200.yaml"
node3_3200_3200 = "./tests/test-scenario/test_data/node3_3200_3200.yaml"

pods1_1_100_100_h_n2 = "./tests/test-scenario/test_data/pods1_1_100_100_h_n2.yaml"
pods2_1_100_100_h_s1_n2 = "./tests/test-scenario/test_data/pods2_1_100_100_h_s1_n2.yaml"
pods3_1_100_100_h_s2_n2 = "./tests/test-scenario/test_data/pods3_1_100_100_h_s2_n2.yaml"
pods4_1_100_100_z_n2 = "./tests/test-scenario/test_data/pods4_1_100_100_z_n2.yaml"
pods5_1_100_100_z_s1_n1 = "./tests/test-scenario/test_data/pods5_1_100_100_z_s1_n1.yaml"
pods6_1_100_100_z_s2_n2 = "./tests/test-scenario/test_data/pods6_1_100_100_z_s2_n2.yaml"
pods7_1_1000_1000_h_n1 = "./tests/test-scenario/test_data/pods7_1_1000_1000_h_n1.yaml"
pods8_1_1000_1000_h_s1_n2 = "./tests/test-scenario/test_data/pods8_1_1000_1000_h_s1_n2.yaml"
pods9_1_1000_1000_h_s2_n2 = "./tests/test-scenario/test_data/pods9_1_1000_1000_h_s2_n2.yaml"
pods10_1_1000_1000_z_n2 = "./tests/test-scenario/test_data/pods10_1_1000_1000_z_n2.yaml"
pods11_1_1000_1000_z_s1_n1 = "./tests/test-scenario/test_data/pods11_1_1000_1000_z_s1_n1.yaml"
pods12_1_1000_1000_z_s2_n2 = "./tests/test-scenario/test_data/pods12_1_1000_1000_z_s2_n2.yaml"
pods13_5_100_100_h_d1_2n1_1n2_2n3 = "./tests/test-scenario/test_data/pods13_5_100_100_h_d1_2n1_1n2_2n3.yaml"
pods14_5_100_100_z_d2_3n1_2n3 = "./tests/test-scenario/test_data/pods14_5_100_100_z_d2_3n1_2n3.yaml"
pods15_5_100_100_z_d3_2n2_3n3 = "./tests/test-scenario/test_data/pods15_5_100_100_z_d3_2n2_3n3.yaml"
pods16_1_1000_1000_h_s1_n2 = "./tests/test-scenario/test_data/pods16_1_1000_1000_h_s1_n2.yaml"
pods17_1_1000_1000_z_s1_n1 = "./tests/test-scenario/test_data/pods17_1_1000_1000_z_s1_n1.yaml"
pods18_5_100_100_z_d2_3n1_2n2 = "./tests/test-scenario/test_data/pods18_5_100_100_z_d2_3n1_2n2.yaml"

priorityclass = "./tests/test-scenario/test_data/priorityclass.yaml"
replicaset_for_deployment1 = "./tests/test-scenario/test_data/replicaset_for_deployment1.yaml"
replicaset_for_deployment2 = "./tests/test-scenario/test_data/replicaset_for_deployment2.yaml"
replicaset_for_deployment3 = "./tests/test-scenario/test_data/replicaset_for_deployment3.yaml"
service1 = "./tests/test-scenario/test_data/service1.yaml"
service2 = "./tests/test-scenario/test_data/service2.yaml"
service3 = "./tests/test-scenario/test_data/service3.yaml"

DUMP1_S1_H_S2_Z_FREE_200 = [priorityclass,\
                            node1_3200_3200,\
                            node2_3200_3200,\
                            pods7_1_1000_1000_h_n1,\
                            pods11_1_1000_1000_z_s1_n1,\
                            pods17_1_1000_1000_z_s1_n1,\
                            pods8_1_1000_1000_h_s1_n2,\
                            pods12_1_1000_1000_z_s2_n2,\
                            pods16_1_1000_1000_h_s1_n2,\
                            service1,\
                            service2]

DUMP1_S1_H_S2_Z_FREE_200_WITH_D2=[]
DUMP1_S1_H_S2_Z_FREE_200_WITH_D2.extend(DUMP1_S1_H_S2_Z_FREE_200)
DUMP1_S1_H_S2_Z_FREE_200_WITH_D2.extend([deployment2_5_100_100_z,\
                                        replicaset_for_deployment2,\
                                        pods18_5_100_100_z_d2_3n1_2n2])

DUMP1_S1_H_S2_Z_FREE_200_WITH_DAEMONSET_ZERO=[]
DUMP1_S1_H_S2_Z_FREE_200_WITH_DAEMONSET_ZERO.extend(DUMP1_S1_H_S2_Z_FREE_200)
DUMP1_S1_H_S2_Z_FREE_200_WITH_DAEMONSET_ZERO.extend([daemonset3_500_1000_z])

CHANGE_DEPLOYMENT_HIGH = [deployment1_5_100_100_h]
CHANGE_DAEMONSET_HIGH = [daemonset4_300_300_h]
CHANGE_DEPLOYMENT_ZERO = [deployment2_5_100_100_z]
CHANGE_DEPLOYMENT_ZERO_WITH_SERVICE = [deployment3_5_100_100_z,replicaset_for_deployment3,service3]

def print_plan(p):
    print("Plan:")
    if p.plan:
        for a in p.plan:
            print(a)
    else:
        print("Empty plan") 
        
def print_objects_compare(k,k2):
    print("---originaly-generated---")
    print_objects(k.state_objects)
    print("---loaded-from-yaml----")
    print_objects(k2.state_objects)

def calculate_variable_dump(DUMP_local):
    DUMP_with_command = []
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            DUMP_with_command.extend(["--dump-file"])
            DUMP_with_command.extend([dump_item])
    return DUMP_with_command

def calculate_variable_change(CHANGE_local):
    CHANGE_with_command = []
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            CHANGE_with_command.extend(["-f"])
            CHANGE_with_command.extend([change_item])
    CHANGE_with_command.extend(["-o", "yaml", "-t", "650","--pipe"])
    return CHANGE_with_command

def run_wo_cli_step1(DUMP_local,CHANGE_local):
    k = KubernetesCluster()
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            k.load(open(dump_item).read())
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            k.create_resource(open(change_item).read())
    k._build_state()
    pod_running = next(filter(lambda x: isinstance(x, Pod) and x.status == STATUS_POD["Running"], k.state_objects))
    class NewGoal(OptimisticRun):
        goal = lambda self: pod_running.status == STATUS_POD["Killing"]
    p = NewGoal(k.state_objects)
    print("#### run_wo_cli:")
    print("#### print_objects before run: #### ")
    print(print_objects(k.state_objects))

    p.run(timeout=300, sessionName="test_OptimisticRun")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print("##### Scenario:")
    print(Scenario(p.plan).asyaml())
    print("#### print_objects after run: ####")
    print(print_objects(k.state_objects))

def run_wo_cli(DUMP_local,CHANGE_local):
    k = KubernetesCluster()
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            k.load(open(dump_item).read())
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            k.create_resource(open(change_item).read())
    k._build_state()
    p = OptimisticRun(k.state_objects)
    print("#### run_wo_cli:")
    print("#### print_objects before run: ######")
    print(print_objects(k.state_objects))

    p.run(timeout=300, sessionName="test_OptimisticRun")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print("#### Scenario:")
    print(Scenario(p.plan).asyaml())
    print("#### print_objects after run: ######")
    print(print_objects(k.state_objects))

def run_dir_wo_cli(DUMP_local,CHANGE_local):
    k = KubernetesCluster()
    if not (DUMP_local is None):
        for dump_item in DUMP_local:
            k.load_dir(dump_item)
    if not (CHANGE_local is None):
        for change_item in CHANGE_local:
            k.create_resource(open(change_item).read())
    k._build_state()
    p = OptimisticRun(k.state_objects)
    print("#### run_wo_cli:")
    print("#### print_objects before run: #####")
    print(print_objects(k.state_objects))

    p.run(timeout=6600, sessionName="test_OptimisticRun")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print("####  Scenario:")
    print(Scenario(p.plan).asyaml())
    print("#### print_objects after run: ######")
    print(print_objects(k.state_objects))

def run_cli_directly(DUMP_with_command_local,CHANGE_with_command_local):
    k = KubernetesCluster()
    args = []
    args.extend(calculate_variable_dump(DUMP_with_command_local))
    args.extend(calculate_variable_change(CHANGE_DEPLOYMENT_HIGH))
    run(args) # pylint: disable=no-value-for-parameter

def run_cli_invoke(DUMP_with_command_local,CHANGE_with_command_local):
    runner = CliRunner()
    args=[]
    args.extend(calculate_variable_dump(DUMP_with_command_local))
    args.extend(calculate_variable_change(CHANGE_DEPLOYMENT_HIGH))
    result = runner.invoke(run,args)
    print("##### run_cli_invoke:")
    print(result.output)
    assert result.exit_code == 0



from guardctl.model.full import kinds_collection
from guardctl.model.kinds.PriorityClass import PriorityClass, zeroPriorityClass
import guardctl.model.kinds.Node as mnode
import guardctl.model.kinds.Service as mservice
from guardctl.misc.util import CPU_DIVISOR, MEM_DIVISOR
import time,random
from typing import List
import re
import yaml
yaml.Dumper.ignore_aliases = lambda *args : True
def convert_space_to_dict(space, load_logic_support=True):
    resources = []
    SUPPORTED_KINDS = kinds_collection
    UNSUPPORTED_KINDS = ["Scheduler", "GlobalVar"] 
    # processed_objects = []
    # TODO HERE: sort space so that pods, nodes, services are always processed last
    pods = [x for x in space if type(x).__name__ == "Pod"]
    nodes = [x for x in space if type(x).__name__ == "Node"]
    services = [x for x in space if type(x).__name__ == "Service"]
    last_res = pods + nodes + services
    beg_res = [ x for x in space if not x in last_res]
    sorted_space = beg_res + last_res
    # because we would generate pods defs from Deployment, DaemonSet
    for ob in sorted_space:
        # if ob in processed_objects: continue
        # print("Doing for", ob, ob.__class__.__name__)
        if ob.__class__.__name__ in SUPPORTED_KINDS and not type(ob).__name__ in UNSUPPORTED_KINDS:
            if hasattr(ob, "asdict"): continue
            # print("Converting resource", repr(type(ob).__name__))
            resources.extend(render_object(ob, load_logic_support=load_logic_support)[1:]) # objects rendered in-place, only take additions
    # second pass, as object graph may have been rendered in any order
    for ob in sorted_space: 
        if ob.__class__.__name__ in SUPPORTED_KINDS and not type(ob).__name__ in UNSUPPORTED_KINDS:
            resources.append(ob.asdict)
    return resources

def convert_space_to_yaml(space, wrap_items=False, load_logic_support=True):
    ret = []
    for x in convert_space_to_dict(space, load_logic_support=load_logic_support):
        # print("YAML for", x)
        if wrap_items: x = {"items": [ x ]}
        ret.append(yaml.dump(x))
    return ret

def print_objects_from_yaml(k2):
    for y in convert_space_to_yaml(k2.state_objects, wrap_items=True):
        print(y)
        
def load_yaml(yamlState,k):
    for y in yamlState:
        k.load(y)
    k._build_state()

def getint(poob):
    return int(poob._get_value())

def render_object(ob, load_logic_support=True):
    # TODO: dump priorityClass for controllers (look at their pods' priorities)
    ret_obj = []
    d = { "apiVersion": "v1", # not used
        "kind": str(type(ob).__name__), 
        "metadata": {
            "name": str(ob.metadata_name)
        }
    }
    # Pod
    if str(type(ob).__name__) == "Pod":
        # TODO: add hasDeployment to annotations
        labels = {"service": str(ob.metadata_name)+'-'+str(random.randint(100000000, 999999999))}
        if str(ob.spec_priorityClassName) != "KUBECTL-VAL-NONE":
            if not "spec" in d: d["spec"] = {}
            d["spec"] = {"priorityClassName": str(ob.spec_priorityClassName)}
        if not (ob.priorityClass._property_value == zeroPriorityClass):
            pc = ob.priorityClass._property_value
            if not "spec" in d: d["spec"] = {}
            d["spec"] = {"priorityClassName": str(pc.metadata_name)}
            # maybe add priority number too?
            if not hasattr(pc, "asdict"):
                r = render_object(pc, load_logic_support=load_logic_support)
                ret_obj.append(r[0])
        if ob.atNode._property_value != mnode.Node.NODE_NULL:
            if not "spec" in d: d["spec"] = {}
            node = ob.atNode._property_value
            d["spec"] = {"nodeName": str(node.metadata_name)}
        if ob.targetService._property_value != mservice.Service.SERVICE_NULL:
            serv = ob.targetService._property_value
            if not hasattr(serv, "asdict"):
                labels = {"service": str(serv.metadata_name)+str(random.randint(100000000, 999999999))}
                d_serv = render_object(serv, load_logic_support=load_logic_support)[0]
                if "labels" in d_serv["metadata"]:
                    labels = d_serv["metadata"]["labels"]
                d_serv["metadata"]["labels"] = labels
                serv.asdict = d_serv
            else:
                labels = serv.asdict["metadata"]["labels"]
                # print("skip service")
        if getint(ob.cpuRequest) > -1:
            if not "spec" in d: d["spec"] = {}
            if not "containers" in d["spec"]: 
                d["spec"]["containers"] = [{"resources": 
                                        {"requests": {}}}]
            d["spec"]["containers"][0]["resources"]["requests"]["cpu"] = \
                                    "%sm" % (getint(ob.cpuRequest) * CPU_DIVISOR)
        if getint(ob.memRequest) > -1:
            if not "spec" in d: d["spec"] = {}
            if not "containers" in d["spec"]: 
                d["spec"]["containers"] = [{"resources": 
                                        {"requests": {}}}]
            d["spec"]["containers"][0]["resources"]["requests"]["memory"] = \
                                    "%sMi" % (getint(ob.memRequest) * MEM_DIVISOR)
        if not "labels" in d["metadata"]:
            d["metadata"]["labels"] = labels
        else:
            d["metadata"]["labels"].update(labels)
        if not "status" in d: d["status"] = {}
        d["status"]["phase"] = str(ob.status._get_value())

        # TODO: support to generate limits too!
            
    if str(type(ob).__name__) in [ "DaemonSet" ]: 
        # more like Replicaet than Deployment
        labels = {
            "name": str(ob.metadata_name)+"-"+str(random.randint(100000000, 999999999)),
            "pod-template-hash": str(random.randint(100000000, 999999999)) 
        }
        d["spec"] = {
            "selector": {
                "matchLabels": labels
            },
            "template": {
                "metadata": {
                    "labels": labels
                },
                "spec": {
                    "containers": [
                        {
                            "resources": {
                                # "limits": { },
                                # "requests": { }
                            }
                        }
                    ]
                }
            }
        }
        d["metadata"]["labels"] = {}

        # Dedup objects to circumvent poodle bug
        lpods = ob.podList._get_value()
        dd_lpods = []
        for podOb in lpods:
            found = False
            for p in dd_lpods:
                if str(p.metadata_name) == str(podOb.metadata_name):
                    found = True
                    break
            if found: continue
            dd_lpods.append(podOb)
        assert dd_lpods, "Please add some pods to DaemonSet to infer pod template: %s" % str(ob.metadata_name)

        for podOb in dd_lpods: 
            assert not hasattr(podOb, "asdict")
            d_pod = render_object(podOb, load_logic_support=load_logic_support)[0]
            try:
                pcn = d_pod["spec"]["priorityClassName"]
                d["spec"]["template"]["spec"]["priorityClassName"] = pcn
            except KeyError:
                pass
            try:
                cpum = d_pod["spec"]["containers"][0]["resources"]["requests"]["cpu"]
                d["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"] = cpum
            except KeyError:
                pass
            try:
                memm = d_pod["spec"]["containers"][0]["resources"]["requests"]["memory"]
                d["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["memory"] = memm
            except KeyError:
                pass
            # assert not "labels" in d_pod["metadata"]
            d_pod["metadata"]["labels"].update(labels)
            d_pod["metadata"]["ownerReferences"] = [
                        {
                            "apiVersion": "apps/v1",
                            "controller": True,
                            "kind": str(type(ob).__name__),
                            "name": str(ob.metadata_name)
                        }
                    ]
            labels.update(d_pod["metadata"]["labels"])
            podOb.asdict = d_pod
        d["spec"]["template"]["spec"] = d_pod["spec"]
        d["metadata"]["labels"].update(labels)
 
    if str(type(ob).__name__) in [ "Deployment" ]: 
        labels = {
            "name": str(ob.metadata_name)+"-"+str(random.randint(100000000, 999999999)),
            "pod-template-hash": str(random.randint(100000000, 999999999)) 
        }
        d["spec"] = {
            "selector": {
                "matchLabels": labels
            },
            "template": {
                "metadata": {
                    "labels": labels
                },
                "spec": {
                    "containers": [
                        {
                            "resources": {
                                # "limits": { },
                                # "requests": { }
                            }
                        }
                    ]
                }
            }
        }
        d["metadata"]["labels"] = {}

        # Dedup objects to circumvent poodle bug
        lpods = ob.podList._get_value()
        dd_lpods = []
        for podOb in lpods:
            found = False
            for p in dd_lpods:
                if str(p.metadata_name) == str(podOb.metadata_name):
                    found = True
                    break
            if found: continue
            dd_lpods.append(podOb)
        assert dd_lpods, "Please add some pods to Deployment to infer pod template: %s" % str(ob.metadata_name)

        for podOb in dd_lpods: 
            assert not hasattr(podOb, "asdict")
            d_pod = render_object(podOb, load_logic_support=load_logic_support)[0]
            try:
                pcn = d_pod["spec"]["priorityClassName"]
                d["spec"]["template"]["spec"]["priorityClassName"] = pcn
            except KeyError:
                pass
            try:
                cpum = d_pod["spec"]["containers"][0]["resources"]["requests"]["cpu"]
                d["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"] = cpum
            except KeyError:
                pass
            try:
                memm = d_pod["spec"]["containers"][0]["resources"]["requests"]["memory"]
                d["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["memory"] = memm
            except KeyError:
                pass
            # assert not "labels" in d_pod["metadata"]
            d_pod["metadata"]["labels"].update(labels)
            labels.update(d_pod["metadata"]["labels"])
            podOb.asdict = d_pod
        d["spec"]["template"]["spec"] = d_pod["spec"]
        d["spec"]["replicas"] = getint(ob.spec_replicas)
        d["metadata"]["labels"].update(labels)
        if load_logic_support:
            d2 = { 
                "apiVersion": "v1", # not used
                "kind": "ReplicaSet", 
                "metadata": {
                    "name": str(ob.metadata_name)+"-"+str(random.randint(100000000, 999999999)),
                    "labels": labels,
                    "ownerReferences": [
                        {
                            "apiVersion": "apps/v1",
                            "controller": True,
                            "kind": str(type(ob).__name__),
                            "name": str(ob.metadata_name)
                        }
                    ]
                },
                "spec": {
                    "replicas": getint(ob.spec_replicas),
                    "selector": {
                        "matchLabels": labels
                    },
                    "template": {
                        "metadata": {
                            "labels": labels
                        },
                        "spec": d_pod["spec"]
                    }
                }
            }
            # TODO: add status for ReplicaSets
            ret_obj.append(d2)
    # Service
    if str(type(ob).__name__) == "Service":
        labels = {"service": str(ob.metadata_name)+'-'+str(random.randint(100000000, 999999999))}
        d["spec"] = { "selector": labels }
        d["metadata"]["labels"] = labels
    # Node
    if str(type(ob).__name__) == "Node":
        d["status"] = {
            "allocatable": {
                "cpu": "%sm" % (getint(ob.cpuCapacity) * CPU_DIVISOR),
                "memory": "%sMi" % (getint(ob.memCapacity) * MEM_DIVISOR)
            }
        }
    # PriorityClass
    if str(type(ob).__name__) == "PriorityClass":
        d["value"] = getint(ob.priority)

    if str(type(ob).__name__) == "ReplicaSet":
        d = { 
            "apiVersion": "v1", # not used
            "kind": "ReplicaSet", 
            "metadata": {
                "name": str(ob.metadata_name),
                "labels": 'XXX',
                "ownerReferences": [
                    {
                        "apiVersion": "apps/v1",
                        "controller": True,
                        "kind": str(ob.metadata_ownerReferences__kind),
                        "name": str(ob.metadata_ownerReferences__name)
                    }
                ],
                "spec": {
                    "replicas": getint(ob.spec_replicas),
                    "selector": {
                        "matchLabels": 'XXX'
                    },
                    "template": {
                        "metadata": {
                            "labels": 'XXX'
                        },
                        "spec": 'XXX'
                    }
                }
            }
        }


    ob.asdict = d
    return [d] + ret_obj

def prepare_yamllist_for_diff(ylist: List[str], ignore_replica_set=True, ignore_names=False):
    if ignore_replica_set: ylist = [x for x in ylist if not "ReplicaSet" in x ]
    slist = ''.join([i if not i.isdigit() else "N" for i in repr(ylist).replace("\\n", "\\n\n")])
    if ignore_names:
        slist = re.sub(r'name:.+', 'name: XXX', slist)
    return slist

def checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,test_mode,debug_mode):
    p.run(timeout=200)
    brake = False
    if p.plan:
        for a in assert_conditions:
            if not a in "\n".join([repr(x) for x in p.plan]):
                brake = True
        for a in not_assert_conditions:
            if a in "\n".join([repr(x) for x in p.plan]):
                brake = True
    if not p.plan:
        brake = True
    if not brake:
        if debug_mode:
            print("--- ",test_mode,": Ok")
        else:
            pass
    else:
        if debug_mode:
            print("--- ",test_mode,": Error")
            print_plan(p)
    return  brake

def compare_yaml_files(k,k2):
    yamlState = convert_space_to_yaml(k.state_objects, wrap_items=True)
    yamlState2 = convert_space_to_yaml(k2.state_objects, wrap_items=True)
    if  prepare_yamllist_for_diff(yamlState, ignore_names=True) != \
            prepare_yamllist_for_diff(yamlState2, ignore_names=True):
            print("Yaml file have differences")
            assert prepare_yamllist_for_diff(yamlState, ignore_names=True) == \
                    prepare_yamllist_for_diff(yamlState2, ignore_names=True)
    else:
        print("yaml files are similar")

def checks_assert_conditions(k,k2,p,p2,assert_conditions,not_assert_conditions,debug_mode):
    if debug_mode:
        print("--print_objects--")    
        print("--k1--")    
        print_objects(k.state_objects)
        print("--k2--")
        print_objects(k2.state_objects)
        print("--print_yamls--")    
        print("--k1--")    
        print_objects_from_yaml(k)
        print("--k2--")    
        print_objects_from_yaml(k2)
        # print("---yaml diff ---")
        # compare_yaml_files(k,k2)
        print("--functional test--")    
        test_mode = "functional test"
        test_assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,test_mode,debug_mode)
        if test_assert_brake == False:
            print("OK")
        print_plan(p)

    test_mode = "loading test"
    test_assert_brake = checks_assert_conditions_in_one_mode(k2,p2,assert_conditions,not_assert_conditions,test_mode,debug_mode)
    if debug_mode:
        print_plan(p2)
    if test_assert_brake == True:
        test_mode = "functional test"
        test_assert_brake = checks_assert_conditions_in_one_mode(k,p,assert_conditions,not_assert_conditions,test_mode,debug_mode)
        raise Exception("###  Error loading data   ####")

def reload_cluster_from_yaml(k, create_objects):
    yamlState = convert_space_to_yaml(k.state_objects, wrap_items=True)
    yamlCreate = convert_space_to_yaml(create_objects, wrap_items=False, load_logic_support=False)
    k2 = KubernetesCluster()
    for y in yamlState:
        k2.load(y)
    for y in yamlCreate:
        k2.load(y, mode=KubernetesCluster.CREATE_MODE)
    k2._build_state()
    return k2
