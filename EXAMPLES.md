# Testing examples:
  
## Prepare test cluster

Create cluster: For this test create cluster with 2 nodes, each with 3.75 RAM and 1 CPU

Use following commands:
```bash
gcloud container clusters create your-testspace-cluster
kubectl config view
kubectl config use-context your-testspace-cluster
kubectl config set-context --current --namespace=default
```

List of test examples directories in directory EXAMPLES:

* daemonset_eviction_small

  

## Run
Open directory with exaple and run commands to perform test (replace cluster name in commands below with name of your cluster):

```python
kubectl apply -f ./deployments.yaml
sleep 10
kubectl get deployments
mkdir ./cluster_dump
kubectl get po -o yaml > ./cluster_dump/pods.yaml
kubectl get no -o yaml > ./cluster_dump/nodes.yaml
kubectl get services -o yaml > ./cluster_dump/service.yaml
kubectl get priorityclass -o yaml > ./cluster_dump/priorityclass.yaml
kubectl check -d ./cluster_dump/ -f ./daemonset_create.yaml
```

To make sure that scenario found could happen , please run commands below to setup daemonset :
```python
kubectl apply -f ./daemonset_create.yaml
```

## Clean up

To Clean up exaples data from "testspace" cluster run this:

```python
kubectl delete deployment redis-master redis-master-2 redis-slave redis-slave-unlimit-norequest redis-slave-unlimit-norequest-2 redis-master-evict  
kubectl delete priorityclass name = high-priority
kubectl delete daemonset fluentd-elasticsearch
rm -R ./cluster_dump/
sleep 10
kubectl get pods
```

Make sure no resources found.
