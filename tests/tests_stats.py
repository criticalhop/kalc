from random import randrange
import os
import re

comment = ""
file_for_commit = "./log-current-commit" + "-" + comment
file_for_report = "./log_test_stats" #+ "-" + comment
# test_cases=["test_38","test_41","test_42","test_43","test_44","test_45","test_46","test_47","test_48"]
# test_cases=["test_36","test_37","test_38","test_39","test_29","test_30","test_31","test_32","test_33","test_34","test_40"]
# test_cases = [  "test_50_7pods",\
#                 "test_51_11pods",\
#                 "test_52_14pods",\
#                 "test_53_17pods",\
#                 "test_54_25pods",\
#                 "test_55_31pods",\
#                 "test_56_7pods",\
#                 "test_57_11pods",\
#                 "test_58_15pods",\
#                 "test_59_25pods",\
#                 "test_60_31pods",\
#                 "test_61_28pods",\
#                 "test_62_32pods",\
#                 "test_63_34pods",\
#                 "test_64_35pods",\
#                 "test_65_28pods",\
#                 "test_66_30pods",\
#                 "test_67_32pods",\
#                 "test_68_34pods",\
#                 "test_69_7pods_1node",\
#                 "test_70_11pods_1node",\
#                 "test_71_15pods_1node",\
#                 "test_72_25pods_1node",\
#                 "test_73_31pods_1node"
#                 ]
test_cases = [  "test_53_17pods",\
                "test_54_25pods",\
                "test_55_31pods",\
                "test_56_7pods",\
                "test_57_11pods",\
                "test_58_15pods",\
                "test_59_25pods",\
                "test_60_31pods",\
                "test_61_28pods",\
                "test_62_32pods",\
                "test_63_34pods",\
                "test_64_35pods",\
                "test_65_28pods",\
                "test_66_30pods",\
                "test_67_32pods",\
                "test_68_34pods",\
                "test_69_7pods_1node",\
                "test_70_11pods_1node",\
                "test_71_15pods_1node",\
                "test_72_25pods_1node",\
                "test_73_31pods_1node"
                ]

test_cases = [  
    "test_6_11pods",\
    "test_8_52pods",\
    "test_9_61pods",\
    "test_10_70pods",\
    "test_10_79pods",\
    "test_11_88pods",\
    "test_12_97pods",\
    "test_13_106pods",\
    "test_14_121pods"    
]

test_cases = [  
    "test_6_11pods",\
    "test_8_52pods",\
    "test_9_61pods"
]

# test_cases = [  
#     "test_10_70pods",\
#     "test_10_79pods",\
#     "test_11_88pods"
# ]

# test_cases = [  
#     "test_12_97pods",\
#     "test_13_106pods",\
#     "test_14_121pods"    
# ]

lin_count = "70"
weight = "1"

command_to_get_git_commit = "git rev-parse --short HEAD >"+ file_for_commit + "; git branch | grep \* | cut -d ' ' -f2 >> " + file_for_commit
os.system(command_to_get_git_commit)
commit_item = ['']
with open(file_for_commit) as f_commit:
    commit_item = f_commit.read().splitlines()

commit_item_inline= ''
for line in commit_item:
     commit_item_inline = commit_item_inline + line + '-'

f_report = open(file_for_report,"a+")
# f_report.write('tested commit: '+ commit_item_inline +"\r\n")
# f_report.write('comment: ' + comment +"\r\n")
print(commit_item_inline)
print(comment,'lin_count',lin_count,'weight',weight)



for i in test_cases:
    test_name = i
    log_name = "log-" + comment + "-" + commit_item_inline + "-" + i + "-" + lin_count + "-" + weight
    port = randrange(10000, 10101, 1) 
    template = "POODLE_LIN_COUNT={} POODLE_ASTAR_WEIGHT={} PYTHON=pypy POODLE_SOLVER_URL=http://localhost:{} tox -e poodledev -- -s ./tests/test_synthetic_hypothesis_run.py::{} > {}"
    bashCommand = template.format(lin_count,weight,port, test_name,log_name)
    os.system(bashCommand)
    duration2 = ['0']
    status = "FAILED"
    with open('./'+ log_name) as f:
        lines = f.read().splitlines()
    for a in lines:
        if "PASSED" in a:
            status = "PASSED"
    for a in lines:
        if "Empty plan" in a:
            status = "FAILED"
    for a in lines:    
        if "s call     tests/test_synthetic_masstest.py::"+test_name in a:
            duration2 = re.findall(r'(\d*)\.', a)
    stats_item = comment + ' ' + commit_item_inline + ', test_name, '+ test_name +', lin_count, '+ lin_count + ', weight ,' + weight + ', status,' + status + ', log_name,' + log_name +', duration, '+ duration2[0]
    f_report.write("" + stats_item + "\r\n")
    print(stats_item)