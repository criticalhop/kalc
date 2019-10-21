from tests.libs_for_tests import *
 
print("test_evict")
logger.info("----- test_evict:")


# # @pytest.mark.skip(reason="temporary skip")
# def test_AnyGoal_wo_cli():
#     run_dir_wo_cli(TEST_CLUSTER_FOLDER,   TEST_DAEMONSET)
# @pytest.mark.skip(reason="temporary skip")
# def test_AnyGoal_cli_direct():
#     run_cli_directly(TEST_CLUSTER_FOLDER,   TEST_DAEMONSET)
# # @pytest.mark.skip(reason="temporary skip")
# def test_AnyGoal_cli_invoke():
#     run_cli_invoke(TEST_CLUSTER_FOLDER,   TEST_DAEMONSET)

print("test_has_deployment_creates_daemonset__pods_evicted_pods_pending")
logger.info("----- test_has_deployment_creates_daemonset__pods_evicted_pods_pending:")
def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
@pytest.mark.skip(reason="temporary skip")
def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_cli_direct():
    run_cli_directly(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
# @pytest.mark.skip(reason="temporary skip")
def test_has_deployment_creates_daemonset__pods_evicted_pods_pending_cli_invoke():
    run_cli_invoke(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DAEMONSET_HIGH)
 
print("test_creates_deployment_but_insufficient_resource__pods_pending")
logger.info("----- test_creates_deployment_but_insufficient_resource__pods_pending:")
def test_creates_deployment_but_insufficient_resource__pods_pending_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO)
@pytest.mark.skip(reason="temporary skip")
def test_creates_deployment_but_insufficient_resource__pods_pending_cli_direct():
    run_cli_directly(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO)
# @pytest.mark.skip(reason="temporary skip")
def test_creates_deployment_but_insufficient_resource__pods_pending_cli_invoke():
    run_cli_invoke(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO)
 
print("test_creates_service_and_deployment_insufficient_resource__service_outage")
logger.info("----- test_creates_service_and_deployment_insufficient_resource__service_outage:")
def test_creates_service_and_deployment_insufficient_resource__service_outage_wo_cli():
    run_wo_cli(DUMP1_S1_H_S2_Z_FREE_200,CHANGE_DEPLOYMENT_ZERO_WITH_SERVICE)
@pytest.mark.skip(reason="temporary skip")
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

# Disabled these as they fail linting:
# E: 65,15: Undefined variable 'DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO' (undefined-variable)
# E: 68,21: Undefined variable 'DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO' (undefined-variable)
# E: 71,19: Undefined variable 'DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO' (undefined-variable)
# print("  has_daemonset_creates_deployment__pods_pending_high_severity")
# logger.info("----- has_daemonset_creates_deployment__pods_pending_high_severity:")
# def test_has_daemonset_creates_deployment__pods_pending_high_severity_wo_cli():
#     run_wo_cli(DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO,  CHANGE_DEPLOYMENT_HIGH)
# @pytest.mark.skip(reason="temporary skip")
# def test_has_daemonset_creates_deployment__pods_pending_high_severity_cli_direct():
#     run_cli_directly(DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO,  CHANGE_DEPLOYMENT_HIGH)
# # @pytest.mark.skip(reason="temporary skip")
# def test_has_daemonset_creates_deployment__pods_pending_high_severity_cli_invoke():
#     run_cli_invoke(DUMP_S1_HIGH_PRIORITY_S2_ZERO_PRIORITY_WITH_DAEMONSET_ZERO,  CHANGE_DEPLOYMENT_HIGH)