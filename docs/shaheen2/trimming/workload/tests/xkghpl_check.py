#!/usr/bin/env python
import os,sys,shutil,time,subprocess,shlex,string
from xkghpl_test import XKGhplTest 

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

def main(test_options=None):
    test = XKGhplTest()
    if test is not None:
        if not test_options:
            test.process_commandline_options()
        if test.initialize(test_options,report_mode=True):
            print "test failed: unable to initialize"
        else:
            error_tuples_list = []
            searchable_log_files_list = []
            if test_options and 'xtsystest_session_timestamp' in test_options and test_options['xtsystest_session_timestamp']:
                job_logs_root = sysconfig.expand_and_verify_work_root(test_options['work_root']) + "/" + test_options['name'].replace('check','test') + "/job_log"
                searchable_log_files_list = sysconfig.get_session_single_job_logfiles(job_logs_root,test_options['xtsystest_session_timestamp']) 
            elif 'reporting_session_timestamp' in test and test.reporting_session_timestamp:
                job_logs_root = test.work_root + "/job_log"
                searchable_log_files_list = sysconfig.get_session_single_job_logfiles(job_logs_root,test.reporting_session_timestamp) 
            else:    
                last_state_dict = test.load_last_state_as_json()
                if last_state_dict:
                    if 'validated_test_commands' in last_state_dict and last_state_dict['validated_test_commands']:
                        for validated_command in last_state_dict['validated_test_commands']:
                            if 'test_logfile_name' in validated_command and validated_command['test_logfile_name']:
                                searchable_log_files_list.append(str(validated_command['test_logfile_name']))

            if searchable_log_files_list:
                if 0:
                    print test.MODULE_NAME + ": calling test.check_logs with params:"
                    print "\tsearchable_log_files_list: " + sysconfig.dump_data(searchable_log_files_list) 
                    print "\terror_keyword_list: " + str(test.error_keyword_list)
                error_tuples_list = test.check_logs(searchable_log_files_list,test.error_keyword_list)
                if error_tuples_list:
                    print "found " + str(len(error_tuples_list)) + " errors:"
                    print sysconfig.dump_data(error_tuples_list)
                else:
                    print "found " + str(len(error_tuples_list)) + " errors"
            else:
                print test.MODULE_NAME + ": unable to determine list of searchable log filenames" 
            return error_tuples_list


if __name__ == "__main__":
    main()

