from kalc.model.kinds.Service import Service
from kalc.model.kinds.Pod import Pod
import pytest
from kalc.model.kubernetes import KubernetesCluster

pod_str="""apiVersion: v1
items:
- apiVersion: v1
  kind: Pod
  metadata:
    labels:
      app: redis
      pod-template-hash: 57fc67768d
      role: master
      tier: backend
    name: redis-master-57fc67768d-2xc2q-2
    namespace: default
  spec:
    containers:
    - image: k8s.gcr.io/redis:e2e
      resources:
        requests:
          cpu: 100m
          memory: 100Mi
    nodeName: gke-tesg1-default-pool-ff7a1295-7kwg
- apiVersion: v1
  kind: Pod
  metadata:
    labels:
      app: redis-bad
      pod-template-hash: 57fc67768d
      role: master
      tier: backend
    name: redis-master-fdsfsdfsddsf
    namespace: default
  spec:
    containers:
    - image: k8s.gcr.io/redis:e2e
      resources:
        requests:
          cpu: 100m
          memory: 100Mi
    nodeName: gke-tesg1-default-pool-bad
kind: List
metadata:
  resourceVersion: ""
  selfLink: ""
"""
service_str="""apiVersion: v1
items:
- apiVersion: v1
  kind: Service
  metadata:
    labels:
      service: myservice
    name: redis-master
    namespace: default
  spec:
    selector:
      app: redis
      role: master
    sessionAffinity: None
- apiVersion: v1
  kind: Service
  metadata:
    labels:
      service: broken-service
    name: redis-master-evict
    namespace: default
  spec:
    selector:
      app: redis-evict
      role: master
kind: List
metadata:
  resourceVersion: ""
  selfLink: ""
"""
def test_native_selector_service_to_pod():
    k = KubernetesCluster()
    k.load(pod_str)
    k.load(service_str)
    k._build_state()

    for s in filter(lambda x: isinstance(x, Service), k.state_objects):
        if str(s.metadata_name._get_value()) == "redis-master":
            assert len(s.podList._get_value()) == 1 
        else:
            assert len(s.podList._get_value()) == 0
