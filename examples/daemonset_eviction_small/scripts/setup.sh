kubectl config view | grep "cluster:"
kubectl config use-context gke_closercriticalhop_us-central1-a_testspace
kubectl config set-context --current --namespace=default