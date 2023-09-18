#!/usr/bin/env python
###############################################################################
# Copyright 2016 Cray Inc. All Rights Reserved.
#
# xta2a_test.py - a wrapper script used in conjunction with xta2a_test.ini
#                       to execute the standard Cray xta2a diagnostic
#
# author: Erik Stromberg
#
# The purpose of xta2a_test.py is to provide the means to include 
# the standard Cray xta2a diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xta2a_test.py <options> 
#    To see the available options, type: ./xta2a_test.py -h 
#
# 2. To use within a script, just include the "import xta2a_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xta2a_test
# a tool to execute the Cray xta2a diagnostic 
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XtA2aTest(BaseTestComponent):

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
    test = XtA2aTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)