PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3289 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_synthetic_start_pod_with_scheduler > log-12
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3289 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_evict_and_killpod_with_deployment_and_service > log-13
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3189 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_2_synthetic_service_outage_step2 > log-14-2
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3289 tox -e poodledev -- ./tests/test_scenarios_synthetic.py > log-synth
PYTHON=pypy POODLE_SOLVER_URL=http://localhost:3189 tox -e poodledev -- ./tests/test_scenarios_synthetic.py::test_2_synthetic_service_outage_step4 > log-14-4


