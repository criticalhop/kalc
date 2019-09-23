# Testing examples:
  ./tests/daemonset_eviction_small
## Use-case daemonset_eviction_small

0. Create cluster: For this test create cluster with 2 nodes, each with 3.75 RAM and 1 CPU
1. To create cluster one should setup template in the Google cloud platform
Once default template is setup and use following script to create a cluster: 'bash ./create_cluster.sh'
3. Update script 'setup.sh' with corresponing cluster name instead of 'testspace'. 
4. Run "bash run_test.sh"   

Make sure no resources found.

## Use-case nopods_for_service

0. Create cluster: For this test create cluster with 2 nodes, each with 3.75 RAM and 1 CPU
1. To create cluster one should setup template in the Google cloud platform
Once default template is setup and use following script to create a cluster: 'bash ./create_cluster.sh'
3. Update script 'setup.sh' with corresponing cluster name instead of 'testspace'. 
4. Run "bash run_test.sh"   

Make sure no resources found.