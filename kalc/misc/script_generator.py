import subprocess
import json
from kalc.model.kinds.Node import Node

def move_pod_with_deployment_script(pod, node_to: Node, deployment, replicaset):
    "Move the pod when the pod is part of Deployment"
    # 1. Dump full original Deployment
    deployment_name = str(deployment.metadata_name)
    replicaset_name = str(replicaset.metadata_name)
    pod_original_name = str(pod.metadata_name)
    pod_new_name = f"{pod_original_name}-kalcmoved"
    all_node_labels = {}
    for label in node_to.metadata_labels:
        all_node_labels[label.key] = label.value

    nodeSelector_json = json.dumps(all_node_labels)

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
    echo "Disabling relevant controllers by backing up and temporarily deleting them..."
    kubectl get deployment/{deployment_name} -o=yaml > ./deployment_{deployment_name}.yaml &&
    kubectl delete --cascade=false deployment/{deployment_name} &&
    kubectl get replicaset/{replicaset_name} -o=yaml > ./replicaset_{replicaset_name}.yaml &&
    kubectl delete --cascade=false replicaset/{replicaset_name} &&
    echo "Storing current version of pod config of the pod-to-be-moved..." &&
    kubectl get pod/{pod_original_name} -o=yaml > ./pod_new.yaml &&
    echo "Renaming pod template..." &&
    yq '.metadata += {{name: "{pod_new_name}"}}' ./pod_new.yaml > ./pod_new.yaml.$$ && mv ./pod_new.yaml.$$ pod_new.yaml &&
    echo "Deleting status from dump..." &&
    yq 'del(.status)' ./pod_new.yaml > ./pod_new.yaml.$$ && mv ./pod_new.yaml.$$ pod_new.yaml &&
    echo "Inserting nodeSelector..." &&
    yq '.spec += {{nodeSelector: {nodeSelector_json}}}' ./pod_new.yaml > ./pod_new.yaml.$$ && mv ./pod_new.yaml.$$ pod_new.yaml &&
    echo "Running new pod..." &&
    kubectl apply -f ./pod_new.yaml &&
    echo "Waiting for new pod to become ready..." &&
    kubectl wait --for condition=ready -f ./pod_new.yaml &&
    echo "Deleting original pod..." &&
    kubectl delete pod/{pod_original_name}
    echo "Re-applying ReplicaSet..." &&
    kubectl apply -f ./replicaset_{replicaset_name}.yaml &&
    echo "Re-applying Deployment..." &&
    kubectl apply -f ./deployment_{deployment_name}.yaml &&
    echo "Done moving pod '{pod_original_name}'!"
    """
    return move_pod

def generate_compat_header():
    "Generate script header for checking if correct tools are installed"

    # Compatibility and installed utilities part

    compat = """
    # Checking for tools
    echo "Checking for kubectl..." && kubectl > /dev/null || (echo "sed not found" && exit 1)
    echo "Checking for jq..." && jq --version | grep -q jq- || (echo "jq not found or not compatible. Install with 'apt install jq'" && exit 1)
    echo "Checking for yq..." && yq --version 2>&1 | grep -q "yq 2" || (echo "yq not found or not compatible" && exit 1)
    echo "Checking for sed..." && sed || (echo "sed not found" && exit 1)
    echo -n "Checking for kubectl get permission for deployment... " && kubectl auth can-i get deployment || (echo "kubectl does not have permission to get deployments" && exit 1)
    echo -n "Checking for kubectl get permission for replicaset... " && kubectl auth can-i get replicaset || (echo "kubectl does not have permission to get replicaset" && exit 1)
    echo -n "Checking for kubectl get permission for pod... " && kubectl auth can-i get pod || (echo "kubectl does not have permission to get pod" && exit 1)
    echo -n "Checking for kubectl apply permission for deployment... " && kubectl auth can-i apply deployment || (echo "kubectl does not have permission to apply deployments" && exit 1)
    echo -n "Checking for kubectl apply permission for replicaset... " && kubectl auth can-i apply replicaset || (echo "kubectl does not have permission to apply replicaset" && exit 1)
    echo -n "Checking for kubectl apply permission for pod... " && kubectl auth can-i get apply || (echo "kubectl does not have permission to apply pod" && exit 1)
    """

    return compat