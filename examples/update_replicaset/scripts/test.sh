kubectl apply -f ../current_state.yaml
sleep 10
kubectl get deployments
rm -R ../cluster_dump/
mkdir ../cluster_dump
kubectl get po -o yaml > ../cluster_dump/pods.yaml --all-namespaces
kubectl get no -o yaml > ../cluster_dump/nodes.yaml --all-namespaces
kubectl get services -o yaml > ../cluster_dump/service.yaml 
kubectl get priorityclass -o yaml > ../cluster_dump/priorityclass.yaml --all-namespaces
kubectl val -d ../cluster_dump/ -f ../incomming_change.yaml