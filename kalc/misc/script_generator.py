import subprocess
import json
from kalc.model.kinds.Node import Node
import kalc.model.kinds.ReplicaSet as rs
import kalc.model.kinds.Deployment as d
import time

def script_remove_node(node):
    if hasattr(node, "_variable_mode") and node._variable_mode: 
        return "" # FIX for https://github.com/criticalhop/poodle/issues/59
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


def move_pod_with_deployment_script_simple(pod, node_to: Node, object_space):
    if hasattr(pod, "_variable_mode") and pod._variable_mode: 
        return "" # FIX for https://github.com/criticalhop/poodle/issues/59
    d = get_deployment_from_pod(pod, object_space)
    return move_pod_with_deployment_script(pod, node_to, d,
        get_rs_from_deployment(d, object_space))


def move_pod_with_deployment_script(pod, node_to: Node, deployment, replicaset):
    "Move the pod when the pod is part of Deployment"
    # 1. Dump full original Deployment
    deployment_name = str(deployment.metadata_name)
    deployment_namespace = deployment.metadata_namespace._get_value()
    replicaset_name = str(replicaset.metadata_name)
    replicaset_namespace =  replicaset.metadata_namespace._get_value()
    pod_original_name = str(pod.metadata_name)
    pod_namespace =  pod.metadata_namespace._get_value()
    pod_new_name = f"{pod_original_name}-kalcmoved-" + str(time.time())

    assert pod_namespace == deployment_namespace, "{0}({1}) == {2}({3})".format(pod_namespace, pod_original_name, deployment_namespace, deployment_name)
    assert pod_namespace == replicaset_namespace, "{0}({1}) == {2}({3})".format(pod_namespace, pod_original_name,replicaset_namespace, replicaset_name)
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

    # Compatibility and installed utilities part

    compat = """#!/bin/bash
die() { echo "$*" 1>&2 ; exit 1; }

# Checking for tools
echo "Checking for kubectl..." && kubectl > /dev/null || die "sed not found" 
echo "Checking for jq..." && jq --version | grep -q jq- || die "jq not found or not compatible. Install with 'apt install jq'" 
echo "Checking for yq..." && yq --version 2>&1 | grep -q "yq 2" || die "yq not found or not compatible" 
echo "Checking for sed..." && sed --version >/dev/null 2> /dev/null || die "sed not found"
echo -n "Checking for kubectl get permission for deployment... " && kubectl auth can-i get deployment || die "kubectl does not have permission to get deployments" 
echo -n "Checking for kubectl get permission for replicaset... " && kubectl auth can-i get replicaset || die "kubectl does not have permission to get replicaset" 
echo -n "Checking for kubectl get permission for pod... " && kubectl auth can-i get pod || die "kubectl does not have permission to get pod" 
echo -n "Checking for kubectl apply permission for deployment... " && kubectl auth can-i apply deployment || die "kubectl does not have permission to apply deployments" 
echo -n "Checking for kubectl apply permission for replicaset... " && kubectl auth can-i apply replicaset || die "kubectl does not have permission to apply replicaset" 
echo -n "Checking for kubectl apply permission for pod... " && kubectl auth can-i apply pod || (echo "kubectl does not have permission to apply pod" && exit 1) """

    return compat