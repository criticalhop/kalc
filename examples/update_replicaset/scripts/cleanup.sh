kubectl delete --all deployments --namespace=default
kubectl delete priorityclass  high-priority  --namespace=default
kubectl delete --all daemonsets --namespace=default 
rm -R ../cluster_dump/
sleep 20
kubectl get pods