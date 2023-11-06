#!/usr/bin/env python
###############################################################################
# Copyright 2017 Cray Inc. All Rights Reserved.
#
# xtnls_test.py - a wrapper script used in conjunction with xtnls_test.ini
#                       to execute the standard Cray xtnls diagnostic
#
# The purpose of xtnls_test.py is to provide the means to include 
# the standard Cray xtnls diagnostic as a component test in a list
# of tests 
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtnls_test.py <options> 
#    To see the available options, type: ./xtnls_test.py -h 
#
# 2. To use within a script, just include the "import xtnls_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xtnls_test
# a tool to execute the Cray xtnls diagnostic 
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XtNlsTest(BaseTestComponent):

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
    
    def get_template_arguments(self,test_dictionary):
        #self.logger.debug(self.sysconfig.dump_data(test_dictionary))
        template_arguments = None
        memory_cpu_start = 0
        network_cpu_start = 1
        processor_cpu_start = 2
        stride = 3

        if test_dictionary:
            template_arguments = {}
            if "test_source_path" in test_dictionary and test_dictionary["test_source_path"]:
                template_arguments["script_template_path"] = test_dictionary["test_source_path"]

            if "test_work_path" in test_dictionary and test_dictionary["test_work_path"]:
                template_arguments["script_work_path"] = test_dictionary["test_work_path"]

            template_arguments["template_context"] = {}
            arch = test_dictionary["arch"]
            if arch == "knl":
                use_arch = "bdw"    # use bdw binarys for knl
            else:
                use_arch = arch

            template_arguments["template_context"]["processor_type"] = use_arch
            num_cores = test_dictionary["test_script_ini_num_cores"]
            if (test_dictionary["gpu_model_names"]):
                template_arguments["template_context"]["has_gpu"] = True
                avail_cores = int(num_cores) - 1   # set aside a cpu for launching 1 GPU test
            else:
                template_arguments["template_context"]["has_gpu"] = False
                avail_cores = num_cores            # all cpus go for the Xeon tests

            proc_cpu_csv_list = self.sysconfig.create_integer_csv_list(processor_cpu_start,avail_cores,stride)
            template_arguments["template_context"]["processor_cpu_list"] = proc_cpu_csv_list
            mem_cpu_csv_list = self.sysconfig.create_integer_csv_list(memory_cpu_start,avail_cores,stride)
            template_arguments["template_context"]["memory_cpu_list"] = mem_cpu_csv_list
            net_cpu_csv_list = self.sysconfig.create_integer_csv_list(network_cpu_start,avail_cores,stride)
            template_arguments["template_context"]["network_cpu_list"] = net_cpu_csv_list
            template_arguments["template_context"]["gpu_cpu_list"] = str(avail_cores)  # gpu uses highest cpu
            template_arguments["template_context"]["processor_time_duration"] = "600"
            template_arguments["template_context"]["memory_time_duration"] = "600"
            template_arguments["template_context"]["network_time_duration"] = "600"
            template_arguments["template_context"]["gpu_time_duration"] = "600"
            template_arguments["template_context"]["processor_log_level"] = "2"
            template_arguments["template_context"]["memory_log_level"] = "2"
            template_arguments["template_context"]["network_log_level"] = "2"
            template_arguments["template_context"]["gpu_log_level"] = "2"

        return template_arguments

    def get_aprun_parameters(self,number_of_test_copies=1):
        parameters = []
        
        aprun_parameter_template = self.get_aprun_parameter_template()
        if not aprun_parameter_template:
            aprun_parameter_template = "-n WIDTH -N 1 -L NODE_LIST"
       
        parameters = self.get_job_launcher_parameter_list(aprun_parameter_template,False)	
        return parameters 
    
    def get_srun_parameters(self,number_of_test_copies=1):
        srun_parameter_template = self.get_srun_parameter_template()
         
        if not srun_parameter_template:
            #srun_parameter_template = "--exclusive --mem-per-cpu=MAX -n WIDTH -N 1 --ntasks-per-node=1 --hint=multithread --threads-per-core=NUM_HYPER_THREADS --nodelist=NODE_LIST --time=90"
            #srun_parameter_template = "--exclusive -n WIDTH -N 1 --ntasks-per-node=1 --hint=multithread --threads-per-core=NUM_HYPER_THREADS --nodelist=NODE_LIST --time=90"
            srun_parameter_template = "--exclusive -n WIDTH -N 1 --ntasks-per-node=1 --hint=multithread --threads-per-core=NUM_HYPER_THREADS --nodelist=NODE_LIST --time=360"
         
        parameters = self.get_job_launcher_parameter_list(srun_parameter_template,True)		
        return parameters 

    def get_job_launcher_parameter_list(self,parameter_template_string,slurm_flag):
        parameters = []

        number_of_nodes_per_job = 1
        if self.get_component_option('number_of_nodes_per_job') and (self.get_component_option('number_of_nodes_per_job') is not None):
            number_of_nodes_per_job = int(self.get_component_option('number_of_nodes_per_job'))

        processor_configuration = sysconfig.get_processor_configuration(self.node_info_dict)
        if processor_configuration:
            #get num_cores per nodes dict -- a nodes num_cores will be added to name like bdw_88
            nid_num_cores_dict = sysconfig.get_num_cores_dictionary()

            for name in processor_configuration.keys():
                (node_count,node_list) = processor_configuration[name]

                accel_node_list = []
                if node_list:
                    # check to see if this node_list is a subset of the requested cname list
                    if 'user_specified_node_list' in self and self.user_specified_node_list:
                        intersection_list = sysconfig.get_node_list_intersection(node_list,self.user_specified_node_list)

                        if intersection_list:
                            #node_list = sysconfig.convert_node_list_to_sparse_string(intersection_list)
                            node_list = intersection_list
                            node_count = len(intersection_list)
                        else:
                            continue
                    else:
                        #node_list = sysconfig.convert_node_list_to_sparse_string(node_list)
                        node_list = node_list

                    #node list is now a set of nids with the same core size and mem size
                    number_of_nodes = len(node_list)
                    number_of_jobs = int(number_of_nodes/number_of_nodes_per_job)
                    number_of_odd_jobs = number_of_nodes%number_of_nodes_per_job

                    for i in xrange(number_of_jobs):
                        num_hyper_threads = 2
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
                        if name == "knl" or name == "tx2":
                            num_hyper_threads = 4
                        parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))

                        #see if accelerator or not -- will be added to name like bdw_88_gpu
                        accel_node_list = sysconfig.get_accelerator_model_names_from_node_list(node_list[0:number_of_nodes_per_job])
                        if accel_node_list:
                            if slurm_flag:
                                parameter_string = "--gres=gpu " + parameter_string
                            parameters.append((name + "_" + nid_num_cores_dict[str(node_list[0])] + "_gpu",parameter_string,number_of_nodes_per_job,cur_nid_list_string))
                        else:
                            parameters.append((name + "_" + nid_num_cores_dict[str(node_list[0])],parameter_string,number_of_nodes_per_job,cur_nid_list_string))
                        del node_list[0:number_of_nodes_per_job]

                    if number_of_odd_jobs > 0 and len(node_list) > 0:
                        number_of_nodes = len(node_list)
                        for i in xrange(number_of_nodes):
                            num_hyper_threads = 2
                            #see if accelerator or not -- will be added to name like bdw_88_gpu
                            accel_node_list = sysconfig.get_accelerator_model_names_from_node_list(node_list[0])
                            nid_num_cores = nid_num_cores_dict[str(node_list[0])]    #grab num_cores now before nid_list[0] is deleted
                            nid = node_list[0]
                            if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                cur_host_list_string = self.sysconfig.convert_node_list_to_hostname_list_string([nid])
                            else:
                                cur_host_list_string = str(nid)
                            del node_list[0]
                            parameter_string = parameter_template_string.replace("NPPN","1")
                            if self.partition:
                                parameter_string = "-p " + self.partition + " " + parameter_string
                            parameter_string = parameter_string.replace("WIDTH","1")
                            parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                            if name == "knl":
                                num_hyper_threads = 4
                            parameter_string = parameter_string.replace("NUM_HYPER_THREADS",str(num_hyper_threads))

                            if accel_node_list:
                                if slurm_flag:
                                    parameter_string = "--gres=gpu " + parameter_string
                                parameters.append((name + "_" + nid_num_cores + "_gpu",parameter_string,number_of_nodes_per_job,str(nid)))
                            else:
                                parameters.append((name + "_" + nid_num_cores,parameter_string,number_of_nodes_per_job,str(nid)))
                else:
                    self.logger.debug("unable to build job launcher parameters for " + name)

        return parameters

def main(test_options=None):
    status = 0 
    test = XtNlsTest()
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
                test.post_run_tasks() 
                #test.report()
                json_dump_file_name = test.work_root + "/" + test.MODULE_NAME + ".last_state.json"
                test.dump_state_as_json(json_dump_file_name)
                status = test.get_main_return_status()
            else:
                test.logger.error("main: test failed due to validation errors")
                test.logger.error(validation_errors)
                status = 1
    return status 

if __name__ == "__main__":
    main()


