#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xthpcc_test.py - a wrapper script used in conjunction with xthpcc_test.ini
#                       to execute the standard hpcc benchmarking tool 
#
# author: Pete Halseth
#
# The purpose of xthpcc_test.py is to provide the means to include 
# the standard hpcc benchmarking tool as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xthpcc_test.py <options> 
#    To see the available options, type: ./xthpcc_test.py -h 
#
# 2. To use within a script, just include the "import xthpcc_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xthpcc_test
# a tool to execute the standard hpcc benchmark 
import os,sys
from base_test_component import BaseTestComponent

class XTHpccTest(BaseTestComponent):

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
    
    def get_setup_script_parameters(self,number_of_test_copies=1,reducer=None):
        parameters = []
        list_mem_sizes = self.sysconfig.get_list_mem_sizes()
        
        starting_memory_reduction_multiplier = 0.8
        if self.get_component_option('memory_reduction_multiplier') and (self.get_component_option('memory_reduction_multiplier') is not None):
            starting_memory_reduction_multiplier = float(self.get_component_option('memory_reduction_multiplier'))
        
        parameter_template_string = "-n WIDTH -m MEM_SIZE -a 1"

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
                    memory_reduction_multiplier = starting_memory_reduction_multiplier
                    #deal with large memory nodes: CAEXC-1872
                    if int(mem_size) > 700000:
                        memory_reduction_multiplier = .0375

                    #get the nids for this core size and mem size
                    mem_size_nid_list = self.sysconfig.get_memory_size_nid_list(mem_size)
                    if mem_size_nid_list:
                        intersection_list = self.sysconfig.get_node_list_intersection(mem_size_nid_list,core_size_nid_list)
                        intersection_list.sort(key=int)
                        if not intersection_list:
                            continue
                        
                        #intersection list is now a set of nids with the same core size and mem size 
                        number_of_nodes = len(intersection_list)
                        number_of_jobs = int(number_of_nodes/number_of_nodes_per_job)
                        number_of_odd_jobs = number_of_nodes%number_of_nodes_per_job
                        task_count = int(core_size_string) * number_of_nodes_per_job
                        for i in xrange(number_of_jobs):
                            #get number_of_nodes_per_jobs nids off of intersection_list
                            cur_nid_list = intersection_list[0:number_of_nodes_per_job]
                            cur_nid_list_string = self.sysconfig.convert_node_list_to_sparse_string(cur_nid_list)
                            del intersection_list[0:number_of_nodes_per_job]
                            job_instance_cwd = "job_log/" + self.session_timestamp + "/" + cur_nid_list_string.replace(",","_")
                            
                            parameter_string = parameter_template_string.replace("WIDTH",str(task_count))
                            calculated_mem_size = str((int(mem_size)*memory_reduction_multiplier)/int(core_size_string))
                            parameter_string = parameter_string.replace("MEM_SIZE",str(calculated_mem_size))
                            parameters.append((job_instance_cwd,parameter_string,task_count,cur_nid_list_string))
                        
                        if number_of_odd_jobs > 0 and len(intersection_list) > 0:
                            number_of_nodes = len(intersection_list)
                            for i in xrange(number_of_nodes):
                                nid = intersection_list[0]
                                 
                                del intersection_list[0]
                                job_instance_cwd = "job_log/" + self.session_timestamp + "/" + str(nid) 
                            
                                parameter_string = parameter_template_string.replace("WIDTH",core_size_string)
                            	calculated_mem_size = str((int(mem_size)*memory_reduction_multiplier)/int(core_size_string))
                                parameter_string = parameter_string.replace("MEM_SIZE",calculated_mem_size)
                                parameters.append((job_instance_cwd,parameter_string,core_size_string,str(nid)))
                       
        return parameters

    def get_aprun_parameters(self,number_of_test_copies=1):
        parameters = []
        
        aprun_parameter_template = self.get_aprun_parameter_template()
        if not aprun_parameter_template:
            aprun_parameter_template = "-j NUM_HYPER_THREADS -n WIDTH -N NPPN -L NODE_LIST"
       
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
        self.skip_spin_wait_logging = 1 
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
                        if group_processor_type == "knl" or group_processor_type == "tx2":
                            num_hyper_threads = 4
                        else:
                            num_hyper_threads = 2
                        
                        #intersection list is now a set of nids with the same core size and mem size 
                        number_of_nodes = len(intersection_list)
                        number_of_jobs = int(number_of_nodes/number_of_nodes_per_job)
                        number_of_odd_jobs = number_of_nodes%number_of_nodes_per_job
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
                            job_instance_cwd = "job_log/" + self.session_timestamp + "/" + cur_nid_list_string.replace(",","_")
                            job_instance_hpccoutf = self.work_root + "/" + job_instance_cwd + "/hpccoutf.txt"
                            self.single_job_logfiles.append(job_instance_hpccoutf)
                            
                            parameter_string = parameter_template_string.replace("NPPN",core_size_string)
                            if self.partition:
                                parameter_string = "-p " + self.partition + " " + parameter_string
                            parameter_string = parameter_string.replace("WIDTH",str(task_count))
                            parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))
                            parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                            parameters.append((job_instance_cwd,parameter_string,task_count,cur_nid_list_string))
                        
                        if number_of_odd_jobs > 0 and len(intersection_list) > 0:
                            number_of_nodes = len(intersection_list)
                            for i in xrange(number_of_nodes):
                                nid = intersection_list[0]
                                if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                    cur_host_list_string = self.sysconfig.convert_node_list_to_hostname_list_string([nid])
                                else:
                                    cur_host_list_string = str(nid) 
                                 
                                del intersection_list[0]
                                job_instance_cwd = "job_log/" + self.session_timestamp + "/" + str(nid) 
                                job_instance_hpccoutf = self.work_root + "/" + job_instance_cwd + "/hpccoutf.txt" 
                                self.single_job_logfiles.append(job_instance_hpccoutf)
                            
                                parameter_string = parameter_template_string.replace("NPPN",core_size_string)
                                if self.partition:
                                    parameter_string = "-p " + self.partition + " " + parameter_string
                                parameter_string = parameter_string.replace("WIDTH",core_size_string)
                                parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))
                                parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                                parameters.append((job_instance_cwd,parameter_string,core_size_string,str(nid)))
                       
        return parameters

def main(test_options=None):
    status = 0 
    test = XTHpccTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
