#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xkdgemm_test.py - a wrapper script used in conjunction with xkdgemm_test.ini
#                       to execute the standard Cray xkdgemm diagnostic
#
# author: Pete Halseth
#
# The purpose of xkdgemm_test.py is to provide the means to include 
# the standard Cray xkdgemm diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xkdgemm_test.py <options> 
#    To see the available options, type: ./xkdgemm_test.py -h 
#
# 2. To use within a script, just include the "import xkdgemm_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xkdgemm_test
# a tool to execute the Cray xkdgemm diagnostic 
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XKDgemmTest(BaseTestComponent):

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
        parameters = []
        
        aprun_parameter_template = self.get_aprun_parameter_template()
        if not aprun_parameter_template:
            aprun_parameter_template = "-n WIDTH -N NPPN -L NODE_LIST"
       
        parameters = self.get_job_launcher_parameter_list(aprun_parameter_template)		
        return parameters 
    
    def get_srun_parameters(self,number_of_test_copies=1):
        srun_parameter_template = self.get_srun_parameter_template()
         
        if not srun_parameter_template:
            #srun_parameter_template = "-n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST --time=90"
            srun_parameter_template = "-n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST --time=360"
         
        parameters = self.get_job_launcher_parameter_list(srun_parameter_template)		
        return parameters 
    
    def get_job_launcher_parameter_list(self,parameter_template_string):
        parameters = []
        
        supported_accelerator_names = self.get_component_option("supported_accelerator_names")
        if supported_accelerator_names:
            supported_accelerator_names = supported_accelerator_names.split(",")
        
        accelerator_configuration = sysconfig.get_accelerator_configuration()
        if accelerator_configuration:
            for name in supported_accelerator_names:
                if name in accelerator_configuration:
                    (node_count,node_list) = accelerator_configuration[name]
                    if node_list:
                        # check to see if this node_list is a subset of the requested cname list
                        if 'user_specified_node_list' in self and self.user_specified_node_list:
                            intersection_list = sysconfig.get_node_list_intersection(node_list,self.user_specified_node_list)
                            if intersection_list:
                                node_list = intersection_list
                                node_count = len(node_list)
                            else:
                                continue
                        
                        cur_nid_list_string = sysconfig.convert_node_list_to_sparse_string(node_list)
                        if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                            cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(node_list))
                        else:
                            cur_host_list_string = cur_nid_list_string 
                        parameter_string = parameter_template_string.replace("NPPN","1")
                        parameter_string = parameter_string.replace("WIDTH",str(node_count))
                        parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                        parameters.append((name,parameter_string,node_count,cur_nid_list_string))  
                    else:
                        self.logger.debug("unable to build job launcher parameters for " + name)

        return parameters 

def main(test_options=None):
    status = 0 
    test = XKDgemmTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
