import subprocess
import json
from kalc.model.kinds.Node import Node
import kalc.model.kinds.ReplicaSet as rs
import kalc.model.kinds.Deployment as d
from kalc.misc.metrics import Metric
import time


def script_remove_node(node, object_space):
    if hasattr(node, "_variable_mode") and node._variable_mode: 
        return ""  # FIX for https://github.com/criticalhop/poodle/issues/59
    metric = next(filter(lambda x: isinstance(x, Metric), object_space))
    metric.drained_node_set.add(node)
    return f'echo "Please remove node \'{str(node.metadata_name)}\'"' 


def get_rs_from_deployment(deployment, object_space):
    replicasets = filter(lambda x: isinstance(x, rs.ReplicaSet), object_space)
    for replicaset in replicasets:
        if replicaset.metadata_ownerReferences__name == deployment.metadata_name:
            return replicaset
    raise ValueError("Can not find ReplicaSet")


def get_deployment_from_pod(pod, object_space):
    deployments = filter(lambda x: isinstance(x, d.Deployment), object_space)
    for deployment in deployments:
        if pod in deployment.podList:
            return deployment 
    return None


def move_pod_with_deployment_script_simple(pod, node_from: Node, node_to: Node, object_space):
    if hasattr(pod, "_variable_mode") and pod._variable_mode: 
        return "" # FIX for https://github.com/criticalhop/poodle/issues/59
    d = get_deployment_from_pod(pod, object_space)
    metric = next(filter(lambda x: isinstance(x, Metric), object_space))
    metric.moved_pod_set.add(pod)
    metric.touched_node_set.add(node_to)
    metric.touched_node_set.add(node_from)
    return move_pod_with_deployment_script(pod, node_to, d,
        get_rs_from_deployment(d, object_space))


def print_metric(value: float, metric_name: str):
    utilisation = value 
    metric_info = f"""echo {metric_name} {utilisation:.1f}
"""
    return metric_info

def print_stats(metric: Metric, metric_name: str):
    metric_info = ""
    if len(metric.drained_node_set) > 0:
        metric_info += f"""echo Node drained {len(metric.drained_node_set)}
"""
    if len(metric.moved_pod_set) > 0:
        metric_info += f"""echo Pod moved {len(metric.moved_pod_set)}
"""
    if metric.run_time > 0:
        metric_info += f"""echo Run time {metric.run_time}
"""
    if len(metric.pods) > 0:
        metric_info += f"""echo Pod amount {len(metric.pods)}
"""
    if len(metric.nodes) > 0:
        metric_info += f"""echo Node amount {len(metric.nodes)}
"""
    return metric_info


def move_pod_with_deployment_script(pod, node_to: Node, deployment, replicaset):
    "Move the pod when the pod is part of Deployment"
    # 1. Dump full original Deployment
    deployment_name = str(deployment.metadata_name)
    deployment_namespace = deployment.metadata_namespace._get_value()
    replicaset_name = str(replicaset.metadata_name)
    replicaset_namespace =  replicaset.metadata_namespace._get_value()
    pod_original_name = str(pod.metadata_name)
    pod_namespace =  pod.metadata_namespace._get_value()
    pod_new_name = f"{pod_original_name}-kalcmoved-" + str(int(time.time()))

    assert str(pod_namespace) == str(deployment_namespace), "{0}({1}) == {2}({3})".format(pod_namespace, pod_original_name, deployment_namespace, deployment_name)
    assert str(pod_namespace) == str(replicaset_namespace), "{0}({1}) == {2}({3})".format(pod_namespace, pod_original_name, replicaset_namespace, replicaset_name)
    namespace = pod_namespace

    if namespace is None:
        namespace = 'default'
    
    # TODO: check that pod that we are deleting had a full green-light status (alive&ready)
    # TODO: check if state has diverged too far and we can not continue
    # TODO: explicily prohibit moving singleton pods... except allowed explicitly
    # TODO: namespace support

    # TODO: dry run mode!! - default mode
    # TODO: move fake pod - test mode
    # TODO: move smth unimportant
    # TODO: execute mode
    # TODO: paranoid checks: that deployment does not get re-created
    
    from kalc.interactive import cluster_md5_sh, md5_cluster

    move_pod = f"""

echo "Moving pod '{pod_original_name}'..."
echo " -- Disabling relevant controllers by backing up and temporarily deleting them..."
kubectl get deployment/{deployment_name} --namespace={namespace} -o=yaml > ./deployment_{deployment_name}.yaml &&
kubectl delete --cascade=false deployment/{deployment_name} --namespace={namespace} &&
kubectl get replicaset/{replicaset_name} --namespace={namespace} -o=yaml > ./replicaset_{replicaset_name}.yaml &&
kubectl delete --cascade=false replicaset/{replicaset_name} --namespace={namespace} &&
echo " -- Storing current version of pod config of the pod-to-be-moved..." &&
kubectl get pod/{pod_original_name} --namespace={namespace} -o=yaml > ./pod_new.yaml &&
echo "  --- Renaming pod template..." &&
yq '.metadata += {{name: "{pod_new_name}"}}' ./pod_new.yaml > ./pod_new.yaml.$$ && mv ./pod_new.yaml.$$ pod_new.yaml &&
echo "  --- Deleting status from dump..." &&
yq 'del(.status)' ./pod_new.yaml > ./pod_new.yaml.$$ && mv ./pod_new.yaml.$$ pod_new.yaml &&
echo "  --- Inserting nodeName..." &&
yq '.spec += {{nodeName: "{str(node_to.metadata_name)}"}}' ./pod_new.yaml > ./pod_new.yaml.$$ && mv ./pod_new.yaml.$$ pod_new.yaml &&
echo " -- Running new pod..." &&
kubectl apply -f ./pod_new.yaml &&
echo " -- Waiting 30s for new pod to become ready..." &&
kubectl wait --for condition=ready --namespace={namespace} -f ./pod_new.yaml &&
echo " -- Deleting original pod..." &&
kubectl delete pod/{pod_original_name} --namespace={namespace}
echo " -- Re-applying ReplicaSet..." &&
kubectl apply -f ./replicaset_{replicaset_name}.yaml &&
echo " -- Re-applying Deployment..." &&
kubectl apply -f ./deployment_{deployment_name}.yaml &&
echo "Done moving pod '{pod_original_name}'!" """
    return move_pod

