#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xtvrm_socket1_test.py - a wrapper script used in conjunction with xtvrm_socket1_test.ini
#                       to execute the standard Cray xtcpudgemm diagnostic
#
# author: Pete Halseth
#
# The purpose of xtvrm_socket1_test.py is to provide the means to include 
# the standard Cray xtcpudgemm diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtvrm_socket1_test.py <options> 
#    To see the available options, type: ./xtvrm_socket1_test.py -h 
#
# 2. To use within a script, just include the "import xtvrm_socket1_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xtvrm_socket1_test
# a tool to execute the Cray xtcpudgemm diagnostic 
import os,shutil,time,subprocess,shlex

from xtvrm_screen_test import XTVrmScreen 

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XTVrmScreen_Socket1(XTVrmScreen):

    def __init__(self):
        
        # set self.FULL_PATH_TO_SCRIPT_DIR 
        self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        
        # set self.COMPONENT_NAME
       	self.COMPONENT_NAME = self.__class__.__name__ 

        # set self.MODULE_NAME
        (file_root,file_name) = os.path.split(os.path.realpath(__file__))
       	(self.MODULE_NAME,ext) = os.path.splitext(file_name)
       
        # initialize parent
        XTVrmScreen.__init__(self)
    
    def get_test_script_parameters(self,number_of_test_copies=1,node_list_string=None,num_PEs=None,job_label=None):

        smallest_size = float("inf") 
        node_list = []
        if not node_list_string:
            return None 
        else:
            node_list = sysconfig.expand_node_list(node_list_string)

        if not node_list:
            return None
        if 'mem_size_dict' in self: 
            mem_size_dict = self.mem_size_dict 
        else:
            mem_size_dict = sysconfig.get_mem_size_dictionary()

        if len(node_list) > 1:
            for nid in node_list:
                if float(mem_size_dict[str(nid)]) < smallest_size:
                    smallest_size = int(mem_size_dict[str(nid)])
        else:
            smallest_size = int(mem_size_dict[str(node_list[0])])

        test_script_parameter_template = self.get_test_script_parameter_template()
        if not test_script_parameter_template:
            test_script_parameter_template = ""

        node_memory_gb = (smallest_size/1024)/2
        ncores = (int(job_label)/2)/2
        test_script_parameters = test_script_parameter_template + " -nthreads " + str(ncores) + " -mem " + str(node_memory_gb)
        return test_script_parameters

def main(test_options=None):
    status = 0 
    test = XTVrmScreen_Socket1()
    if test is not None:
        if not test_options:
            test.process_commandline_options()
        if test.initialize(test_options):
            print "test failed: unable to initialize"
        else:
            validation_errors = test.validate_setup()
            if not validation_errors:
                return_value = test.run()
                if return_value:
                    test.logger.error("main: run method returned non-zero")
                
                #generate results csv output 
                results_output_filename = test.generated_results_csv_output_filename.replace("timestamp",test.session_timestamp)
                test.generate_power_csv(test.log_file_name,results_output_filename.replace("socket_number","socket1"),["Passed","passed","Failed","failure"],[r'c[*0-9]+\-[*0-9]+c[*0-2]s[0-1]?[0-9]'],test.get_component_option("bin_sort_column_label"),1)
                
                #generate watts csv output 
                watts_output_filename = test.get_component_option("generated_watts_csv_output_filename")
                if watts_output_filename:
                    watts_output_filename = test.work_root + "/" + watts_output_filename.replace("timestamp",test.session_timestamp)
                    test.generate_power_csv(test.log_file_name,watts_output_filename.replace("socket_number","socket1"),["Passed","passed","Failed","failure"],[r'c[*0-9]+\-[*0-9]+c[*0-2]s[0-1]?[0-9]'],test.get_component_option("watts_sort_column_label"),1)
                time.sleep(10)
                smw_output_file_name = "/tmp/" + "_".join(map(str,test.apids)) + ".json"
                local_file_name = test.work_root + "/" + "_".join(map(str,test.apids)) + ".json"
                
                test.post_run_tasks()
                #test.report()
                
                try:
                    sysconfig.get_power_and_thermal_data_from_smw(test.get_component_option('destination'),test.get_component_option('first'),test.get_component_option('last'),test.apids,smw_output_file_name,local_file_name,test.get_component_option('smw_utils_path'))
                    outliers = test.get_power_and_thermal_outliers(local_file_name,test.get_component_option('node_power_max'),test.get_component_option('socket_temp_max'))
                    if outliers:
                        print("Power/Temp Outliers")
                        for key in outliers.keys():
                            print str(key) + ": " + str(outliers[key])
                        print "got " + str(len(outliers.keys())) + " power/temp outliers"

                except Exception as e:
                    print "couldn't get power and thermal data from smw"
                    print "reason: %s" % e

                status = test.get_main_return_status()
            else:
                test.logger.error("main: test failed due to validation errors")
                test.logger.error(validation_errors)
    return status 


def test_get_power_and_thermal_outliers(local_file_name,power_max=None,temp_max=None):
    test = XTVrmScreen_Power() 
    outliers = test.get_power_and_thermal_outliers(local_file_name,power_max,temp_max)
    if outliers:
        for outlier in outliers:
            print sysconfig.dump_data(outlier)
        print str(len(outliers)) + " power and temp outliers:"

if __name__ == "__main__":
    json_data_file = "/cray/css/users/phalseth/dev/8917013_8917014.json"
    power_max=450
    temp_max=92
    test_get_power_and_thermal_outliers(json_data_file,power_max,temp_max)
