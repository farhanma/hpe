#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xkmemtest_test.py - a wrapper script used in conjunction with xkmemtest_test.ini
#                       to execute the standard Cray xkmemtest diagnostic
#
# author: Pete Halseth
#
# The purpose of xkmemtest_test.py is to provide the means to include 
# the standard Cray xkmemtest diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xkmemtest_test.py <options> 
#    To see the available options, type: ./xkmemtest_test.py -h 
#
# 2. To use within a script, just include the "import xkmemtest_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xkmemtest_test
# a tool to execute the Cray xkmemtest diagnostic 
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XKMemtestTest(BaseTestComponent):

    def __init__(self):
        
        # set self.FULL_PATH_TO_SCRIPT_DIR 
        self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        
        # set self.COMPONENT_NAME
        self.COMPONENT_NAME = self.__class__.__name__ 

        # set self.MODULE_NAME
        (file_root,file_name) = os.path.split(os.path.realpath(__file__))
        (self.MODULE_NAME,ext) = os.path.splitext(file_name)
       
        # initialize parent
        BaseTestComponent.__init__(self)

    def get_test_script_parameters(self,number_of_test_copies=1,node_list_string=None,num_PEs=None,job_label=None):
        return self.get_gpu_test_script_parameters(number_of_test_copies,node_list_string,num_PEs,job_label)
    
    def get_aprun_parameters(self,number_of_test_copies=1):
        aprun_parameter_template = self.get_aprun_parameter_template()
       
        parameters = self.get_job_launcher_parameter_list(aprun_parameter_template)		
        return parameters 
    
    def get_srun_parameters(self,number_of_test_copies=1):
        srun_parameter_template = self.get_srun_parameter_template()
         
        parameters = self.get_job_launcher_parameter_list(srun_parameter_template)		
        return parameters 
    
    def get_job_launcher_parameter_list(self,parameter_template_string):
        parameters = []
        
        num_nodes_per_job = 4 
        if self.get_component_option('number_of_nodes_per_job') and (self.get_component_option('number_of_nodes_per_job') is not None):
            num_nodes_per_job = int(self.get_component_option('number_of_nodes_per_job')) 
        
        list_of_all_nids_with_accelerators = []
        final_node_list = []
        
        supported_accelerator_names = self.get_component_option("supported_accelerator_names")
        if supported_accelerator_names:
            supported_accelerator_names = supported_accelerator_names.split(",")
       
        accelerator_configuration = sysconfig.get_accelerator_configuration()
        if accelerator_configuration:
            for name in supported_accelerator_names:
                if name in accelerator_configuration:
                    (node_count,node_list) = accelerator_configuration[name]
                    if node_list:
                        list_of_all_nids_with_accelerators = list_of_all_nids_with_accelerators + node_list
             
            #list_of_all_nids_with_accelerators should now be populated
            if len(list_of_all_nids_with_accelerators)>0:
                # if user specified node list, find the intersection with all accelerator nids
                if 'user_specified_node_list' in self and self.user_specified_node_list:
                    intersection_list = sysconfig.get_node_list_intersection(list_of_all_nids_with_accelerators,self.user_specified_node_list)
                    if intersection_list:
                        final_node_list = intersection_list 
                    else:
                        self.logger.debug("unable to find intersection with user-specified node list, so unable to build job launcher parameters for " + name)
                else:
                    final_node_list = list_of_all_nids_with_accelerators
            
                if final_node_list:
                    #create jobs with num_nodes_per_job nodes apiece
                    while len(final_node_list)>=num_nodes_per_job:
                        current_nid_set = final_node_list[0:num_nodes_per_job]
                        #current_nid_list = ",".join(str(e) for e in current_nid_set)
                        cur_nid_list_string = sysconfig.convert_node_list_to_sparse_string(current_nid_set) 
                        if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                            cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(current_nid_set))
                        else:
                            cur_host_list_string = cur_nid_list_string 
                        current_nid_list = sysconfig.convert_node_list_to_sparse_string(current_nid_set)
                        parameter_string = parameter_template_string.replace("NODE_LIST",cur_host_list_string)
                        parameter_string = parameter_string.replace("WIDTH",str(num_nodes_per_job))
                        parameter_string = parameter_string.replace("NPPN",str(1))
                        parameters.append(("bin",parameter_string,num_nodes_per_job,cur_nid_list_string))
                        del final_node_list[0:num_nodes_per_job]
                    
                    #create a job for each of the remaining nodes 
                    if len(final_node_list)>0:
                        num_nodes_per_job = 1 
                        while len(final_node_list)>0:
                            current_nid = str(final_node_list.pop())
                            if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                cur_host_list_string = self.sysconfig.convert_node_list_to_hostname_list_string([int(current_nid)])
                            else:
                                cur_host_list_string = current_nid 
                            parameter_string = parameter_template_string.replace("NODE_LIST",cur_host_list_string)
                            parameter_string = parameter_string.replace("WIDTH",str(num_nodes_per_job))
                            parameter_string = parameter_string.replace("NPPN",str(1))
                            parameters.append(("bin",parameter_string,num_nodes_per_job,current_nid))
            else:
                self.logger.debug("unable to identify and nids with accelerators, so unable to build job launcher parameters for " + name)
                        
        return parameters 

def main(test_options=None):
    status = 0 
    test = XKMemtestTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