def generate_compat_header():
    "Generate script header for checking if correct tools are installed"
    
    from kalc.interactive import cluster_md5_sh, md5_cluster

    # Compatibility and installed utilities part

    compat = f"""#!/bin/bash
die() {{ echo "$*" 1>&2 ; exit 1; }}

# Checking for tools
echo "Checking for kubectl..." && kubectl > /dev/null || die "sed not found" 
echo "Checking for jq..." && jq --version | grep -q jq- || die "jq not found or not compatible. Install with 'apt install jq'" 
echo "Checking for yq..." && yq --version 2>&1 | grep -q "yq 2" || die "yq not found or not compatible" 
echo "Checking for sed..." && sed --version >/dev/null 2> /dev/null || die "sed not found"
echo "Checking for awk..." && awk --version >/dev/null 2> /dev/null || die "awk not found"
echo -n "Checking for kubectl get permission for deployment... " && kubectl auth can-i get deployment || die "kubectl does not have permission to get deployments" 
echo -n "Checking for kubectl get permission for replicaset... " && kubectl auth can-i get replicaset || die "kubectl does not have permission to get replicaset" 
echo -n "Checking for kubectl get permission for pod... " && kubectl auth can-i get pod || die "kubectl does not have permission to get pod" 
echo -n "Checking for kubectl apply permission for deployment... " && kubectl auth can-i apply deployment || die "kubectl does not have permission to apply deployments" 
echo -n "Checking for kubectl apply permission for replicaset... " && kubectl auth can-i apply replicaset || die "kubectl does not have permission to apply replicaset" 
echo -n "Checking for kubectl apply permission for pod... " && kubectl auth can-i apply pod || (echo "kubectl does not have permission to apply pod" && exit 1)

CLUSTER_MD5={md5_cluster}
CLUSTER_MD5_current=`{cluster_md5_sh} | awk ' {{printf $1}} ' `
if [ "$CLUSTER_MD5" !=  "$CLUSTER_MD5_current" ] ;
then
 echo "WARNING: CLUSTER STATE DIVERGED - USE AT YOUR OWN RISK"
  finish="1"
  if [ "$1" != "-y" ];
  then
    echo  -n "Are you going to continue?  [yes/no]? "
    read answer
    finish="-1"
  fi
  while [ "$finish" = '-1' ]
  do
    finish="1"
    if [ "$answer" = '' ];
    then
      answer=""
    else
      case $answer in
        yes | YES ) answer="y";;
        no | NO ) exit 0 ;;
        *) finish="-1";
           echo -n 'Invalid !!! Please enter "yes" or "no" :';
           read answer;;
       esac
    fi
  done
fi
"""
    return compat
