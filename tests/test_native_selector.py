pod_str="""apiVersion: v1
items:
- apiVersion: v1
kind: Pod
 metadata:
    generateName: redis-master-57fc67768d-
    labels:
      app: redis
      pod-template-hash: 57fc67768d
      role: master
      tier: backend
    name: redis-master-57fc67768d-2xc2q-2
    namespace: default
  spec:
    containers:
    - image: k8s.gcr.io/redis: e2e
    resources:
        requests:
          cpu: 100m
          memory: 100Mi
    nodeName: gke-tesg1-default-pool-ff7a1295-7kwg
- apiVersion: v1
kind: Pod
 metadata:
    generateName: redis-master-57fc67768d-bad
    labels:
      app: redis-bad
      pod-template-hash: 57fc67768d
      role: master
      tier: backend
    name: redis-master-fdsfsdfsddsf
    namespace: default
  spec:
    containers:
    - image: k8s.gcr.io/redis: e2e
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