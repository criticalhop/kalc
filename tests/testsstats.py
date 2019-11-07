from random import randrange
import os
import re

test_cases=[["test_36","100","100"],\
                ["test_36","100","20"],\
                ["test_37","100","100"],\
                ["test_37","100","20"],\
                ["test_38","100","100"],\
                ["test_38","100","20"],\
                ["test_39","100","100"],\
                ["test_39","100","20"],\
                ["test_36","100","100"],\
                ["test_36","100","20"],\
                ["test_29","100","100"],\
                ["test_29","100","20"],\
                ["test_30","100","100"],\
                ["test_30","100","20"],\
                ["test_31","100","100"],\
                ["test_31","100","20"],\
                ["test_32","100","100"],\
                ["test_32","100","20"],\
                ["test_33","100","100"],\
                ["test_33","100","20"],\
                ["test_34","100","100"],\
                ["test_34","100","20"],\
                ["test_40","100","100"],\
                ["test_40","100","20"]]#test_name,log_name,lin_count,weight,
for i in test_cases:
    test_name = i[0]
    log_name = "log-"+i[0]+"-"+i[1]+"-"+i[2]
    lin_count = i[1] 
    weight = i[2]
    port = randrange(10000, 10101, 1) 
    template = "POODLE_LIN_COUNT={} POODLE_ASTAR_WEIGHT={} PYTHON=pypy POODLE_SOLVER_URL=http://localhost:{} tox -e poodledev -- -s ./tests/test_scenarios_synthetic.py::{} > {}"
    bashCommand = template.format(lin_count,weight,port, test_name,log_name)
    os.system(bashCommand)
    with open('./'+ log_name) as f:
        lines = f.read().splitlines()
    for a in lines:    
        if "s call     tests/test_scenarios_synthetic.py::"+test_name in a:
            duration2 = re.findall(r'(\d*)\.', a)
            print('test_name', test_name,'lin_count', lin_count,'weight',weight, 'duration', duration2[0])