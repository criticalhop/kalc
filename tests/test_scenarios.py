from tests.libs_for_tests import *
import pytest
pytestmark = pytest.mark.skip # TODO DELETEME
 
# # @pytest.mark.skip(reason="temporary skip")
# def test_OptimisticRun_wo_cli():
#     run_dir_wo_cli(TEST_CLUSTER_FOLDER,   TEST_DAEMONSET)
# @pytest.mark.skip(reason="temporary skip")
# def test_OptimisticRun_cli_direct():
#     run_cli_directly(TEST_CLUSTER_FOLDER,   TEST_DAEMONSET)
# # @pytest.mark.skip(reason="temporary skip")
# def test_OptimisticRun_cli_invoke():
#     run_cli_invoke(TEST_CLUSTER_FOLDER,   TEST_DAEMONSET)

print("test_has_deployment_creates_daemonset__pods_evicted_pods_pending")

def test_1_step_1_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
    
def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
@pytest.mark.debug(reason="temporary skip")
def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_cli_direct():
    run_cli_directly(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
# @pytest.mark.skip(reason="temporary skip")
def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_cli_invoke():
    run_cli_invoke(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
 
print("test_creates_deployment_but_insufficient_resource__pods_pending")
def test_creates_deployment_but_insufficient_resource__pods_pending_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO)
@pytest.mark.debug(reason="temporary skip")
def test_creates_deployment_but_insufficient_resource__pods_pending_cli_direct():
    run_cli_directly(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO)
# @pytest.mark.skip(reason="temporary skip")
def test_creates_deployment_but_insufficient_resource__pods_pending_cli_invoke():
    run_cli_invoke(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO)
 
print("test_creates_service_and_deployment_insufficient_resource__service_outage")
def test_creates_service_and_deployment_insufficient_resource__service_outage_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO_WITH_SERVICE)
@pytest.mark.debug(reason="temporary skip")
def test_creates_service_and_deployment_insufficient_resource__service_outageg_cli_direct():
    run_cli_directly(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO_WITH_SERVICE)
# @pytest.mark.skip(reason="temporary skip")
def test_creates_service_and_deployment_insufficient_resource__service_outage_cli_invoke():
    run_cli_invoke(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO_WITH_SERVICE)


print(" has_deployment_creates_deployment__pods_evicted_pods_pending")
logger.info("----- has_deployment_creates_deployment__pods_evicted_pods_pending:")
def test_has_deployment_creates_deployment__pods_evicted_pods_pending_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_HIGH)
@pytest.mark.skip(reason="temporary skip")
def test_has_deployment_creates_deployment__pods_evicted_pods_pending_cli_direct():
    run_cli_directly(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_HIGH)
# @pytest.mark.skip(reason="temporary skip")
def test_has_deployment_creates_deployment__pods_evicted_pods_pending_cli_invoke():
    run_cli_invoke(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_HIGH)


# print("  has_daemonset_creates_deployment__pods_pending_high_severity")
# #Customer has a DaemonSet, creates a Deployment with higher priority, 
# # one of the pods for DaemonSet gets evicted => we detect a high-severity 
# # issue (because DaemonSet only has 1 pod per node working)

# def test_has_daemonset_creates_deployment__pods_pending_high_severity_wo_cli():
#     run_wo_cli(DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO,  CHANGE_DEPLOYMENT_HIGH)
# @pytest.mark.skip(reason="temporary skip")
# def test_has_daemonset_creates_deployment__pods_pending_high_severity_cli_direct():
#     run_cli_directly(DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO,  CHANGE_DEPLOYMENT_HIGH)
# # @pytest.mark.skip(reason="temporary skip")
# def test_has_daemonset_creates_deployment__pods_pending_high_severity_cli_invoke():
#     run_cli_invoke(DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO,  CHANGE_DEPLOYMENT_HIGH)