PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3289 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_synthetic_start_pod_with_scheduler > log-12
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3289 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_evict_and_killpod_with_deployment_and_service > log-13
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3189 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_2_synthetic_service_outage_step2 > log-14-2
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3289 tox -e poodledev -- ./tests/test_scenarios_synthetic.py > log-synth
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3189 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_2_synthetic_service_outage_step4 > log-14-4


PYTHON=pypy POODLE_SOLVER_URL=http://localhost:10003 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_0_run_pods_no_eviction_invload > log-synt-0
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:10003 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_2_synthetic_service_outage_invload > log-synt-2
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:10003 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_3_synthetic_service_outage_multi_invload > log-synt-3
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:10003 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_4_synthetic_service_NO_outage_multi > log-synt-4
