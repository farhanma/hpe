#!/usr/bin/env python
import os,sys
from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XKGhplTest(BaseTestComponent):

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
                    final_node_list = []
                    (node_count,node_list) = accelerator_configuration[name]
                    # check to see if this node_list is a subset of the requested cname list
                    if node_list and 'user_specified_node_list' in self and self.user_specified_node_list:
                        intersection_list = sysconfig.get_node_list_intersection(node_list,self.user_specified_node_list)
                        if intersection_list:
                            final_node_list = intersection_list
                    elif node_list:
                        final_node_list = node_list
                    else:
                        self.logger.debug("unable to build job launcher parameters for " + name)
                    #TODO: fix this 
                    if final_node_list:
                        #if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                        #    cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(cur_nid_list))
                        #else:
                        #    cur_host_list_string = cur_nid_list_string 
                        parameter_node_string = ",".join(map(str,final_node_list))
                        parameters.append((name,"-cc numa_node -N 4 -n " + str(4*len(final_node_list)) + " -L " + parameter_node_string + " -j 1 " + " -d 2" ,1,str(parameter_node_string)))  

        return parameters
   
    def get_environment_vars_list(self,job_label=None,launcher_parameters=None,num_PEs=None,node_list=None):
        environment_variables_template = self.get_environment_variables_template()
        environment_vars_list = environment_variables_template.split(";")
        environment_vars_list_tuples = []
        for environment_variable in environment_vars_list:
            environment_variable = environment_variable.split("=")
            environment_vars_list_tuples.append((environment_variable[0],environment_variable[1]))
        
        return environment_vars_list_tuples	

def main(test_options=None):
    status = 0
    test = XKGhplTest()
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
                test.report()
            else:
                test.logger.error("main: test failed due to validation errors")
                test.logger.error(validation_errors)
                status = 1
            return status

if __name__ == "__main__":
    main()

