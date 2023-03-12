#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xtimb_test.py - a wrapper script used in conjunction with xtimb_test.ini
#                       to execute the standard IMB benchmarking tool 
#
# author: Pete Halseth
#
# The purpose of xtimb_test.py is to provide the means to include 
# the standard IMB benchmarking tool as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtimb_test.py <options> 
#    To see the available options, type: ./xtimb_test.py -h 
#
# 2. To use within a script, just include the "import xtimb_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xtimb_test
# a tool to execute the standard IMB benchmark 
import os,sys
from base_test_component import BaseTestComponent

class XTImbTest(BaseTestComponent):

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
            aprun_parameter_template = "-n WIDTH -N NPPN -j NUM_HYPER_THREADS -L NODE_LIST"
       
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
        
        list_mem_sizes = self.sysconfig.get_list_mem_sizes()
        num_hyper_threads = 2
        
        number_of_nodes_per_job = 1	
        if self.get_component_option('number_of_nodes_per_job') and (self.get_component_option('number_of_nodes_per_job') is not None):
            number_of_nodes_per_job = int(self.get_component_option('number_of_nodes_per_job'))
        
        # auto-generate num_cores_per_copy
        #treat each core size as if it was its own system partition
        if 'user_specified_node_list' in self and self.user_specified_node_list:
            nids_by_core_size = self.get_list_of_nids_by_core_size(self.user_specified_node_list)
        else:
            nids_by_core_size = self.get_list_of_nids_by_core_size()

        if nids_by_core_size:
            for core_size_tuple in nids_by_core_size:
                (core_size_string,core_size_nid_list) = core_size_tuple

                for mem_size in list_mem_sizes:
                    intersection_list = []
                    #get the nids for this core size and mem size
                    mem_size_nid_list = self.sysconfig.get_memory_size_nid_list(mem_size)
                    if mem_size_nid_list:
                        intersection_list = self.sysconfig.get_node_list_intersection(mem_size_nid_list,core_size_nid_list)
                        intersection_list.sort(key=int)
                        if not intersection_list:
                            continue
                        #get the processor_type for this group of nids
                        node_info = self.node_info_dict[str(intersection_list[0])]
                        group_processor_type = node_info['cpu_type']
                        if group_processor_type == "knl" or  group_processor_type == "tx2":
                            num_hyper_threads = 4
                        else:
                            num_hyper_threads = 2
                        
                        #intersection list is now a set of nids with the same core size and mem size 
                        number_of_nodes = len(intersection_list)
                        number_of_jobs = int(number_of_nodes/number_of_nodes_per_job)
                        
                        task_count = int(core_size_string) * number_of_nodes_per_job
                        for i in xrange(number_of_jobs):
                            #get number_of_nodes_per_jobs nids off of intersection_list
                            cur_nid_list = intersection_list[0:number_of_nodes_per_job]
                            cur_nid_list_string = self.sysconfig.convert_node_list_to_sparse_string(cur_nid_list)
                            if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(cur_nid_list))
                            else:
                                cur_host_list_string = cur_nid_list_string 
                            del intersection_list[0:number_of_nodes_per_job]
                            
                            parameter_string = parameter_template_string.replace("WIDTH",str(task_count))
                            if self.partition:
                                parameter_string = "-p " + self.partition + " " + parameter_string
                            parameter_string = parameter_string.replace("NPPN",str(core_size_string))
                            parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))
                            parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                            run_name = core_size_string + "_" + str(mem_size) + "_" + group_processor_type
                            parameters.append((run_name,parameter_string,task_count,cur_nid_list_string))
                        
                        if len(intersection_list) > 0:
                            remaining_number_of_nodes = len(intersection_list)
                            remaining_task_count = int(core_size_string) * remaining_number_of_nodes
                            remaining_nid_list_string = self.sysconfig.convert_node_list_to_sparse_string(intersection_list)
                            if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(intersection_list))
                            else:
                                cur_host_list_string = remaining_nid_list_string 
                            parameter_string = parameter_template_string.replace("WIDTH",str(remaining_task_count))
                            if self.partition:
                                parameter_string = "-p " + self.partition + " " + parameter_string
                            parameter_string = parameter_string.replace("NPPN",str(core_size_string))
                            parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))
                            parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                            run_name = core_size_string + "_" + str(mem_size) + "_" + group_processor_type
                            parameters.append((run_name,parameter_string,str(core_size_string),remaining_nid_list_string))
                        
        return parameters
    
    def get_max_imb_cores(self,core_size):
        IMB_MAX = 1100 
        return IMB_MAX - (IMB_MAX % int(core_size))

def main(test_options=None):
    status = 0 
    test = XTImbTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
