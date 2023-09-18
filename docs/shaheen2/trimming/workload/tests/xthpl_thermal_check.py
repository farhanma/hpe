#!/usr/bin/env python
import os,sys,shutil,time,subprocess,shlex,string
from xthpl_thermal_test import XTHplThermalTest 

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

def main(test_options=None):
    debug = 0 

    display_results = 0
    if test_options and 'display_results' in test_options:
        display_results = 1

    test = XTHplThermalTest()
    standard_error_tuples_list = test.component_check_main(test_options)  
    
    #look for residual errors
    residual_error_tuples_list = [] 
    residual_keyword_list = ["PASSED"]
    residual_log_file_list = sysconfig.get_session_single_job_logfiles(test.work_root + "/job_log",test.reporting_session_timestamp)
    
    logfile_lists_sorted_by_node_type = test.sysconfig.sort_logfile_list_by_node_type(residual_log_file_list)
    if logfile_lists_sorted_by_node_type:
        if debug: print "sorted logfile list keys: " + test.dump_data(logfile_lists_sorted_by_node_type.keys())
        for key in logfile_lists_sorted_by_node_type.keys():
            if debug: print "looking through " + key + " list: " + test.dump_data(logfile_lists_sorted_by_node_type[key]) 
            residuals = test.check_hpl_residuals(logfile_lists_sorted_by_node_type[key],residual_keyword_list)
            if residuals:
                if len(residuals.keys()) > 1:
                    error_status = ""
                    residual_keys = residuals.keys()
                    if debug: print "xthpl_test found residual values errors:"
                    if debug: print test.sysconfig.dump_data(residual_keys)
            
                    longest_list_key_name = residual_keys[0]
                    longest_list_key_length = len(residuals[residuals.keys()[0]])
                    for i,residual_key in enumerate(residual_keys):
                        if debug: print "length residuals[" + residual_key + "]: " + str(len(residuals[residual_key]))
                        if len(residuals[residual_key]) > longest_list_key_length:
                            longest_list_key_length = len(residuals[residual_key])
                            longest_list_key_name = residual_keys[i]
                    if debug: print "longest_list_key_name: " + longest_list_key_name
                        
                    for residual_key in residual_keys:
                        failed_residual_cnames = []
                        failed_residual_nids = []
                        complete_failure_list = []
                        if not residual_key == longest_list_key_name:
                            if debug: print "creating display list for residual_key: " + residual_key
                            for index,nid in enumerate(residuals[residual_key]):
                                if debug: print "nid[" + str(index) + "]: " + str(nid) 
                                if "c" in nid:
                                    failed_residual_cnames.append(nid)
                                else: 
                                    cname = test.get_cname_from_nid_using_cnames_dictionary(int(nid))
                                    if cname:
                                        failed_residual_cnames.append(cname)
                                    else:
                                        failed_residual_nids.append(str(nid))
                                
                            complete_failure_list = failed_residual_cnames + failed_residual_nids
                            label = "node"
                            if len(complete_failure_list) > 1:
                                label = "nodes"
                                
                            cname_string = ""
                            comma = ""
                            for cname in complete_failure_list:
                                cname_string = cname_string + comma + str(cname)
                                comma = ","
                            residual_failure_message = "actual value: " + str(residual_key) + ", expected value: " + longest_list_key_name 
                            residual_error_tuples_list.append((test.reporting_session_timestamp,cname_string,"residual failure - " + residual_failure_message)) 
    
    if residual_error_tuples_list and display_results:
        test.display_and_log_error_tuples_list(residual_error_tuples_list)

    if not standard_error_tuples_list:
        standard_error_tuples_list = []

    return standard_error_tuples_list + residual_error_tuples_list  

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    test_options["add_global_error_keywords"] = True
    test_options["display_results"] = True
    main(test_options)


