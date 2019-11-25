from random import randrange
import os
import re
import glob

file_for_list_of_reports = "./log_list_of_reports"
file_for_report = "./log_test_stats_all.csv" 
report_field_names=['log_id','comment','commit',"poodle_commit" ,'file_name','test_name','lin_count','weight' ,'timeout','status','duration']

with open(file_for_list_of_reports) as f_report_list:
    log_items_in_db = f_report_list.read().splitlines()

f_report = open(file_for_report,"w")
f_report.write("" + ','.join(map(repr, report_field_names)) + "\r\n")

log_items_in_db_pattern = re.compile(r"\['(.*)', '(.*), '(.*), '(.*)', '(.*)', '(.*)', '(.*), '(.*), (.*)\]")
 
for log_item_in_db in log_items_in_db:
    m = log_items_in_db_pattern.match(log_item_in_db)
    if m:
        log_id = m.group(1)
        comment = m.group(2)
        commit_item_inline = m.group(3)
        commit_poodle_item_inline = m.group(4)
        test_file = m.group(5)
        test_name = m.group(6)
        lin_count = m.group(7)
        weight = m.group(8)
        timeout = m.group(9)
        item=[log_id,comment,commit_item_inline, commit_poodle_item_inline, test_file, test_name, lin_count ,weight, timeout]
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