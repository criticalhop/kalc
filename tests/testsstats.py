from random import randrange
import os
import re

file_for_commit = "./log-current-commit"
file_for_report = "./log_test_stats.txt"
comment = "branch-makarty-29"
test_cases=[["test_36","100","100"],\
                ["test_36","100","20"],\
                ["test_37","100","100"],\
                ["test_37","100","20"],\
                ["test_38","100","100"],\
                ["test_38","100","20"],\
                ["test_39","100","100"],\
                ["test_39","100","20"],\
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
                ["test_40","100","20"]]#test_name,lin_count,weight,

command_to_get_git_commit = "git rev-parse --short HEAD > " + file_for_commit
os.system(command_to_get_git_commit)
with open(file_for_commit) as f_commit:
    commit_item = f_commit.read()

f_report = open(file_for_report,"a+")
f_report.write('testet commit: '+ commit_item)
print(commit_item)

for i in test_cases:
    test_name = i[0]
    log_name = "log-"+i[0]+"-"+i[1]+"-"+i[2]+"-"+comment
    lin_count = i[1] 
    weight = i[2]
    port = randrange(10000, 10101, 1) 

    template = "POODLE_LIN_COUNT={} POODLE_ASTAR_WEIGHT={} PYTHON=pypy POODLE_SOLVER_URL=http://localhost:{} tox -e poodledev -- -s ./tests/test_scenarios_synthetic.py::{} > {}"
    bashCommand = template.format(lin_count,weight,port, test_name,log_name)
    print('test_name, '+ test_name +', lin_count, '+ lin_count + ', weight ,'+ weight)
    os.system(bashCommand)
    with open('./'+ log_name) as f:
        lines = f.read().splitlines()
    for a in lines:    
        if "s call     tests/test_scenarios_synthetic.py::"+test_name in a:
            duration2 = re.findall(r'(\d*)\.', a)
            stats_item = 'test_name, '+ test_name +', lin_count, '+ lin_count + ', weight ,'+ weight+', duration, '+ duration2[0]
            f_report.write(stats_item +"\r\n")
            print(stats_item)