#!/usr/bin/env python
###############################################################################
# Copyright 2016 Cray Inc. All Rights Reserved.
#
# xtfbc_batch_test.py - a wrapper script used in conjunction with xtfbc_batch_test.ini
#                       to execute the standard Cray xtfbc diagnostic
#
# author: Pete Halseth 
#
# The purpose of xtfbc_batch_test.py is to provide the means to include 
# the standard Cray xtfbc diagnostic as a component test in a list
# of tests 
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtfbc_batch_test.py <options> 
#    To see the available options, type: ./xtfbc_batch_test.py -h 
#
# 2. To use within a script, just include the "import xtfbc_batch_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xtfbc_batch_test
# a tool to execute the Cray xtfbc diagnostic 
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XtFbcBatchTest(BaseTestComponent):

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
        parameter_template = self.get_test_script_parameter_template()
        if not parameter_template or not node_list_string:
            return "" 
        node_list = self.sysconfig.expand_node_list(node_list_string)
        return parameter_template.replace("RANK",self.sysconfig.get_rank(len(node_list)))  

    def get_aprun_parameters(self,number_of_test_copies=1):
        parameters = []
        
        aprun_parameter_template = self.get_aprun_parameter_template()
        if not aprun_parameter_template:
            aprun_parameter_template = "-n WIDTH -N 1 -L NODE_LIST"
       
        parameters = self.get_network_job_launcher_parameter_list(aprun_parameter_template)		
        return parameters 
    
    def get_srun_parameters(self,number_of_test_copies=1):
        srun_parameter_template = self.get_srun_parameter_template()
         
        if not srun_parameter_template:
            #srun_parameter_template = "-n WIDTH --ntasks-per-node=1 --nodelist=NODE_LIST --time=90"
            srun_parameter_template = "-n WIDTH --ntasks-per-node=1 --nodelist=NODE_LIST --time=360"
         
        parameters = self.get_network_job_launcher_parameter_list(srun_parameter_template)		
        return parameters 
    
def main(test_options=None):
    status = 0 
    test = XtFbcBatchTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
