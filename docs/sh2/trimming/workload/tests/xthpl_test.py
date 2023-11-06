#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xthpl_test.py - a wrapper script used in conjunction with xthpl_test.ini
#                       to execute the standard IMB benchmarking tool 
#
# author: Pete Halseth
#
# The purpose of xthpl_test.py is to provide the means to include 
# the standard IMB benchmarking tool as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xthpl_test.py <options> 
#    To see the available options, type: ./xthpl_test.py -h 
#
# 2. To use within a script, just include the "import xthpl_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xthpl_test
# a tool to execute the standard IMB benchmark 
import os,sys
from base_test_component import BaseTestComponent

class XTHplTest(BaseTestComponent):

    def __init__(self):
        
        # set self.FULL_PATH_TO_SCRIPT_DIR 
        self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        
        # set self.COMPONENT_NAME
        if not hasattr(self,'COMPONENT_NAME'):
            self.COMPONENT_NAME = self.__class__.__name__ 

        # set self.MODULE_NAME
        if not hasattr(self,'MODULE_NAME'):
            (file_root,file_name) = os.path.split(os.path.realpath(__file__))
            (self.MODULE_NAME,ext) = os.path.splitext(file_name)
       
        # initialize parent
        BaseTestComponent.__init__(self)

    def get_setup_script_parameters(self,number_of_test_copies=1,reducer=None):

        parameters = []
        list_mem_sizes = self.sysconfig.get_list_mem_sizes()
        num_hyper_threads = 2

        starting_memory_reduction_multiplier = 0.8
        if self.get_component_option('memory_reduction_multiplier') and (self.get_component_option('memory_reduction_multiplier') is not None):
            starting_memory_reduction_multiplier = float(self.get_component_option('memory_reduction_multiplier'))

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
                        memory_reduction_multiplier = .25
                    #get the nids for this core size and mem size
                    mem_size_nid_list = self.sysconfig.get_memory_size_nid_list(mem_size)
                    #self.logger.debug("mem_size_nid_list: " + str(mem_size_nid_list))
                    if mem_size_nid_list:
                        intersection_list = self.sysconfig.get_node_list_intersection(mem_size_nid_list,core_size_nid_list)
                        intersection_list.sort(key=int)
                        if not intersection_list:
                            continue
                        
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
                            cur_nid_list = intersection_list[0:number_of_nodes_per_job-1]
                            cur_nid_list_string = self.sysconfig.convert_node_list_to_sparse_string(cur_nid_list)
                            del intersection_list[0:number_of_nodes_per_job-1]
                            parameters.append((core_size_string + "_" + str(mem_size) +"_" + group_processor_type,"-mem=" + str(((int(mem_size)/1024)*memory_reduction_multiplier)/(int(core_size_string))) + "G" + " -n " + str(task_count) + " -j " + str(num_hyper_threads),int(core_size_string),cur_nid_list_string))
                        
                        if number_of_odd_jobs > 0 and len(intersection_list) > 0:
                            number_of_nodes = len(intersection_list)
                            for i in xrange(number_of_nodes):
                                nid = intersection_list[0]
                                del intersection_list[0]
                                parameters.append((core_size_string + "_" + str(mem_size) +"_" + group_processor_type,"-mem=" + str(((int(mem_size)/1024)*memory_reduction_multiplier)/(int(core_size_string))) + "G" + " -n " + core_size_string + " -j " + str(num_hyper_threads),int(core_size_string),str(nid)))
                        
        return parameters

    def get_srun_parameters(self,number_of_test_copies=1,reducer=None):
        
        parameters = []
        list_mem_sizes = self.sysconfig.get_list_mem_sizes()
        num_hyper_threads = 2

        srun_parameter_template = self.get_srun_parameter_template()
        if not srun_parameter_template:
            #srun_parameter_template = "-n WIDTH --nodelist NODE_LIST --time=90"
            srun_parameter_template = "-n WIDTH --nodelist NODE_LIST --time=360"
        
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
                    #self.logger.debug("mem_size_nid_list: " + str(mem_size_nid_list))
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
                            cur_hostname_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(cur_nid_list)) 
                            del intersection_list[0:number_of_nodes_per_job]

                            parameter_string = srun_parameter_template.replace("NPPN",str(task_count))
                            if self.partition:
                                parameter_string = "-p " + self.partition + " " + parameter_string
                            parameter_string = parameter_string.replace("WIDTH",str(task_count))
                            parameter_string = parameter_string.replace("NODE_LIST",cur_hostname_list_string)
                            parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))
                            parameters.append((core_size_string + "_" + str(mem_size) + "_" + group_processor_type,parameter_string,task_count,cur_nid_list_string))
                        
                        if number_of_odd_jobs > 0 and len(intersection_list) > 0:
                            number_of_nodes = len(intersection_list)
                            for i in xrange(number_of_nodes):
                                cur_nid_list = [intersection_list[0]]
                                cur_nid_list_string = str(intersection_list[0])
                                cur_hostname_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(cur_nid_list)) 
                                parameter_string = srun_parameter_template.replace("NPPN",core_size_string)
                                if self.partition:
                                    parameter_string = "-p " + self.partition + " " + parameter_string
                                parameter_string = parameter_string.replace("WIDTH",core_size_string)
                                parameter_string = parameter_string.replace("NODE_LIST",cur_hostname_list_string)
                                parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))
                                
                                parameters.append((core_size_string + "_" + str(mem_size) + "_" + group_processor_type,parameter_string,core_size_string,cur_nid_list_string))
                                del intersection_list[0]
                        
        return parameters

    def get_aprun_parameters(self,number_of_test_copies=1,reducer=None):
        
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
                    #self.logger.debug("mem_size_nid_list: " + str(mem_size_nid_list))
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
                            del intersection_list[0:number_of_nodes_per_job]
                            parameters.append((core_size_string + "_" + str(mem_size) + "_" + group_processor_type,"-n " + str(task_count) + " -j " + str(num_hyper_threads) + " -L " + cur_nid_list_string,task_count,cur_nid_list_string))
                        
                        if number_of_odd_jobs > 0 and len(intersection_list) > 0:
                            number_of_nodes = len(intersection_list)
                            for i in xrange(number_of_nodes):
                                nid = intersection_list[0]
                                del intersection_list[0]
                                parameters.append((core_size_string + "_" + str(mem_size) + "_" + group_processor_type,"-n " + core_size_string + " -j " + str(num_hyper_threads) + " -L " + str(nid),core_size_string,str(nid)))
                        
        return parameters
    
    def check_hpl_residuals(self,log_file_list,keyword_list):
        residuals = {}
        for log_file_name in log_file_list:
            nid = "NA"
            match_list = self.sysconfig.search_log(log_file_name,keyword_list,1,self.error_match_exclusion_list)
            
            file_name_components = log_file_name.split("/")
            if file_name_components:
                file_name = file_name_components.pop()
                nid = file_name.split("_").pop().replace(".log","")
            
            for match in match_list:
                match_split_list = match.split()
                if match_split_list and len(match_split_list) >= 2:
                    if not match_split_list[1] in residuals:
                       residuals[match_split_list[1]] = [nid]
                    else:
                       residuals[match_split_list[1]].append(nid)
        return residuals

    def report(self,dump=True):
        self.logger.info("checking xhpl log output")
        keyword_list = ["PASSED"]
        residuals = self.check_hpl_residuals(self.single_job_logfiles,keyword_list)
        if residuals:
            if len(residuals.keys()) > 1:
                self.logger.error("xhpl_test found multiple residual values: " + str(residuals.keys()))
                residual_keys = residuals.keys()
                longest_list_key_name = residual_keys[0]
                longest_list_key_length = len(residuals[residuals.keys()[0]])
                for residual_key in residual_keys:
                    if len(residuals[residual_key]) > longest_list_key_length:
                        longest_list_key_length = len(residuals[residual_key])
                for residual_key in residual_keys:
                    if residual_key == longest_list_key_name:
                        self.logger.error("value: " + residual_key + ", number of nodes: " + str(len(residuals[residual_key])))
                    else:
                        self.logger.error("value: " + residual_key + ", nodes: " + str(residuals[residual_key]))
            else:
                self.logger.info("all nodes report the same residual value: " + str(residuals.keys()))
        #call the default report method to look for keyword errors 
        num_general_errors = super(XTHplTest,self).report()
        return num_general_errors 

def main(test_options=None):
    status = 0 
    test = XTHplTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)
