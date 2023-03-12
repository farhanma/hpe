#!/usr/bin/env python
###############################################################################
# Copyright 2016 Cray Inc. All Rights Reserved.
#
# xtnuma_test.py - a wrapper script used in conjunction with xtnuma_test.ini
#                       to execute the standard Cray xt numa diagnostic
#
# author: Pete Halseth
#
# The purpose of xtnuma_test.py is to provide the means to include 
# the standard Cray xt numa diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtnuma_test.py <options> 
#    To see the available options, type: ./xtnuma_test.py -h 
#
# 2. To use within a script, just include the "import xtnuma_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xtnuma_test
# a tool to execute the Cray xt numa diagnostic 
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XtNumaTest(BaseTestComponent):

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
            aprun_parameter_template = "-n WIDTH -N NPPN -L NODE_LIST"
       
        parameters = self.get_job_launcher_parameter_list(aprun_parameter_template)		
        return parameters 
    
    def get_srun_parameters(self,number_of_test_copies=1):
        srun_parameter_template = self.get_srun_parameter_template()
         
        if not srun_parameter_template:
            srun_parameter_template = "-n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST"
         
        parameters = self.get_job_launcher_parameter_list(srun_parameter_template)		
        return parameters 
    
    def get_job_launcher_parameter_list(self,parameter_template_string):
        parameters = []
        
        number_of_nodes_per_job = 1
        if self.get_component_option('number_of_nodes_per_job') and (self.get_component_option('number_of_nodes_per_job') is not None):
            number_of_nodes_per_job = int(self.get_component_option('number_of_nodes_per_job'))
       
        processor_configuration = sysconfig.get_processor_configuration(self.node_info_dict)
        if processor_configuration:
            for name in processor_configuration.keys():
                (node_count,node_list) = processor_configuration[name]

                if node_list:
                    # check to see if this node_list is a subset of the requested cname list
                    if 'user_specified_node_list' in self and self.user_specified_node_list:
                        intersection_list = sysconfig.get_node_list_intersection(node_list,self.user_specified_node_list)
                            
                        if intersection_list:
                            node_list = intersection_list
                            node_count = len(intersection_list)
                        else:
                            continue
                    else:
                        node_list = node_list
                        
                    #node list is now a set of nids with the same core size and mem size 
                    number_of_nodes = len(node_list)
                    number_of_jobs = int(number_of_nodes/number_of_nodes_per_job)
                    number_of_odd_jobs = number_of_nodes%number_of_nodes_per_job
                    for i in xrange(number_of_jobs):
                        #get number_of_nodes_per_jobs nids off of intersection_list
                        cur_nid_list = node_list[0:number_of_nodes_per_job]
                        cur_nid_list_string = sysconfig.convert_node_list_to_sparse_string(cur_nid_list)
                        if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                            cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(cur_nid_list))
                        else:
                            cur_host_list_string = cur_nid_list_string 
			                
                        parameter_string = parameter_template_string.replace("NPPN","1")
                        if self.partition and (self.sysconfig.get_wlm() == self.sysconfig.SLURM):
                            parameter_string = "-p " + self.partition + " " + parameter_string
                        parameter_string = parameter_string.replace("WIDTH",str(number_of_nodes_per_job))
                        parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                        parameters.append((name,parameter_string,number_of_nodes_per_job,cur_nid_list_string))  
                        del node_list[0:number_of_nodes_per_job]
                        
                    if number_of_odd_jobs > 0 and len(node_list) > 0:
                        number_of_nodes = len(node_list)
                        for i in xrange(number_of_nodes):
                            nid = node_list[0]
                            if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                cur_host_list_string = self.sysconfig.convert_node_list_to_hostname_list_string([nid])
                            else:
                                cur_host_list_string = str(nid) 
                            del node_list[0]
                            parameter_string = parameter_template_string.replace("NPPN","1")
                            if self.partition and (self.sysconfig.get_wlm() == self.sysconfig.SLURM):
                                parameter_string = "-p " + self.partition + " " + parameter_string
                            parameter_string = parameter_string.replace("WIDTH","1")
                            parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                            parameters.append((name,parameter_string,number_of_nodes_per_job,str(nid)))  
                else:
                    self.logger.debug("unable to build job launcher parameters for " + name)
			
        return parameters 

def main(test_options=None):
    status = 0 
    test = XtNumaTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
