#!/usr/bin/env python
import os,sys,shutil,time,subprocess,shlex,string
from xtvrm_screen_test import XTVrmScreen 

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

def main(test_options=None):
    test = XTVrmScreen()
    if test is not None:
        if not test_options:
            test.process_commandline_options()
        if test.initialize(test_options):
            print "test failed: unable to initialize"
        else:
            last_state_dict = test.load_last_state_as_json()
            if last_state_dict:

                log_file_name_list = []
                if 'log_file_name' in last_state_dict:
                    log_file_name_list.append(str(last_state_dict['log_file_name']))
                
                if 'validated_test_commands' in last_state_dict and last_state_dict['validated_test_commands']:
                    for validated_command in last_state_dict['validated_test_commands']:
                        if 'test_logfile_name' in validated_command and validated_command['test_logfile_name']:
                            log_file_name_list.append(str(validated_command['test_logfile_name']))
                test.check_logs(log_file_name_list,test.error_keyword_list)

if __name__ == "__main__":
    main()

