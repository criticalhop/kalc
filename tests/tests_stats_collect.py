from random import randrange
import os
import re
import glob

comment = "costrange200"
file_for_commit = "./log-current-commit" + "-" + comment
file_for_list_of_reports = "./log_list_of_reports"
file_for_report = "./log_test_stats_all.csv" #+ "-" + comment
report_field_names=['log_id','comment','commit', 'file_name','test_name','lin_count','weight' ,'status','log_name','duration']
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
    "test_1_3pods_Service_outage",\
    "test_5_11pods",\
    "test_20pods",\
    "test_30pods",\
    "test_40pods",\
    "test_8_52pods",\
    "test_9_61pods",\
    "test_10_70pods",\
    "test_10_79pods",\
    "test_11_88pods",\
    "test_12_97pods",\
    "test_13_106pods",\
    "test_14_121pods"    
]

# test_cases = [  
#     "test_6_11pods",\
#     "test_8_52pods",\
#     "test_9_61pods"
# ]

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

# lin_count = "50"
# weight = "1"
# test_file = "test_synthetic_hypothesis_run.py"

# command_to_get_git_commit = "git rev-parse --short HEAD >"+ file_for_commit + "; git branch | grep \* | cut -d ' ' -f2 >> " + file_for_commit
# os.system(command_to_get_git_commit)
# commit_item = ['']
# with open(file_for_commit) as f_commit:
#     commit_item = f_commit.read().splitlines()

# commit_item_inline= ''
# for line in commit_item:
#      commit_item_inline = commit_item_inline + line + '-'

with open(file_for_list_of_reports) as f_report_list:
    log_items_in_db = f_report_list.read().splitlines()

f_report = open(file_for_report,"w")
f_report.write("" + ','.join(map(repr, report_field_names)) + "\r\n")

log_items_in_db_pattern = re.compile(r"\['(.*)', '(.*), '(.*), '(.*)', '(.*)', '(.*)', '(.*)'\]")
 
for log_item_in_db in log_items_in_db:
    m = log_items_in_db_pattern.match(log_item_in_db)
    if m:
        log_id = m.group(1)
        comment = m.group(2)
        commit_item_inline = m.group(3)
        test_file = m.group(4)
        test_name = m.group(5)
        lin_count = m.group(6)
        weight = m.group(7)
        item=[log_id,comment,commit_item_inline, test_file, test_name, lin_count ,weight]
        duration2 = ['0']
        status = "FAILED"
        log_name = "log-" + log_id
        try:
            with open('./'+ log_name) as f:
                lines = f.read().splitlines()
                for a in lines:
                    if "Plan found" in a:
                        status = "PASSED"
                for a in lines:    
                    if "s call     tests/" + test_file + "::" + test_name in a:
                        duration2 = re.findall(r'(\d*)\.', a)
                item.extend([status, duration2[0]])

                f_report.write("" + str(','.join(map(repr, item))) + "\r\n")
                
        except:
            pass