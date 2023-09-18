#!/usr/bin/env python
###############################################################################
# Copyright 2014,2016 Cray Inc. All Rights Reserved.
#
# base_test_component.py - the base test class
#
# author: Pete Halseth
#
# This module contains a base test component class that encapsulates
# the common aspects of a test component. 
#
# Usage:
# -------
# 1. To run as a standalone test: ./base_test_component.py <options> 
#    To see the available options, type: ./base_test_component.py -h 
#
# 2. To use within a script, just include the "import base_test_component" statement at 
# the top of the script
# 
################################################################################
##@package workload.tests.base_test_component
# This file can be run as a standalone, top-level script
# or imported as a module to create test component sub-classes

import os, sys, subprocess, shlex, shutil, time, random, logging, ConfigParser, json, glob, threading, copy
from optparse import OptionParser
from datetime import datetime

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class BaseTestComponent(object):
    ## constructor
    # sets general properties 
    def __init__(self):
        self.FULL_PATH_TO_WORKLOAD_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__))).replace("/tests","")
        self.FULL_PATH_TO_UTIL_DIR = self.FULL_PATH_TO_WORKLOAD_DIR + "/util" 
        
        # this should only happen if the base_test_component.py module is executed as a standalone module
        if not hasattr(self,'FULL_PATH_TO_SCRIPT_DIR'):
            self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        
        # this should only happen if the base_test_component.py module is executed as a standalone module
        if not hasattr(self,'MODULE_NAME'):
            (file_root,file_name) = os.path.split(os.path.realpath(__file__))
            (self.MODULE_NAME,ext) = os.path.splitext(file_name)

       
        # improve readability and reliability by pre-defining all member variables here 
        self.current_user_name = None 
        self.global_default_options = {}
        self.global_component_options = {}
        self.global_test_options = {}
        self.global_error_keyword_list = []
        self.component_test_type = "diag" 
        self.component_options = {}
        self.general_options = {}
        self.workload_manager_options = {}
        self.error_keyword_list = []
        self.error_match_exclusion_list = []
        self.cname = None 
        self.cname_exclusions = None 
        self.cnames_dictionary = None
        self.node_info_dict = None
        self.num_cores_dict = None
        self.mem_size_dict = None
        self.wlm = None
        self.partition = None
       
        #ini settings 
        self.default_ini_file = self.FULL_PATH_TO_SCRIPT_DIR + "/" + self.MODULE_NAME + ".ini"
        self.default_global_ini_file = self.FULL_PATH_TO_WORKLOAD_DIR + "/" + "xtsystest.ini"
        
        #user provided commandline options 
        self.margin = ""
        self.dry_run = False
        self.fail_on_error = False
        self.ini_file_path = None
        self.work_root = None
        self.user_specified_node_list = []
        self.wall_clock_time_limit_unit = "m"
        self.wall_clock_time_limit_value = None 
        self.verbose = False
        self.seconds_until_launch_failure = 300 
        self.node_list_ready_retries = 10 
        
        #runtime bookkeeping 
        self.validated_job_launcher_path = None 
        self.validated_test_commands = []
        self.running_test_procs = [] 
        self.running_test_script_names = [] 
        self.apids = []
        self.session_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.returned_statuses = []
        self.main_return_status = 0 
        
        #logging and reporting
        self.report_mode = 0
        self.logger = None
        self.log_file_name = None
        self.error_log_file_name = None
        self.single_job_logfiles = [] 
        self.single_job_logfile_handles = [] 
        self.single_job_error_logfiles = [] 
        self.single_job_error_logfile_handles = [] 
        self.reporting_session_timestamp = None
        self.skip_spin_wait_logging = 0
        self.generated_results_csv_output_filename = "generated_results_" + self.session_timestamp + ".csv"
        self.slurm_memory_error_limit_string = "Exceeded step memory limit"        
    
    ## method to return string representation of object instances
    # utilizes json.dumps
    def __str__(self):
        return json.dumps(self.__dict__,indent=1)
   
    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
                            sort_keys=True, indent=4)
    ## method to return string representation of object instances
    # utilizes json.dumps
    def dump_data(self,data_container):
        if data_container:
            return json.dumps(data_container, default=lambda o: o.__dict__, 
                                sort_keys=True, indent=4)
        else:
            return "no data"
    
    ## method to allow interating across object attribures
    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith("__"):
                yield attr

    ## method to parse commandline options
    # utilizes standard Python OptionParser module
    def process_commandline_options(self):
        parser = OptionParser(usage="%prog [-c CNAME] [-d WORKROOT] [-f] [-i INIFILEPATH] [-h] [-m MARGIN] [-v] [-x CNAMEEXCLUSIONS] [-y] [--version]", version="%prog CAEXC-882")

        parser.add_option("-c","--cname",dest="cname",default=None,
                help="a cname value representing the system resources to target")

        parser.add_option("-d","--dir",dest="workRoot",default=None,
            help="user specified work and log output directory")
        
        parser.add_option("-f","--fail",action='store_true',dest="failOnError",
            help="stop test immediately when an error is encountered")

        parser.add_option("-i","--ini",dest="iniFilePath",default=None,
            help="path to user specified INI file")

        parser.add_option("-m","--margin",dest="margin",default="",
            help="used as a prefix for log file names to provide additional testing context during post-run analysis")
        
        parser.add_option("-s","--session",dest="reportingSessionTimestamp",default=None,
            help="user specified session timestamp for reporting purposes")
       
        parser.add_option("-v","--verbose",action='store_true',dest="verbose",
            help="run in verbose mode")
       
        parser.add_option("-x","--exclude",dest="cnameExclusions",default=None,
            help="a cname value representing the system resources to exclude")

        parser.add_option("-y","--dry",action='store_true',dest="dryRun",
            help="dump config settings and exit")
        
        (options, args) = parser.parse_args()
        if options:
            self.ini_file_path=options.iniFilePath
            self.work_root=options.workRoot
            self.cname=options.cname
            self.margin=options.margin
            self.verbose=options.verbose
            self.dry_run=options.dryRun
            self.fail_on_error=options.failOnError
            self.reporting_session_timestamp=options.reportingSessionTimestamp
    
    ## method to parse the global ini file
    # optional input: ini_file_path
    # if the ini_file_path input parameter is undefined
    # the default_ini_file will be parsed instead
    def parse_global_ini(self,ini_file_path=None):
        
        if not ini_file_path:
            ini_file_path = self.default_global_ini_file
        
        #normalize and check ini_file_path
        ini_file_path = self.sysconfig.expand_and_verify_file_system_path(ini_file_path)
        if ini_file_path:
            ini_file_handle = open(ini_file_path)
            parser = ConfigParser.ConfigParser()
            parser.readfp(ini_file_handle)
            sections = parser.sections()
            if not sections:
                    return False

            # process the defaults section first
            options = parser.options("defaults")
            for option in options:
                self.global_default_options[option] = parser.get("defaults",option)
            
            # process the component-specific settings
            options = parser.options(self.MODULE_NAME)
            if options:
                for option in options:
                    self.global_component_options[option] = parser.get(self.MODULE_NAME,option)
       
            # process the rest of the ini sections, which should just be WLM settings
            for section in sections:
                options = None
                if section != "defaults" and section != self.MODULE_NAME:
                    opts = {}
                    options = parser.options(section)
                    for option in options:
                        opts[option] = parser.get(section,option)
                    self.global_test_options[section] = opts

            ini_file_handle.close()
        else:
            return 0
    
    ## method to parse an ini file
    # optional input: ini_file_path
    # if the ini_file_path input parameter is undefined
    # the default_ini_file will be parsed instead
    def parse_ini(self,ini_file_path=None):
        
        if not ini_file_path:
            ini_file_path = self.default_ini_file
        
        #normalize and check ini_file_path
        ini_file_path = self.sysconfig.expand_and_verify_file_system_path(ini_file_path)
        if ini_file_path:
            ini_file_handle = open(ini_file_path)
            parser = ConfigParser.ConfigParser()
            parser.readfp(ini_file_handle)
            sections = parser.sections()
            if not sections:
                    return False

            # process the defaults section first
            options = parser.options("defaults")
            for option in options:
                self.general_options[option] = parser.get("defaults",option)
            
            # process the component-specific settings
            options = parser.options(self.MODULE_NAME)
            if options:
                for option in options:
                    self.component_options[option] = parser.get(self.MODULE_NAME,option)
       
            # process the rest of the ini sections, which should just be WLM settings
            for section in sections:
                options = None
                if section != "defaults" and section != self.MODULE_NAME:
                    opts = {}
                    options = parser.options(section)
                    for option in options:
                        opts[option] = parser.get(section,option)
                    self.workload_manager_options[section] = opts

            ini_file_handle.close()
        else:
            return 0

    ## method to get a standard Python logging object
    # required input: the full path to a writable log file location
    def get_logger(self,log_file_name):
        if not log_file_name:
            return "get_logger: log_file_name is undefined"
       
        logger = logging.getLogger(self.MODULE_NAME + "." + str(log_file_name))
        logger.setLevel(logging.DEBUG)
        
        #create formatter and add it to the handlers
        formatter = logging.Formatter("%(asctime)s - " + self.MODULE_NAME + " - %(levelname)s - %(message)s")

        if not len(logger.handlers):
            #add the handlers to the logger
            #create file handler which logs INFO messages 
            
            fh = logging.FileHandler(log_file_name)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
            #create console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

        return logger 
    
    ## method that initiates all test component setup including configuration and logging, taking commandline options into account 
    # optional input parameter: user_options
    # if provided, user_options has to be a dictionary object containing name/value pairs, that will override any default values
    def initialize(self,user_options=None,report_mode=None):
        
        component_options_exclusion_list = ["sysconfig"] 
        if user_options and 'sysconfig' in user_options and user_options['sysconfig']:
            self.sysconfig = copy.deepcopy(user_options['sysconfig'])
        else:
            self.sysconfig = system_configuration.BaseConfig.factory() 

        # parse the default component ini file
        # the default component ini file is automatically assumed to be located in the same
        # directory as the current python module file. 
        # full path to default_ini_file is set in constructor 
        parsed_default_config = 0
        if 'ini_file_path' in self and self.ini_file_path:
            self.parse_ini(self.ini_file_path)
        elif os.path.isfile(self.default_ini_file):
            self.parse_ini(self.default_ini_file)
            parsed_default_config = 1
        
        if report_mode:
            self.report_mode=1
        
        # now initialize work_root from default ini, if it wasn't already set by a commandline option 
        if self.work_root is None and 'work_root' in self.general_options and self.general_options['work_root']:
            self.work_root = self.general_options['work_root']
        
        # initialize the cname dictionary 
        self.cnames_dictionary = self.sysconfig.get_cnames_dictionary(self.partition)
        if not self.cnames_dictionary:
            print "%s %s initialize has no cnames_dictionary, unable to proceed" % (time.strftime("%Y%m%d%H%M%S"),self.MODULE_NAME)
            return 1 # non-zero 
        
        #populate the error_keyword_list
        if 'error_keyword_list' in self.component_options and self.component_options['error_keyword_list']:
            self.error_keyword_list = self.component_options['error_keyword_list'].split(",") 
        
        #populate the error_match_exclusion_list
        if 'error_match_exclusion_list' in self.component_options and self.component_options['error_match_exclusion_list']:
            self.error_match_exclusion_list = self.component_options['error_match_exclusion_list'].split(",") 
        
        # override defaults with any user specified options 
        if user_options:
            
            if 'ini_file_path' in user_options and user_options['ini_file_path']:
                self.parse_ini(user_options['ini_file_path'])
            elif not parsed_default_config:
                print "%s %s initialize did not find an ini file, unable to proceed" % (time.strftime("%Y%m%d%H%M%S"),self.MODULE_NAME)
                return 1 # non-zero
  
            if "add_global_error_keywords" in user_options and user_options["add_global_error_keywords"]:
                user_options["error_keyword_list"] = self.get_global_error_keyword_list() 
            
            if 'wlm' in user_options and user_options['wlm']:
                self.wlm = user_options['wlm'] 
            
            if 'partition' in user_options and user_options['partition']:
                self.partition = user_options['partition'] 
            
            if 'error_keyword_list' in user_options and user_options['error_keyword_list']:
                top_level_error_keyword_list = user_options['error_keyword_list'].split(",") 
                self.error_keyword_list = list(set(self.error_keyword_list + top_level_error_keyword_list)) 
            
            if 'seconds_until_launch_failure' in user_options and user_options['seconds_until_launch_failure']:
                self.seconds_until_launch_failure = int(user_options['seconds_until_launch_failure']) 
            
            if 'work_root' in user_options and user_options['work_root']:
                self.work_root = user_options['work_root'] + "/" + self.MODULE_NAME
            
            if 'wall_clock_time_limit_value' in user_options and user_options['wall_clock_time_limit_value']:
                self.wall_clock_time_limit_value = int(user_options['wall_clock_time_limit_value'])
            
            if 'cname' in user_options and user_options['cname']:
                self.cname = user_options['cname']
            
            if 'cname_exclusions' in user_options and user_options['cname_exclusions']:
                self.cname_exclusions = user_options['cname_exclusions']
            
            if 'blades' in user_options and user_options['blades']:
                self.blades = user_options['blades']
            
            if 'notrim' in user_options:
                self.notrim = user_options['notrim']
            
            if 'dry_run' in user_options and user_options['dry_run']:
                self.dry_run = user_options['dry_run']
            
            if self.verbose:
                print "self.dry_run: " + str(self.dry_run)

            if 'margin' in user_options and user_options['margin']:
                self.margin = user_options['margin']
            
            if 'fail_on_error' in user_options and user_options['fail_on_error']:
                self.fail_on_error = user_options['fail_on_error']
            
            if 'session_timestamp' in user_options and user_options['session_timestamp']:
                self.session_timestamp = user_options['session_timestamp']
            
            if 'node_info_dict' in user_options and user_options['node_info_dict']:
                self.node_info_dict = user_options['node_info_dict']
                self.sysconfig.set_node_info_dictionary(self.node_info_dict)
            
            if 'node_code_names_dict' in user_options and user_options['node_code_names_dict']:
                self.node_code_names_dict = user_options['node_code_names_dict']
            
            # re-initialize the cname dictionary to take partition into account 
            self.cnames_dictionary = self.sysconfig.get_cnames_dictionary(self.partition)
            if not self.cnames_dictionary:
                print "%s %s initialize has no cnames_dictionary, unable to proceed" % (time.strftime("%Y%m%d%H%M%S"),self.MODULE_NAME)
                return 1 # non-zero 
   
            if 'user_specified_node_list' in user_options and user_options['user_specified_node_list']:
                #need to reconcile user_specified_node_list with current set of up nodes 
                self.user_specified_node_list = self.sysconfig.get_node_list_intersection(self.cnames_dictionary["s0"],user_options['user_specified_node_list']) 
            
            if 'report_mode' in user_options and user_options['report_mode']:
                self.report_mode = user_options['report_mode']

            #now add any remaining user options to the component_options list
            for key in user_options.keys():
                if not key in component_options_exclusion_list:
                    self.component_options[key] = user_options[key]
        
        
        # make sure the wlm is known
        if not self.wlm:
            self.wlm = self.sysconfig.get_wlm() 
       
        #populate the mem_size_dict
        self.mem_size_dict = self.sysconfig.get_mem_size_dictionary()
        
        #populate the num_cores_dict
        self.num_cores_dict = self.sysconfig.get_num_cores_dictionary()
        
        #handle cname and cname_exclusions when in standalone mode
        #the only way this can be true is if the component test is executed directly (not invoked by xtsystest.py)
        if not 'user_specified_node_list' in self and 'cname' in self and self.cname:
            self.user_specified_node_list = self.sysconfig.get_user_specified_node_list(self.cnames_dictionary,self.cname) 
            if 'cname_exclusions' in self and self.cname_exclusions:
                node_exclusion_list = self.sysconfig.get_user_specified_node_list(self.cnames_dictionary,self.cname_exclusions)
                if node_exclusion_list:
                    self.user_specified_node_list = [nid for nid in self.user_specified_node_list if nid not in node_exclusion_list]
            if not self.user_specified_node_list: 
                print "%s %s initialize unable to resolve user requested cname: %s, unable to proceed" % (time.strftime("%Y%m%d%H%M%S"),self.MODULE_NAME,self.cname)
                return 1 # non-zero
        elif not 'user_specified_node_list' in self and 'cname_exclusions' in self and self.cname_exclusions:
            node_list = self.sysconfig.expand_note_list(self.sysconfig.get_node_list()) 
            node_exclusion_list = self.sysconfig.get_user_specified_node_list(self.cnames_dictionary,self.cname_exclusions)
            if node_exclusion_list:
                self.user_specified_node_list = [nid for nid in node_list if nid not in node_exclusion_list]
            if not self.user_specified_node_list: 
                print "%s %s initialize unable to resolve user requested node list using cname_excluseion: %s, unable to proceed" % (time.strftime("%Y%m%d%H%M%S"),self.MODULE_NAME,self.cname_exclusions)
                return 1 # non-zero
       
        #populate the node_code_names_dict
        if 'node_code_names_dict' not in self and not self.report_mode:
            if 'node_info_dict' in self and self.node_info_dict:
                self.node_code_names_dict = self.sysconfig.get_node_code_names_dictionary_from_node_info_dictionary(self.node_info_dict)
            else:
                self.node_code_names_dict = self.sysconfig.get_node_code_names_dictionary()
        
        # at this point, self.work_root is either defined from user_options, default ini, or is None
        self.work_root = self.sysconfig.expand_and_verify_work_root(self.work_root)
        
        margin_component = "" 
        if self.margin:
            margin_component = "_" + self.margin

        if self.report_mode:
            self.log_file_name = self.work_root + "/" + self.MODULE_NAME.replace("test","check") + margin_component + "_" + self.session_timestamp + ".log"
        else:
            self.log_file_name = self.work_root + "/" + self.MODULE_NAME + margin_component + "_" + self.session_timestamp + ".log"
        self.logger = self.get_logger(self.log_file_name)
        
         
        if self.report_mode:
            self.error_log_file_name = self.work_root + "/" + self.MODULE_NAME.replace("test","check") + margin_component + "_" + self.session_timestamp + "_error.log"
        else:
            self.error_log_file_name = self.work_root + "/" + self.MODULE_NAME + margin_component + "_" + self.session_timestamp + "_error.log"
        self.error_log = open(self.error_log_file_name,'w')
    
        
        if not self.logger:
            return 1 #non-zero
        
        #determine the currrent user name 
        self.current_user_name = self.sysconfig.get_current_user_name()
        if 'root' in self.current_user_name:
            self.logger.error("Running as root is not allowed. Please change user and run using a non-root account.")
            return 1 #non-zero
        
        #verify all targeted nodes are available
        if not self.report_mode: 
            ready_retries = 1 
            ready_node_list = []
            
            if not self.user_specified_node_list:
                frontend_host_arch = sysconfig.get_frontend_host_arch()
                arch_specific_node_list = sysconfig.get_arch_specific_node_list(frontend_host_arch)
                self.user_specified_node_list = sysconfig.get_node_list_intersection(sysconfig.expand_node_list(sysconfig.get_node_list()),arch_specific_node_list)

            while (not self.sysconfig.node_list_ready_for_job_submission(self.user_specified_node_list)) and (ready_retries <= self.node_list_ready_retries):
                self.logger.info("Not all nodes ready for job submission in node list")
                ready_retries = ready_retries + 1
                time.sleep(5)

            if ready_retries >= self.node_list_ready_retries:
                self.logger.error("Initialization failed: node list not ready after " + str(ready_retries) + " verification attempts: " + str(self.user_specified_node_list))
                return 1
            elif ready_retries > 1:
                self.logger.info("All nodes in list ready for job submission after " + str(ready_retries) + " verification attempts")

        return 0 

    def validate_setup(self):
        ## wrapper method that aggregates validation errors for the general options, component options, and wlm options 
        self.validation_errors = {}
        
        # validate that expected general options are properly defined
        general_options_validation_errors = []
        if 'general_options' in self and self.general_options is not None:
            general_options_validation_errors = self.validate_general_options()
        else:
            general_options_validation_errors.append("general options member variable not defined, check ini file definition")
        if general_options_validation_errors:
            self.validation_errors['general_options_validation_errors'] = general_options_validation_errors  
        
        # validate that expected component options are properly defined. The implementation of this is component specific
        component_options_validation_errors = []
        if 'component_options' in self and self.component_options is not None:
            component_options_validation_errors = self.validate_component_options()
        else:
            component_options_validation_errors.append("component options member variable not defined, check ini definition")
        if component_options_validation_errors:
            self.validation_errors['component_options_validation_errors'] = component_options_validation_errors  
        return self.validation_errors
        
    def validate_general_options(self):
        validation_errors = []
       
        #honor specified wall clock time limits
        if not self.wall_clock_time_limit_unit and 'wall_clock_time_limit_unit' in self.general_options and self.general_options['wall_clock_time_limit_unit']:
            self.wall_clock_time_limit_unit = self.general_options['wall_clock_time_limit_unit']
        
        if not self.wall_clock_time_limit_value and 'wall_clock_time_limit_value' in self.general_options and self.general_options['wall_clock_time_limit_value']:
            self.wall_clock_time_limit_value = int(self.general_options['wall_clock_time_limit_value'])
        return validation_errors
    
    def validate_component_options(self):
        validation_errors = []
        validated_commands = []

        # examine the component options here, and use them to build a list of tuples of executable commands
        if 'component_options' in self and self.component_options is not None:

            #TODO: make this a list instead of just one 
            if 'test_script' in self.component_options and self.component_options['test_script'] is not None:

                if 'additional_cray_modules' in self.component_options and self.component_options['additional_cray_modules']:
                    temp_mod_list = self.component_options['additional_cray_modules']
                    python_module = {}
                    python_module_file = "/opt/modules/default/init/python.py" 
                    if not os.path.exists(python_module_file):
                        python_module_file = "/opt/modules/default/init/python" 

                    execfile(python_module_file,python_module)
                    temp_mod_list = temp_mod_list.split(',')
                    for mod in temp_mod_list:
                        python_module['module']('load', mod)
            
                if 'generated_results_csv_output_filename' in self.component_options and self.component_options['generated_results_csv_output_filename'] is not None:
                    self.generated_results_csv_output_filename = self.work_root + "/" + self.component_options['generated_results_csv_output_filename']
                else:
                    self.generated_results_csv_output_filename = self.work_root + "/" + self.generated_results_csv_output_filename
 
                if 'num_passes' in self.component_options and self.component_options['num_passes']: 
                    self.num_passes = int(self.component_options['num_passes'])
                
                if 'run_test_copies_concurrently' in self.component_options and self.component_options['run_test_copies_concurrently']: 
                    self.run_test_copies_concurrently = self.component_options['run_test_copies_concurrently']
                else:
                    self.run_test_copies_concurrently = False 
               
                num_test_copies = 1
                if 'num_test_copies' in self.component_options and self.component_options['num_test_copies']:
                    num_test_copies = int(self.component_options['num_test_copies'])
                
                use_reservation = 0 
                if 'reservation' in self.component_options and self.component_options['reservation'] and self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                    use_reservation = self.component_options['reservation'] + " "
               
                # get the job_launcher_parameters, setup_script_parameters lists
                # these are lists of tuples
                job_launcher_parameters_list = [] 
                setup_script_parameters_list = [] 
                if not self.report_mode:
                    job_launcher_parameters_list = self.get_job_launcher_parameters(num_test_copies) 
                    setup_script_parameters_list = self.get_setup_script_parameters(num_test_copies)
               
                # main loop
                if job_launcher_parameters_list:
                    for index,job_launcher_parameters in enumerate(job_launcher_parameters_list):
                        (job_label,launcher_parameters,num_PEs,node_list_string) = job_launcher_parameters
                        
                        # get the test attributes from the component_options 
                        test_attributes = self.get_test_attributes(job_label,node_list_string)
                        #look to see if there is a custom test script parameter list for this iteration
                        if test_attributes: 
                            test_script_parameters_string = self.get_test_script_parameters(1,node_list_string,num_PEs,job_label) 
                            if test_script_parameters_string:
                                test_attributes['test_script_parameters'] = test_script_parameters_string

                        job_launcher_prefix = self.get_job_launcher_prefix(job_label,launcher_parameters,num_PEs,node_list_string)
                        
                        environment_variables_list = self.get_environment_vars_list(job_label,launcher_parameters,num_PEs,node_list_string)
		                
                        #deprecate this?
                        if 'single_logfile_per_job' in self.component_options and self.component_options['single_logfile_per_job']:
                    	    test_attributes['single_logfile_per_job_node_list_string'] = node_list_string  

                        # get the setup attributes from the component_options 
                        setup_attributes = self.get_setup_attributes(job_label)
                        #look to see if there is a custom setup script parameter list for this iteration
                        if setup_attributes and setup_script_parameters_list and len(setup_script_parameters_list)>=index+1 and setup_script_parameters_list[index]:
                            (setup_label,setup_parameter_string,num_PEs,setup_node_list_string) = setup_script_parameters_list[index]
                            if setup_parameter_string:
                                setup_attributes['setup_script_parameters'] = setup_parameter_string
                        else:
                            if self.verbose:
                                self.logger.debug("did not set setup_script_parameters")
                                self.logger.debug("setup_attributes: " + self.sysconfig.dump_data(setup_attributes))
                                self.logger.debug("setup_script_parameters_list: " + self.sysconfig.dump_data(setup_script_parameters_list))
                        
                        if test_attributes and 'test_work_path' in test_attributes and test_attributes['test_work_path']:
                            validated_command = {}
                            #transfer the key/value pairs from the attribute dictionaries to the validated_command
                            validated_command.update(test_attributes)
                            validated_command.update(setup_attributes)
                            
                            # tack on the job_launcher_parameters
                            if use_reservation: 
                                launcher_parameters = "--reservation=" + use_reservation + launcher_parameters
                            validated_command['job_launcher_parameters'] = launcher_parameters
                            
                            # tack on the node_list_string 
                            validated_command['node_list_string'] = node_list_string 
                            
                            # tack on the job_launcher_prefix
                            validated_command['job_launcher_prefix'] = job_launcher_prefix
                            
                            # tack on the list of environment variables 
                            validated_command['environment_variables_tuple_list'] = environment_variables_list 
                            
                            # now append this validated command object onto the local validated_commands list 
                            validated_commands.append(validated_command) 
                            if self.verbose: 
                                self.logger.debug("appending validated_command: " + self.sysconfig.dump_data(validated_command))
                        else:
                            validation_errors.append("validate_component_options: test_work_path attribute missing")
                elif not self.report_mode:
                    validation_errors.append("validate_component_options: no test commands created due to empty list of job launcher parameters")

            else:
                error_message = "validate_component_options: test_script is undefined"
                validation_errors.append(error_message)
                self.logger.error(error_message)
        else:
            error_message = "validate_component_options: component_options dict is undefined"
            validation_errors.append(error_message)
            self.logger.error(error_message)
        
        #concatenate the local list of validated_commands with the global list
        self.validated_test_commands = self.validated_test_commands + validated_commands 
        return validation_errors
        
    def get_setup_attributes(self,copy_dir_name=None):                        
            
        attribute_dict = {} 
                
        if 'setup_script_parameters' in self.component_options and self.component_options['setup_script_parameters'] is not None:
            setup_script_parameters = self.component_options['setup_script_parameters']
        else: 
            setup_script_parameters = None 

        if 'setup_script' in self.component_options and self.component_options['setup_script'] is not None and len(self.component_options['setup_script']) > 0:
            if 'setup_script_source_dir' in self.component_options and self.component_options['setup_script_source_dir'] is not None:
                if not self.component_options['setup_script_source_dir'].startswith("/"):
                    self.component_options['setup_script_source_dir'] = self.FULL_PATH_TO_WORKLOAD_DIR + "/" + self.component_options['setup_script_source_dir']
                    if self.verbose: 
                        self.logger.debug("setup_script_source_dir after update: " + self.component_options['setup_script_source_dir'])
                setup_source_path = self.component_options['setup_script_source_dir'] + "/" + self.component_options['setup_script']
                if copy_dir_name: 
                    setup_work_path = self.work_root + "/" + copy_dir_name + "/" + self.component_options['setup_script'] 
                else:
                    setup_work_path = self.work_root + "/" + self.component_options['setup_script'] 
            else: 
                setup_source_path = None
                setup_work_path = self.component_options['setup_script']
        else:
            setup_source_path = None
            setup_work_path = None
                
        if 'setup_logfile_name' in self.component_options and self.component_options['setup_logfile_name'] is not None:
            setup_logfile_name = self.component_options['setup_logfile_name']
        else: 
            setup_logfile_name = None 
            
        attribute_dict['setup_work_path'] = setup_work_path
        attribute_dict['setup_source_path'] = setup_source_path
        attribute_dict['setup_script_parameters'] = setup_script_parameters
        attribute_dict['setup_logfile_name'] = setup_logfile_name

        return attribute_dict

    def get_template_arguments(self,test_dictionary):
        #this is a generic implementation which should be overridden by the subclass 
        template_arguments = {} 
        return template_arguments

    def get_arch_specific_attribute_value(self,field_name_root,arch):
        debug = 0
        attribute_value = None
        arch_specific_field_name = field_name_root + "_" + str(arch)
        if self.get_component_option(arch_specific_field_name):
            if debug: self.logger.debug("get_arch_specific_attribute_value(" + field_name_root + "," + str(arch) + ") using arch_specific_field_name: " + arch_specific_field_name)
            attribute_value = self.get_component_option(arch_specific_field_name)
        else:
            if debug: self.logger.debug("get_arch_specific_attribute_value(" + field_name_root + "," + str(arch) + ") using field_name_root: " + field_name_root)
            attribute_value = self.get_component_option(field_name_root)
        return attribute_value
    
    def get_test_attribute_value(self,field_name_root,arch,prefix_type=None):
        attribute_value = None
        if prefix_type:
            #determine type_specific_field_name 
            type_specific_field_name = None 
            
            if self.get_component_option(self.component_test_type + prefix_type): 
                type_specific_field_name = self.get_component_option(self.component_test_type + prefix_type) + "_" + field_name_root
            elif self.get_component_option("diag" + prefix_type): 
                type_specific_field_name = self.get_component_option("diag" + prefix_type) + "_" + field_name_root

            if type_specific_field_name:
                attribute_value = self.get_arch_specific_attribute_value(type_specific_field_name,arch) 
                
        if not attribute_value:
            attribute_value = self.get_arch_specific_attribute_value(field_name_root,arch)

        return attribute_value

    def get_test_attributes(self,copy_dir_name=None,node_list_string=None):

        bin_root_prefix = "_bin_root_prefix"
        etc_root_prefix = "_etc_root_prefix"
        ini_file_prefix = "_ini_file_prefix"

        test_script_field_name = "test_script" 
        test_script_source_dir_field_name = "test_script_source_dir" 
        test_script_parameters_field_name = "test_script_parameters" 
        test_script_ini_field_name = "test_script_ini" 
        test_script_ini_source_dir_field_name = "test_script_ini_source_dir"
        test_logfile_name_field_name = "test_logfile_name"
        test_script_other_required_files_field_name = "test_script_other_required_files"
        test_script_other_required_files_source_dir_field_name = "test_script_other_required_files_source_dir" 
        
        attribute_dict = {}
        arch = None 
        
        test_script = None
        test_script_source_dir = None 
        test_script_parameters = None
        test_script_ini = None
        test_ini_source_path = None
        test_script_other_required_files = None
        test_other_required_files_source_path = None
        test_logfile_name = None
        test_work_path = None
        test_source_path = None
        
        node_list = []
        node_list_representative = None 

        if node_list_string:
            node_list = self.sysconfig.expand_node_list(node_list_string)
            if node_list:
                node_list_representative = node_list[0]
                attribute_dict['test_script_ini_mem_size'] = self.mem_size_dict[str(node_list_representative)] 
                attribute_dict['test_script_ini_num_cores'] = self.num_cores_dict[str(node_list_representative)]
                attribute_dict['gpu_model_names'] = self.sysconfig.get_accelerator_model_names_from_node_list(node_list) 
                attribute_dict['node_list_string'] = node_list_string 
        
        #determine component_test_type
        if self.get_component_option("component_test_type"):
            self.component_test_type = self.get_component_option("component_test_type")

        #dynamically determine arch of current node_list
        code_names_list = sysconfig.get_node_list_code_names(self.node_code_names_dict,sysconfig.expand_node_list(node_list_string))
        if code_names_list and len(code_names_list)==1:
            arch = code_names_list[0]
       
        #handle dynamic determination of test_script value
        test_script = self.get_test_attribute_value(test_script_field_name,arch,bin_root_prefix)
        
        #handle dynamic determination of test_script value
        test_script_source_dir = self.get_test_attribute_value(test_script_source_dir_field_name,arch,bin_root_prefix) 
        
        #handle arch and wlm macro-expansions; initialize test_source_path and test_work_path 
        if test_script_source_dir:        
            if "<arch>" in test_script_source_dir:
                test_script_source_dir = test_script_source_dir.replace("<arch>",arch)
                
            if "<wlm>" in test_script_source_dir and self.wlm:
                test_script_source_dir = test_script_source_dir.replace("<wlm>",self.wlm.lower())
                
            if not test_script_source_dir.startswith("/"):
                test_script_source_dir = self.FULL_PATH_TO_WORKLOAD_DIR + "/" + test_script_source_dir
        
            test_source_path = test_script_source_dir + "/" + test_script 
            if copy_dir_name: 
                test_work_path = self.work_root + "/" + copy_dir_name + "/" + test_script 
            else:
                test_work_path = self.work_root + "/" + test_script
        else:        
            test_work_path = test_script 
        
        #handle dynamic determination of test_script_parameters value
        test_script_parameters = self.get_test_attribute_value(test_script_parameters_field_name,arch,bin_root_prefix) 
        
        #handle dynamic determination of test_script_ini value
        test_script_ini = self.get_test_attribute_value(test_script_ini_field_name,arch,ini_file_prefix) 
        
        #handle dynamic determination of test_script_ini_source_dir value
        test_ini_source_path = self.get_test_attribute_value(test_script_ini_source_dir_field_name,arch,ini_file_prefix) 
        if not test_ini_source_path:       
            #allow the ini to inherit the source dir of the test script, which will be a common case
            test_ini_source_path = test_script_source_dir
            
        #handle dynamic determination of test_script_ini_source_dir value
        test_logfile_name = self.get_test_attribute_value(test_logfile_name_field_name,arch) 
        
        #handle dynamic determination of test_script_other_required_files value
        test_script_other_required_files = self.get_test_attribute_value(test_script_other_required_files_field_name,arch) 
        
        #handle dynamic determination of test_script_other_required_files_source_dir value
        test_script_other_required_files_source_dir = self.get_test_attribute_value(test_script_other_required_files_source_dir_field_name,arch) 
        if not test_script_other_required_files_source_dir:
            #allow the other files to inherit the source dir of the test script, which will be a common case
            test_other_required_files_source_path = test_script_source_dir
            
        attribute_dict['test_work_path'] = test_work_path
        attribute_dict['test_source_path'] = test_source_path
        attribute_dict['test_script_parameters'] = test_script_parameters
        attribute_dict['test_script_ini'] = test_script_ini
        attribute_dict['test_ini_source_path'] = test_ini_source_path
        attribute_dict['test_other_files'] = test_script_other_required_files
        attribute_dict['test_other_files_path'] = test_other_required_files_source_path
        attribute_dict['test_logfile_name'] = test_logfile_name
        attribute_dict['arch'] = arch
        return attribute_dict
    
    def get_setup_script_parameter_template(self):
        if 'setup_script_parameters' in self.component_options and self.component_options['setup_script_parameters']:
            return self.component_options['setup_script_parameters']
        else:
            return None
    
    def get_test_script_parameter_template(self):
        if 'test_script_parameters' in self.component_options and self.component_options['test_script_parameters']:
            return self.component_options['test_script_parameters']
        else:
            return None
    
    def get_job_launcher_prefix_template(self):
        if 'job_launcher_prefix_template' in self.component_options and self.component_options['job_launcher_prefix_template']:
            return self.component_options['job_launcher_prefix_template']
        else:
            return "" 
   
    def get_network_job_launcher_parameter_list(self,parameter_template_string):
        name = "bin"
        parameters = []
        
        if self.partition and (self.sysconfig.get_wlm() == self.sysconfig.SLURM):
            total_node_list = self.sysconfig.get_partition_available_node_list(self.partition)
            #self.logger.info("used partition to get total_node_list: " + str(len(total_node_list)))
        else:
            total_node_list = list(self.sysconfig.expand_node_list(self.sysconfig.get_node_list()))

        if total_node_list:
            # check to see if this node_list is a subset of the requested cname list
            if 'user_specified_node_list' in self and self.user_specified_node_list:
                intersection_list = self.sysconfig.get_node_list_intersection(total_node_list,self.user_specified_node_list)
                if intersection_list:
                    node_list = intersection_list
                    node_count = len(intersection_list)
                else:
                    #no node list intersection, so return empty list of aprun parameters 
                    return parameters
            else:
                node_list = total_node_list
                node_count = len(node_list)

            use_single_node_per_blade = False 
            single_node_per_blade_index = None
            if (self.get_component_option("single_node_per_blade_index")):
                use_single_node_per_blade = True 
                single_node_per_blade_index = int(self.get_component_option("single_node_per_blade_index")) 
                if single_node_per_blade_index < 0 or single_node_per_blade_index > 3:
                    single_node_per_blade_index = 0 

            if (use_single_node_per_blade):
                #online network tests have shown the ability to run only when the number of nodes is less 8000
                list_of_single_node_per_blade = self.sysconfig.get_list_single_node_per_blade(single_node_per_blade_index)
                node_list = self.sysconfig.get_node_list_intersection(node_list,list_of_single_node_per_blade)
                node_count = len(node_list)

            number_of_nodes = len(node_list)
            number_of_nodes_per_job = number_of_nodes  
            number_of_jobs = int(number_of_nodes/number_of_nodes_per_job)
            number_of_odd_jobs = number_of_nodes%number_of_nodes_per_job
	    
            for i in xrange(number_of_jobs):
                #get number_of_nodes_per_jobs nids off of intersection_list
                cur_nid_list = node_list[0:number_of_nodes_per_job]
                cur_nid_list_string = self.sysconfig.convert_node_list_to_sparse_string(cur_nid_list)
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
    
    def get_validated_job_launcher_path(self):
        if not self.validated_job_launcher_path:
            #pull the job_launcher_command from the workload_manager_options
            wlm = self.get_wlm()
            if wlm == self.sysconfig.SLURM:
                if 'workload_manager_options' in self and self.workload_manager_options:
                    if 'slurm' in self.workload_manager_options and self.workload_manager_options['slurm']:
                        if 'job_launcher' in self.workload_manager_options['slurm'] and self.workload_manager_options['slurm']['job_launcher']:
                            self.validated_job_launcher_path = self.workload_manager_options['slurm']['job_launcher'] 
            elif wlm == self.sysconfig.ALPS:
                if 'workload_manager_options' in self and self.workload_manager_options:
                    if 'alps' in self.workload_manager_options and self.workload_manager_options['alps']:
                        if 'job_launcher' in self.workload_manager_options['alps'] and self.workload_manager_options['alps']['job_launcher']:
                            self.validated_job_launcher_path = self.workload_manager_options['alps']['job_launcher'] 

        return self.validated_job_launcher_path
    
    def get_wlm(self):
        if not self.wlm:
            self.wlm = self.sysconfig.get_wlm()
        return self.wlm

    def get_environment_variables_template(self):
        if 'environment_variables_template' in self.component_options and self.component_options['environment_variables_template']:
            return self.component_options['environment_variables_template']
        else:
            return "" 

    def get_job_launcher_parameters(self,number_of_test_copies=1):
        
        parameters_list = []
        wlm = self.get_wlm()

        if wlm == self.sysconfig.ALPS:
            parameters_list = self.get_aprun_parameters(number_of_test_copies)        
        elif wlm == self.sysconfig.SLURM:
            parameters_list = self.get_srun_parameters(number_of_test_copies)        
        else:
            self.logger.error("unsupported job_launcher: " + str(wlm))
        
        return parameters_list
    
    def get_srun_parameters(self,number_of_test_copies=1):
        #this is a generic implementation which should be overridden by the subclass 
        parameters_list = []
        return parameters_list
    
    def get_aprun_parameters(self,number_of_test_copies=1):
        #this is a generic implementation which should be overridden by the subclass if/when custom behavior is required
        parameters_list = []
        
        aprun_parameter_template = self.get_aprun_parameter_template()
        if not aprun_parameter_template:
            aprun_parameter_template = "-n WIDTH -N NPPN -L NODE_LIST"

        total_node_list = self.sysconfig.expand_node_list(self.sysconfig.get_node_list())
        if total_node_list:
            total_node_count = len(total_node_list)
            total_node_list 
            #name is a label that can be used for creating additional logging directories 
            name = ""

            if 'user_specified_node_list' in self and self.user_specified_node_list:
                intersection_list = self.sysconfig.get_node_list_intersection(total_node_list,self.user_specified_node_list)
                if intersection_list:
                    node_list = self.sysconfig.convert_node_list_to_sparse_string(intersection_list)
                    node_count = len(intersection_list)
                else:
                    return parameters_list
            else:
                node_list = self.sysconfig.convert_node_list_to_sparse_string(total_node_list)
                node_count = total_node_count
            
            parameter_string = aprun_parameter_template.replace("NPPN",self.get_NPPN())
            parameter_string = parameter_string.replace("WIDTH",str(node_count))
            parameter_string = parameter_string.replace("NODE_LIST",node_list)
            parameters_list.append((name,parameter_string,node_count,node_list))  
        
        return parameters_list
   
    def get_NPPN(self):
        #this is a generic implementation which should be overridden by the subclass if/when custom behavior is required
        return "1"

    def get_aprun_parameter_template(self):
        template = ""
        if 'workload_manager_options' in self and self.workload_manager_options:
            if 'alps' in self.workload_manager_options and self.workload_manager_options['alps']:
                if 'aprun_parameters' in self.workload_manager_options['alps'] and self.workload_manager_options['alps']['aprun_parameters']:
                    template = self.workload_manager_options['alps']['aprun_parameters']
                else:
                    self.logger.error("unable to find aprun_parameters in alps config in workload manager options")
            else:
                self.logger.error("unable to find alps config in workload manager options")
        else:
            self.logger.error("unable to find workload manager options")
        return template
    
    def get_srun_parameter_template(self):
        template = ""
        if 'workload_manager_options' in self and self.workload_manager_options:
            if 'slurm' in self.workload_manager_options and self.workload_manager_options['slurm']:
                if 'srun_parameters' in self.workload_manager_options['slurm'] and self.workload_manager_options['slurm']['srun_parameters']:
                    template = self.workload_manager_options['slurm']['srun_parameters']
                else:
                    self.logger.error("unable to find srun_parameters in slurm config in workload manager options")
            else:
                self.logger.error("unable to find slurm config in workload manager options")
        else:
            self.logger.error("unable to find workload manager options")
        return template
    
    def get_test_script_parameters(self,number_of_test_copies=1,node_list=None,num_PEs=None,job_label=None):
        #this is intended to be overridden by the subclass
        return None 
    
    def get_job_launcher_prefix(self,job_label=None,launcher_parameters=None,num_PEs=None,node_list=None): 
        #this is intended to be overridden by the subclass
        return "" 
    
    def get_environment_vars_list(self,job_label=None,launcher_parameters=None,num_PEs=None,node_list=None):
        environment_vars_list_tuples = []

        environment_variables_template = self.get_environment_variables_template()
        if environment_variables_template:
            environment_vars_list = environment_variables_template.split(";")

            for environment_variable in environment_vars_list:
                environment_variable = environment_variable.split("=")
                environment_vars_list_tuples.append((environment_variable[0],environment_variable[1]))

        return environment_vars_list_tuples    

    def get_setup_script_parameters(self,number_of_test_copies=1):
        #this is intended to be overridden by the subclass
        label = None 
        parameters = None 
        num_PEs = None
        node_list_string = None
        return  [(label,parameters,num_PEs,node_list_string)]
    
    def get_list_of_nids_by_core_size(self,node_list=None):
        nids_per_core_size = []
        
        cores_dictionary = self.sysconfig.get_cores_system()
            
        #figure out how many cores are in the user specified node list
        #by iterating through the cores_dictionary, but first get rid of total_cores attribute
        del cores_dictionary['total_cores']
           
        for core_size in cores_dictionary.keys():
            (num_nodes_for_core_size,list_nids_for_core_size) = cores_dictionary[core_size]
                
            if node_list: 
                intersection_list = self.sysconfig.get_node_list_intersection(node_list,list_nids_for_core_size)
            else:  
                intersection_list = list_nids_for_core_size
                
            if intersection_list:
                nids_per_core_size.append((core_size,intersection_list))
        
        return nids_per_core_size
    
    def get_list_of_nids_by_mem_size(self,node_list=None):
        nids_per_mem_size = []
        mem_dictionary = self.sysconfig.get_mem_size_dictionary()
           
        for mem_size in mem_dictionary["mem_size_nid_lists"].keys():
            list_nids_for_mem_size = mem_dictionary["mem_size_nid_lists"][mem_size]
                
            if node_list: 
                intersection_list = self.sysconfig.get_node_list_intersection(node_list,list_nids_for_mem_size)
            else:  
                intersection_list = list_nids_for_mem_size
                
            if intersection_list:
                nids_per_mem_size.append((mem_size,intersection_list))
        
        return nids_per_mem_size

    def get_num_cores_per_test_copy(self,number_of_test_copies=1,user_specified_node_list=None):
        cores_dictionary = self.sysconfig.get_cores_system()
        total_num_cores_in_system = cores_dictionary['total_cores']
        
        if user_specified_node_list:
            total_num_cores_in_system = 0 
            #figure out how many cores are in the user specified node list
            #by iterating through the cores_dictionary, but first get rid of total_cores attribute
            del cores_dictionary['total_cores']
            for core_size in cores_dictionary.keys():
                (num_nodes_for_core_size,list_nids_for_core_size) = cores_dictionary['core_size']
                intersection_list = self.sysconfig.get_node_list_intersection(user_specified_node_list,list_nids_for_core_size)
                if intersection_list:
                    num_cores_for_core_size = int(core_size) * len(intersection_list)
                    total_num_cores_in_system = total_num_cores_in_system + num_cores_for_core_size

        num_cores_per_copy = total_num_cores_in_system/int(number_of_test_copies)
        
        return num_cores_per_copy

    def validate_workload_manager_options(self,wlm,workload_manager_options):
        validation_errors = []
        if wlm:
            if wlm in workload_manager_options and workload_manager_options[wlm] is not None:
                if wlm == 'pbs':
                    pbs_validation_errors = self.validate_pbs_options(workload_manager_options['pbs'])
                    if pbs_validation_errors:
                        validation_errors.append(pbs_validation_errors)
                elif job_launcher == 'torque':
                    torque_validation_errors = self.validate_torque_options(workload_manager_options['torque'])
                    if torque_validation_errors:
                        validation_errors.append(torque_validation_options)
                else:
                    validation_errors.append("unsupported workload manager: " + wlm)
            else:
                validation_errors.append("wlm is defined as '" + wlm + "', but no " + wlm + " options provided")
        else:
            validation_errors.append("wlm not defined, check ini definition")

        return validation_errors
    
    def validate_job_launcher_options(self,job_launcher,workload_manager_options):
        ## method to verify job_launcher settings are correctly defined
        validation_errors = []
        if job_launcher:
            if job_launcher in workload_manager_options and workload_manager_options[job_launcher] is not None:
                if job_launcher == 'alps':
                    alps_validation_errors = self.validate_alps_options(workload_manager_options['alps'])
                    if alps_validation_errors:
                        validation_errors.append(alps_validation_errors)
                elif job_launcher == 'slurm':
                    slurm_validation_errors = self.validate_slurm_options(workload_manager_options['slurm'])
                    if slurm_validation_errors:
                        validation_errors.append(slurm_validation_errors)
                else:
                    validation_errors.append("unsupported job_launcher: " + job_launcher)
            else:
                validation_errors.append("job_launcher is defined as '" + job_launcher + "', but no " + job_launcher + " options provided")
        else:
            validation_errors.append("job_launcher not defined, check ini definition")
        
        return validation_errors
    
    def validate_alps_options(self,alps_options):
        validation_errors = []
        if alps_options:
            if 'aprun' in alps_options and alps_options['aprun'] is not None:
                if alps_options['aprun'].endswith('aprun'): 
                    pass
                else:
                    validation_errors.append("unable to validate aprun path in alps options")
                
            if 'aprun_parameters' in alps_options and alps_options['aprun_parameters'] is not None:
                self.validated_job_launcher_parameters = alps_options['aprun_parameters'] 
            else:
                validation_errors.append("unable to find aprun_parameters in alps options")
        else:
            validation_errors.append("alps options not provided, unable to validate")
        
        return validation_errors

    def validate_slurm_options(self,slurm_options):
        validation_errors = []
        if slurms_options:
            if 'srun' in slurm_options and slurm_options['srun'] is not None:
                if slurm_options['srun'].endswith('srun'):
                    pass
                else:
                    validation_errors.append("unable to validate srun path in slurm options")
            else:
                validation_errors.append("srun settings not found in slurm options")

        return validation_errors

    def validate_pbs_options(self,pbs_options):
        pass

    def validate_torque_options(self,torque_options):
        pass

    def log_results(self,output_stream,logger=None,max_lines=0):
        if logger:
            try:
                if max_lines > 0: 
                    for i in xrange(max_lines):
                        line = output_stream.readline()
                        if line:
                            logger.info(line.strip("\n"))
                else: 
                    for line in output_stream:
                        logger.info(line.strip("\n"))
            except Exception as e:
                print "log_results caught exception: " + str(e)
        else:
            print "log_results: no logger provided" 


    def run(self):
        status = 0
        test_binary_name = ""
        #self.num_nodes_start = self.sysconfig.get_num_available_nodes()
        self.list_of_previously_copied_files = []
        self.list_of_previously_executed_setup_commands = []
        self.num_jobs_launched = 0
        
        num_jobs_to_launch_before_sleeping = 1 
        if self.get_component_option("num_jobs_to_launch_before_sleeping"):
            num_jobs_to_launch_before_sleeping = int(self.get_component_option("num_jobs_to_launch_before_sleeping"))
        
        job_launch_sleep_duration = .5 
        if self.get_component_option("job_launch_sleep_duration"):
            job_launch_sleep_duration = int(self.get_component_option("job_launch_sleep_duration"))

        if self.dry_run:
            self.logger.info("################### DRY RUN MODE ##################")
        #make sure everything is clear for take-off: no validation errors
        if 'validation_errors' in self and self.validation_errors:
            self.logger.info("run: unable to run due to validation_errors")
            return 1 #non-zero
            
        if 'validated_test_commands' in self and self.validated_test_commands is not None:            
            try:
                additional_ld_library_path_components = []
                #automatically determine proper field name to pull value for test_script_source_dir
                type_specific_additional_ld_library_path_components = "additional_ld_library_path_components"
                if self.get_component_option(self.component_test_type + "_ld_library_prefix"): 
                    type_specific_additional_ld_library_path_components = self.get_component_option(self.component_test_type + "_ld_library_prefix") + "_additional_ld_library_path_components"
                elif self.get_component_option("diag_ld_library_prefix"): 
                    type_specific_additional_ld_library_path_components = self.get_component_option("diag_ld_library_prefix") + "_additional_ld_library_path_components"
                
                if self.get_component_option(type_specific_additional_ld_library_path_components):
                    additional_ld_library_path_components = str(self.get_component_option(type_specific_additional_ld_library_path_components)).split(",")
                    if additional_ld_library_path_components:
                        for add_ld_lib_path_component in additional_ld_library_path_components:
                            add_ld_lib_path_component = ":" + add_ld_lib_path_component
                            #prevent redundant concatentations
                            if 'LD_LIBRARY_PATH' in os.environ and os.environ['LD_LIBRARY_PATH']:
                                os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH'].replace(add_ld_lib_path_component,"") + add_ld_lib_path_component 
                            else:
                                os.environ['LD_LIBRARY_PATH'] = add_ld_lib_path_component 

                #update Library Path
                test_lib_paths = ":" + "/opt/cray/diag/lib"
                if 'LD_LIBRARY_PATH' in os.environ and os.environ['LD_LIBRARY_PATH']:
                    os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH'].replace(test_lib_paths,"") + test_lib_paths
                else:
                    os.environ['LD_LIBRARY_PATH'] = test_lib_paths 
                
                #initialize working directories
                if self.initialize_working_directories(self.validated_test_commands):
                    self.logger.error("run: unable to initialize working directories")
                    return 1 #non-zero
                
                #START run loop here
                number_of_passes = 1 # default
                if 'num_passes' in self and self.num_passes is not None:
                    number_of_passes = int(self.num_passes)
                
                for pass_counter in xrange(number_of_passes):
                    for id,test_dict in enumerate(self.validated_test_commands):
                        node_list_string = test_dict['node_list_string']
                        job_launcher_parameters = test_dict['job_launcher_parameters']
                        if 'job_launcher_prefix' in test_dict: 
                            job_launcher_prefix = test_dict['job_launcher_prefix']
                        else: 
                            job_launcher_prefix = "" 
                        if 'environment_variables_tuple_list' in test_dict: 
                            environment_variables_tuple_list = test_dict['environment_variables_tuple_list']
                        else: 
                            environment_variables_tuple_list = []
                        test_work_path = test_dict['test_work_path']
                        test_source_path = test_dict['test_source_path']
                        test_parameters = test_dict['test_script_parameters']
                        test_logfile_name = test_dict['test_logfile_name']
                        test_script_ini = test_dict['test_script_ini']
                        
                        if 'setup_work_path' in test_dict:
                            setup_work_path = test_dict['setup_work_path']
                        else:
                            setup_work_path = None 

                        if 'setup_source_path' in test_dict:
                            setup_source_path = test_dict['setup_source_path']
                        else:
                            setup_source_path = None 
                        
                        if 'setup_script_parameters' in test_dict:
                            setup_parameters = test_dict['setup_script_parameters']
                        else:
                            setup_parameters = None 
                        
                        if 'setup_log_filename' in test_dict:
                            setup_log_filename = test_dict['setup_log_filename']
                        else:
                            setup_log_filename = None 

                        #self.validated_test_commands[id]['num_nodes_start'] = self.sysconfig.get_num_available_nodes()

                        # if present, run the setup_command
                        if setup_work_path:
                            if setup_parameters:
                                setup_command = setup_work_path + " " + setup_parameters
                            else:
                                setup_command = setup_work_path
                            if self.verbose: 
                                print "setup_command: " + setup_command 
                            
                            setup_logger = None
                            setup_work_dir = os.path.dirname(setup_work_path)
                            if setup_log_filename:
                                if self.verbose: 
                                    print "self.get_logger(" + setup_work_dir + "/" + setup_log_filename + ")"
                                setup_logger = self.get_logger(setup_work_dir + "/" + setup_log_filename)
                            else:
                                setup_logger = None
                            #RUN THE SETUP SCRIPT
                            if not self.dry_run:
                                if not str(setup_command) in self.list_of_previously_executed_setup_commands:
                                    self.logger.info("running setup command \"" + str(setup_command) + "\" for test[" + str(id) + "]")
                                    result = self.sysconfig.run_shell_command(setup_command,setup_logger,setup_work_dir) 
                                    if result:
                                        self.logger.error("setup command \"self.sysconfig.run_shell_command(" + str(setup_command) + ",setup_logger," + setup_work_dir + ")\" returned non-zero: " + str(result) + " skipping test[" + str(id) + "]")
                                        self.main_return_status = 1 #non-zero
                                        if 'fail_on_error' in self and self.fail_on_error:
                                            break
                                        else:
                                            continue #skip to next test command
                                    else:
                                        self.list_of_previously_executed_setup_commands.append(str(setup_command))

                        if test_work_path:

                            test_binary_name = os.path.basename(test_work_path)
                            if not test_binary_name in self.running_test_script_names:
                                self.running_test_script_names.append(test_binary_name)
                            test_work_dir = os.path.dirname(test_work_path)
                            test_command = test_work_path
                            if test_parameters:
                                test_command = test_command + " " + test_parameters
                
                            if self.get_component_option("parse_test_script"):
                                template_arguments = self.get_template_arguments(test_dict)
                                published_path = self.sysconfig.publish_script_template(template_arguments)
                           
                            #update environment variables
                            if environment_variables_tuple_list:
                                for (var_name,var_value) in environment_variables_tuple_list:
                                    os.environ[var_name] = str(var_value)
	                    
                            #append job_launcher and settings
                            job_launcher_command = None
                            validated_job_launcher_path = str(self.get_validated_job_launcher_path())
                            skip_test_command_suffix = 0 
                            if job_launcher_parameters:
                                if self.sysconfig.get_wlm() == self.sysconfig.SLURM and ("srun" in validated_job_launcher_path):
                                    #optimization for SLURM job deployment
                                    #job_launcher_command = job_launcher_prefix + " " + validated_job_launcher_path + " " + job_launcher_parameters + " --bcast=/tmp/" + test_binary_name + " --compress=lz4"
                                    job_launcher_command = job_launcher_prefix + " " + validated_job_launcher_path + " " + job_launcher_parameters + " --bcast=/tmp/" + test_binary_name 
                                else:
                                    job_launcher_command = job_launcher_prefix + " " + validated_job_launcher_path + " " + job_launcher_parameters
                            elif 'validated_job_launcher_parameters' in self and self.validated_job_launcher_parameters:
                                #this is the default case: use the job_launcher params straight out of the ini
                                job_launcher_command = validated_job_launcher_path + " " + self.validated_job_launcher_parameters
                            elif self.verbose:
                                self.logger.debug("run: no job_launcher_parameters defined: [" + str(self.validated_job_launcher_parameters) + "]")

                            #this is the test command that will be launched
                            if skip_test_command_suffix: 
                                test_command = job_launcher_command 
                            else:
                                test_command = job_launcher_command + " " + test_command
                            if self.dry_run:
                                self.logger.info("run: dry-run skipping test_command[" + str(id) + "]: " + test_command)
                                pass
                            else:
                                if (self.num_jobs_launched > 0) and ((self.num_jobs_launched % num_jobs_to_launch_before_sleeping) == 0):
                                    print "sleeping " + str(job_launch_sleep_duration) + "  seconds"
                                    time.sleep(job_launch_sleep_duration)
				
                                #LAUNCH THIS TEST
                                if 'single_logfile_per_job_node_list_string' in test_dict and test_dict['single_logfile_per_job_node_list_string']:
                                    self.skip_spin_wait_logging = True 
                                    job_sub_dir = self.work_root + "/job_log/" + self.session_timestamp
                                    if not os.path.isdir(job_sub_dir):
                                        os.makedirs(job_sub_dir)
                                    
                                    node_component_list = sysconfig.expand_node_list(test_dict['single_logfile_per_job_node_list_string']) 
                                    node_component = sysconfig.convert_node_list_to_sparse_string(node_component_list,use_cnames=False)
                                   
                                    
                                    single_job_log_file_path = job_sub_dir + "/" + self.MODULE_NAME + "_" + self.session_timestamp + "_" + node_component + ".log"
                                    #truncate log file names that are too long 
                                    if len(single_job_log_file_path) >= 200:
                                        first_node_component = sysconfig.convert_node_list_to_sparse_string([node_component_list[0]],use_cnames=False)
                                        missing_node_component = "_more_" 
                                        last_node_component = sysconfig.convert_node_list_to_sparse_string([node_component_list[-1]],use_cnames=False)
                                        shortened_node_component = first_node_component + missing_node_component + last_node_component 
                                        single_job_log_file_path = job_sub_dir + "/" + self.MODULE_NAME + "_" + self.session_timestamp + "_" + shortened_node_component + ".log"

                                    single_job_log = None 
                                    
                                    if "STDOUT" in test_command:
                                        test_command = test_command.replace("STDOUT",single_job_log_file_path)
                                    else:
                                        single_job_log = open(single_job_log_file_path,'a',0)
                                        #write the sparse node list string to the first line of the log file
                                        single_job_log.write("node_info: " + json.dumps(self.sysconfig.get_node_list_cpu_cores_mem_types_dict(node_component_list,self.node_info_dict,self.num_cores_dict,self.mem_size_dict)) + "\n")
                                        self.single_job_logfile_handles.append(single_job_log) 
                                    
                                    if "STDERR" in test_command:
                                        single_job_error_log_file_path = job_sub_dir + "/" + self.MODULE_NAME + "_" + self.session_timestamp + "_" + test_dict['single_logfile_per_job_node_list_string'].replace(",","_") + "_error.log"
                                        test_command = test_command.replace("STDERR",single_job_error_log_file_path)
                                    
                                    #set WTS-specific environment variables for use in batch scripts
                                    os.environ["WTS_JOB_LOG"] = single_job_log_file_path 
                                    os.environ["WTS_JOB_ERROR_LOG"] = self.error_log_file_name 
                                    
                                    self.logger.info("run: launching test_command[" + str(id) + "]: " + test_command)
                                    proc = subprocess.Popen(shlex.split(test_command.encode('ascii')),stdout=single_job_log,stderr=self.error_log,cwd=test_work_dir,env=os.environ.copy())
                                    
                                    #need to close these log files at the end

                                    self.single_job_logfiles.append(single_job_log_file_path) 
                                    self.single_job_error_logfiles.append(single_job_log_file_path) 
                                    self.validated_test_commands[id]['test_logfile_name'] = single_job_log_file_path 
                                    proc_logger_tuple = (proc,None)

                                else:
                                
                                    if test_logfile_name:
                                        self.validated_test_commands[id]['test_logfile_name'] = test_work_dir + "/" + test_logfile_name + "_" + self.session_timestamp + ".log" 
                                    elif self.get_component_option("application_managed_logfile_name"):
                                        self.validated_test_commands[id]['test_logfile_name'] = test_work_dir + "/" + self.get_component_option("application_managed_logfile_name") 
                                    else:
                                        self.validated_test_commands[id]['test_logfile_name'] = self.log_file_name 
                                    
                                    if "STDOUT" in test_command:
                                        test_command = test_command.replace("STDOUT",self.validated_test_commands[id]['test_logfile_name'])
                                    if "STDERR" in test_command:
                                        test_command = test_command.replace("STDERR",self.error_log_file_name)
                                    
                                    #set WTS-specific environment variables for use in batch scripts
                                    os.environ["WTS_JOB_LOG"] = self.validated_test_commands[id]['test_logfile_name'] 
                                    os.environ["WTS_JOB_ERROR_LOG"] = self.error_log_file_name 
                                    
                                    self.logger.info("run: launching test_command[" + str(id) + "]: " + test_command)
                                    proc = subprocess.Popen(shlex.split(test_command.encode('ascii')),stdout=subprocess.PIPE,stderr=self.error_log,cwd=test_work_dir,env=os.environ.copy())
                                    
                                    if test_logfile_name:
                                        proc_logger_tuple = (proc,self.get_logger(self.validated_test_commands[id]['test_logfile_name']))
                                    elif self.get_component_option("application_managed_logfile_name"):
                                        proc_logger_tuple = (proc,self.logger)
                                    else:
                                        proc_logger_tuple = (proc,self.logger)

                                self.running_test_procs.append(proc_logger_tuple)
                                self.num_jobs_launched = self.num_jobs_launched + 1
                                
                                if 'run_test_copies_concurrently' in self and self.run_test_copies_concurrently:
                                    #leave the logging to do_spin_wait 
                                    continue
                                else:
                                    if self.wall_clock_time_limit_value: 
                                        #self.logger.info("running sequentially, doing spin wait for maximum time limit of " + str(self.wall_clock_time_limit_value) + self.wall_clock_time_limit_unit)
                                        killable_apids = self.do_spin_wait(self.current_user_name,[test_binary_name],self.wall_clock_time_limit_unit,self.wall_clock_time_limit_value,self.seconds_until_launch_failure)
                                        if killable_apids: 
                                            self.logger.error("max runtime elapsed, killing " + str(len(killable_apids)) + " apids: " + str(killable_apids))
                                            self.sysconfig.kill_user_jobs(self.current_user_name,killable_apids)
                                    else:
                                        #self.logger.info("running sequentially, no spin wait ")
                                        if proc and proc.stdout: 
                                            for line in proc.stdout: self.logger.info(line.strip("\n"))
                                        errcode = proc.returncode
                                        self.running_test_procs.remove(proc_logger_tuple)

                    #END of the validated test command for loop
                    if not self.dry_run and self.running_test_procs:
                        #save list of apids for post processing usage
                        time.sleep(2)
                        self.apids = self.sysconfig.get_apids_by_name(self.current_user_name,test_binary_name,self.partition)
                        if 'run_test_copies_concurrently' in self and self.run_test_copies_concurrently:
                            if self.wall_clock_time_limit_value: 
                                self.logger.info("doing spin wait for maximum time limit of " + str(self.wall_clock_time_limit_value) + self.wall_clock_time_limit_unit)
                            else:
                                self.logger.info("self.wall_clock_time_limit_value: " + str(self.wall_clock_time_limit_value))
                                self.logger.info("waiting for all " + str(len(self.running_test_procs)) + " subprocesses to finish running")
                            #test_binary_name will be the name of the last test that was launched in the test command for loop
                            killable_apids = self.do_spin_wait(self.current_user_name,self.running_test_script_names,self.wall_clock_time_limit_unit,self.wall_clock_time_limit_value,self.seconds_until_launch_failure)
                            if killable_apids: 
                                self.logger.error("max runtime elapsed, killing " + str(len(killable_apids)) + " apids: " + str(killable_apids))
                                self.sysconfig.kill_user_jobs(self.current_user_name,killable_apids) 
            
            #END of number of passes 
            except KeyboardInterrupt as e:
                for (proc,logger) in self.running_test_procs:
                    proc.kill()
                user_response = raw_input("\nContinue to next test? Press Y or y followed by enter key\nTo exit completely, just hit return\n")
                if user_response.lower() == "y":
            	    self.logger.info("Continuing to next test")
                else:
                    raise
                    #user sent Ctrl-C, kill all of the running test processes
        else:
            self.logger.error("run: validated_test_commands is empty or undefined") 
       
        #close any files that were opened
        if self.single_job_logfile_handles:
	        for single_job_logfile_handle in self.single_job_logfile_handles:
		        if not single_job_logfile_handle.closed:
		            single_job_logfile_handle.close() 
        
        if self.single_job_error_logfiles:
	        for single_job_error_logfile_handle in self.single_job_error_logfile_handles:
		        if not single_job_error_logfile_handle.closed:
		            single_job_error_logfile_handle.close() 
        
        #run general error log searchs
        execution_error_list = self.check_for_execution_errors(self.error_keyword_list)
        if execution_error_list:
            for error in execution_error_list:
                print error
                if self.slurm_memory_error_limit_string in error: 
                    print "It will be necessary to relax SLURM memory limits in order to properly run this test"
            status = 1
            self.main_return_status = 1
        
        self.num_nodes_end_run = self.sysconfig.get_num_available_nodes()
        return status

    def do_spin_wait(self,user_name,test_name,time_limit_unit="m",time_limit_value=None,seconds_until_launch_failure=300):
        #self.logger.info("base_test_component: entering do_spin_wait")
        query_frequency = 4 #every 4 seconds
        elapsed_launch_seconds = 0 #counter to keep track of number of elapsed seconds
        spinner = sysconfig.spinning_cursor()
        apids = self.sysconfig.get_apids_by_name(user_name,test_name)
        
        if not apids:
            if self.apids:
                apids = self.apids
                #self.logger.info("do spin wait: starting self.apids: " + str(apids))
            else:
                self.logger.info("do spin wait: looping to determine apids")
                while not apids:
                    if elapsed_launch_seconds >= seconds_until_launch_failure:
                        sys.stdout.write('\n')
                        self.logger.info("do_spin_wait: no apids found after " + str(elapsed_launch_seconds) + " seconds, something has gone wrong")
                        break 
                    for iteration in range(query_frequency):
                        elapsed_launch_seconds = elapsed_launch_seconds + 1
                        status_string = spinner.next() + " remaining seconds until launch failure: " + str(seconds_until_launch_failure - elapsed_launch_seconds) + "         "
                        sys.stdout.write(status_string)
                        sys.stdout.flush()
                        time.sleep(1)
                        sys.stdout.write('\b' * len(status_string))
                    apids = self.sysconfig.get_apids_by_name(user_name,test_name)
        
        if not self.apids: 
            self.apids = apids
         
        #self.logger.info("base_test_component: do_spin_wait starting spin with apids: " + str(apids))
        while apids:
            
            #push process output into log 
            if not self.skip_spin_wait_logging and self.running_test_procs:
                for id,(proc,logger) in enumerate(self.running_test_procs):
                    self.log_results(proc.stdout,logger,40)
            
            # check to see if time limit has been reached
            if time_limit_value:
                # check to see if time limit has been reached
                test_ages = self.sysconfig.get_age_user_jobs(user_name,apids)
                if test_ages:
                    for id,(apid,hours,mins) in enumerate(test_ages):
                        elapsed_mins = (hours * 60) + mins
                        #self.logger.debug(test_name + ": " + str(len(test_ages)) + " test_ages, test_age[" + str(id) + "]: " + str(apid) + ", " + str(elapsed_mins))
                        if time_limit_unit == "h":
                            if hours >= time_limit_value:
                                return apids 
                        elif elapsed_mins >= time_limit_value:
                            #self.logger.error("reached time_limit_value in mins: " + str(time_limit_value))
                            return apids
                else:
                    #no ages found, assume all jobs have finished
                    #self.logger.info("test completed: no age found for user_name [" + user_name + "], apids " + str(apids))
                    return []
            
            for _ in range(10):
                sys.stdout.write(spinner.next())
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b')
                time.sleep(0.1)
            apids = self.sysconfig.get_apids_by_name(user_name,test_name)
        
        #self.logger.info("base_test_component: leaving do_spin_wait")
        
        return apids 
    
    def initialize_working_directories(self,validated_test_commands):
        #TODO: add checks to avoid use of system directory names, ie /
        #TODO: create a list of previously copied files to avoid doing unnecessary duplicate copying
        
        list_of_allowed_other_source_wildcard_dirs = ["/opt/intel/mkl/benchmarks/mp_linpack/bin_intel/intel64"]
        if validated_test_commands: 
            for i,test_command in enumerate(validated_test_commands):
                #self.logger.info(self.dump_data(test_command)) 
                #self.logger.info(self.dump_data(self.list_of_previously_copied_files)) 
                if 'test_source_path' in test_command and test_command['test_source_path'] and os.path.exists(test_command['test_source_path']):
                    work_dir = os.path.dirname(test_command['test_work_path'])
                    if not os.path.isdir(work_dir):
                        os.makedirs(work_dir)
                    if not (test_command['test_work_path'] in self.list_of_previously_copied_files) and not (os.path.lexists(test_command['test_work_path'])) and not self.get_component_option("parse_test_script"):
                        self.list_of_previously_copied_files.append(test_command['test_work_path'])
                        os.symlink(test_command['test_source_path'],test_command['test_work_path'])
                else:
                    error_message = "unable to locate " + str(test_command['test_source_path']) + ", aborting execution"
                    self.logger.error(error_message)
                    return error_message 
                
                if 'setup_source_path' in test_command and test_command['setup_source_path'] and os.path.exists(test_command['setup_source_path']):
                    setup_dir = os.path.dirname(test_command['setup_work_path'])
                    if not os.path.isdir(setup_dir):
                        os.makedirs(setup_dir)
                    if not (test_command['setup_work_path'] in self.list_of_previously_copied_files):
                        self.list_of_previously_copied_files.append(test_command['setup_work_path'])
                        shutil.copy(test_command['setup_source_path'],test_command['setup_work_path'])
                
                if 'test_script_ini' in test_command and test_command['test_script_ini']:
                    if 'test_ini_source_path' in test_command and test_command['test_ini_source_path']:
                        #self.logger.error("test_ini_source_path: " + test_command['test_ini_source_path'])
                        if test_command['test_ini_source_path'] == "<test_script_dir>":
                            test_command['test_ini_source_path'] = self.FULL_PATH_TO_SCRIPT_DIR 
                         
                        if "|" in test_command['test_script_ini']:
                            source_target_list  = test_command['test_script_ini'].split("|")
                            source_file_name = source_target_list[0]
                            if 'test_script_ini_num_cores' in test_command and test_command['test_script_ini_num_cores']:
                                source_file_name = source_file_name.replace("NUM_CORES",test_command['test_script_ini_num_cores'])
                            if 'test_script_ini_mem_size' in test_command and test_command['test_script_ini_mem_size']:
                                source_file_name = source_file_name.replace("MEM_SIZE",test_command['test_script_ini_mem_size'])
                            target_file_name = source_target_list[1]
                        else:
                            source_file_name = test_command['test_script_ini'] 
                            target_file_name = test_command['test_script_ini'] 

                        
                        ini_source_path = test_command['test_ini_source_path'] + "/" + source_file_name 
                        if os.path.isfile(ini_source_path):
                            # copy the ini file at ini_source_path to the work dir 
                            ini_work_path = os.path.dirname(test_command['test_work_path']) + "/" + target_file_name 
                            if not (ini_work_path in self.list_of_previously_copied_files):
                                self.list_of_previously_copied_files.append(ini_work_path)
                                shutil.copy(ini_source_path,ini_work_path)
                        else:
                            error_message = "unable to locate ini file at source path: " + str(ini_source_path) + ", aborting execution"
                            self.logger.error(error_message)
                            return error_message 
                    else:
                        error_message = "ini file source path undefined, aborting execution"
                        self.logger.error(error_message)
                        return error_message 
                
                if 'test_other_files' in test_command and test_command['test_other_files']:
                    #self.logger.error("test_other_files: " + test_command['test_other_files']) 
                    test_other_files_list = test_command['test_other_files'].split(",")
                    if test_other_files_list:
                        for i,other_file_name in enumerate(test_other_files_list):
                            
                            #TODO: handle file_names that start with a forward slash differently
                            if other_file_name.startswith("/"):
                                other_file_components = other_file_name.split("/")
                                if other_file_components:
                                    target_file_name = other_file_components[-1]
                                other_file_source_path = other_file_name
                                if os.path.isfile(other_file_source_path):
                                    # copy the other file at other_files_source_path to the work dir 
                                    other_file_work_path = os.path.dirname(test_command['test_work_path']) + "/" + target_file_name 
                                    if not (other_file_work_path in self.list_of_previously_copied_files):
                                        self.list_of_previously_copied_files.append(other_file_work_path)
                                        shutil.copy(other_file_source_path,other_file_work_path)
                                continue

                            if "|" in other_file_name:
                                source_target_list  = other_file_name.split("|")
                                source_file_name = source_target_list[0]
                                target_file_name = source_target_list[1]
                            else:
                                source_file_name = other_file_name 
                                target_file_name = other_file_name 
                            
                            if 'test_other_files_path' in test_command and test_command['test_other_files_path']:
                                if "*" in source_file_name:
                                    #self.logger.error("source_file_name contains a wildcard: " + source_file_name) 
                                    #verify that test_other_files_path is in the list of allowed source paths
                                    if test_command['test_other_files_path'] in list_of_allowed_other_source_wildcard_dirs:
                                        other_file_source_path = test_command['test_other_files_path'] + "/" + source_file_name 
                                        #self.logger.error("handling allowed wildcard source path: " + other_file_source_path) 
                                        #now copy all the files in that source dir over
                                        for filename in glob.glob(os.path.join(test_command['test_other_files_path'],source_file_name)):
                                            #self.logger.error("filename: " + filename + "," + os.path.dirname(test_command['test_work_path']))
                                            full_target_file_name = os.path.dirname(test_command['test_work_path']) + "/" + filename
                                            if not (full_target_file_name in self.list_of_previously_copied_files):
                                                self.list_of_previously_copied_files.append(full_target_file_name)
                                                shutil.copy(filename,os.path.dirname(test_command['test_work_path']))
                                    else:
                                        self.logger.error("skipping un-allowed wildcard source path: " + test_command['test_other_files_path']) 
                                else:
                                    other_file_source_path = test_command['test_other_files_path'] + "/" + source_file_name 
                                    #self.logger.error("doing copy to: " + other_file_source_path) 
                                    if os.path.isfile(other_file_source_path):
                                        # copy the other file at other_files_source_path to the work dir 
                                        other_file_work_path = os.path.dirname(test_command['test_work_path']) + "/" + target_file_name 
                                        if not (other_file_work_path in self.list_of_previously_copied_files):
                                            self.list_of_previously_copied_files.append(other_file_work_path)
                                            shutil.copy(other_file_source_path,other_file_work_path)
                            else:
                                error_message = "initialize_working_directories: other files source path undefined, aborting execution"
                                self.logger.error(error_message)
                                return error_message 
                    else:
                        error_message = "test other files list empty after split, aborting execution"
                        self.logger.error(error_message)
                        return error_message 

        return 0 
    
    def post_run_tasks(self):
        #dump proc info to logs
        try:
            if 'running_test_procs' in self and self.running_test_procs:
                for (proc,logger) in self.running_test_procs:
                    if proc.stdout:
                        if logger:
                            for out_line in proc.stdout:
    		                    logger.info(out_line.strip("\n"))
                for i,(proc,logger) in enumerate(self.running_test_procs):
                    del proc 
        except Exception as e:
            self.logger.info("Post run tasks caught exception: " + str(e))
    
    def report(self,dump=True):

        self.logger.info("report: searching for keywords: " + str(self.error_keyword_list))
        log_file_name_list = []
        #log_file_name_list.append(self.log_file_name)
        #log_file_name_list.append(self.error_log_file_name)
        #log_file_name_list = log_file_name_list + self.single_job_logfiles 
        #log_file_name_list = log_file_name_list + self.single_job_error_logfiles 
        for validated_command in self.validated_test_commands:
            if 'test_logfile_name' in validated_command and validated_command['test_logfile_name']:
                log_file_name_list.append(validated_command['test_logfile_name'])

        error_tuples_list = self.check_logs(log_file_name_list,self.error_keyword_list,0,self.error_match_exclusion_list)
        if error_tuples_list:
            for (timestamp,cname,error_message) in error_tuples_list:
                failure_message = "\n" + timestamp
                if cname:
                    failure_message = failure_message + ": " + cname
                failure_message = failure_message + ": " + error_message
                #if not log_file_name == self.error_log_file_name and not log_file_name == self.log_file_name:
                #if not log_file_name == self.error_log_file_name:
                self.error_log.write(failure_message)
            self.main_return_status = (len(error_tuples_list),self.error_log_file_name) 
        else:
            self.logger.info("report: all checks passed")
            self.main_return_status = 0 
        
        num_available_nodes = self.sysconfig.get_num_available_nodes()
        if 'num_nodes_start' in self and self.num_nodes_start:
            num_nodes_start = self.num_nodes_start
            node_difference  = int(num_available_nodes) - int(num_nodes_start)
            if node_difference > 0: 
                self.logger.info(str(node_difference) + " nodes came up since start of test")
            elif node_difference < 0:
                self.logger.info(str(node_difference) + " nodes went down since start of test")

        self.logger.info(str(num_available_nodes) + " nodes available after completion of test")
        
        if dump:
            outfile_name = self.work_root + "/" + self.MODULE_NAME + ".last_state.json"
            #self.logger.info("dumping test state to outfile: " + outfile_name)
            self.dump_state_as_json(outfile_name)

    def check_logs(self,log_file_name_list,error_keyword_list,case_sensitive=0,error_match_exclusion_list=None):
        self.verbose = 0 
        error_tuples_list = []
        if log_file_name_list and len(log_file_name_list)>0:
            if self.verbose: 
                print "looking for the following error keyword(s): "
                print self.sysconfig.dump_data(error_keyword_list)
                print "in the following " + str(len(log_file_name_list)) + " file(s):"
                print self.sysconfig.dump_data(log_file_name_list)

            for log_file_name in log_file_name_list:
                error_list = self.sysconfig.search_log(log_file_name,error_keyword_list,case_sensitive,error_match_exclusion_list,verify_logfile_is_not_empty=True)
                if error_list:
                    for i,error in enumerate(error_list):
                        #extract timestamp and cnames from filename here
                        #first, get the log parsing details
                        nodeinfo_component_index = self.get_component_option("nodeinfo_component_index")
                        if "," in log_file_name and self.get_component_option("nodeinfo_component_index_alternate"):
                            nodeinfo_component_index = self.get_component_option("nodeinfo_component_index_alternate")
                        if self.verbose:
                            print self.MODULE_NAME + ".check_logs: sysconfig.get_cname_and_timestamp_from_logfile_name(" + log_file_name + "," + str(self.get_component_option("nodeinfo_in_logfile_name")) + "," + str(self.get_component_option("timestamp_path_index")) + "," + str(self.get_component_option("timestamp_component_index")) + "," + str(self.get_component_option("nodeinfo_path_index")) + "," + str(nodeinfo_component_index) + ")" 
                        (timestamp,cnames) = sysconfig.get_cname_and_timestamp_from_logfile_name(log_file_name,self.get_component_option("nodeinfo_in_logfile_name"),self.get_component_option("timestamp_path_index"),self.get_component_option("timestamp_component_index"),self.get_component_option("nodeinfo_path_index"),nodeinfo_component_index) 
                        error_tuples_list.append((timestamp,cnames,error)) 
                        if self.verbose:
                            print "error instance[" + str(i) + "]: " + error
        
        return error_tuples_list

    def get_main_return_status(self):
        return self.main_return_status 

    def load_last_state_as_json(self,last_state_file_name=None):
        doc = {}
        if not last_state_file_name:
            last_state_file_name = self.work_root + "/" + self.MODULE_NAME + ".last_state.json"
        if os.path.isfile(last_state_file_name):
            doc = json.load(open(last_state_file_name))
        else:
            self.logger.info("no results to report - unable to locate last state file: " + last_state_file_name)
        return doc
    
    def get_component_option(self,option_name):
        if not option_name:
            return None
        if "component_options" in self and self.component_options:
            if option_name in self.component_options and self.component_options[option_name]:
                return self.component_options[option_name]
            else:
                return None 
    
    def set_component_option(self,option_name,option_value=None):
        if not option_name:
            return None
        if "component_options" in self:
            self.component_options[option_name] = option_value 

    def dump_state_as_json(self,out_file_name):
        if out_file_name:
            #get rid of non-printable members
            
            self.sysconfig = None    
            
            if self.logger:
                del self.logger
            
            if self.error_log:
                self.error_log.close()
                del self.error_log
        
            if len(self.running_test_procs) > 0:
                self.running_test_procs = None
            
            if len(self.single_job_logfile_handles) > 0:
		        self.single_job_logfile_handles = None 
            
            if len(self.single_job_error_logfile_handles) > 0:
		        self.single_job_error_logfile_handles = None 
            
            if os.path.isfile(out_file_name):
                target_file_name = os.path.dirname(out_file_name) + "/" + self.MODULE_NAME + ".previous_state.json"
                shutil.move(out_file_name,target_file_name)
                if self.verbose: 
                    print "moved " + out_file_name + " to " + target_file_name
                
            out_file_handle = open(out_file_name,"w")
            out_file_handle.write(self.to_JSON())
            out_file_handle.close()

    def get_cname_from_nid_using_cnames_dictionary(self,nid):
        cname = str(nid) 
        nid = int(nid)
        cnames_dictionary = None
        if not ('cnames_dictionary' in self and self.cnames_dictionary):
            cnames_dictionary = sysconfig.get_cnames_dictionary()
            if cnames_dictionary:
                self.cnames_dictionary = cnames_dictionary
        else:
            cnames_dictionary = self.cnames_dictionary
        
        if cnames_dictionary:
            for key in cnames_dictionary.keys():
                if "n" in key and nid in cnames_dictionary[key]: 
                    return key

        return cname
    
    def get_global_error_keyword_list(self):
        if not self.global_error_keyword_list:
            self.global_error_keyword_list = self.get_global_default_option("error_keyword_list")
        return self.global_error_keyword_list

    def get_global_default_option(self,option_name):
        if not self.global_default_options:
            self.parse_global_ini() 
        
        if option_name in self.global_default_options:
            return self.global_default_options[option_name]
        else: 
            return None
    
    def get_global_component_option(self,option_name):
        if not self.global_component_options:
            self.parse_global_ini() 
        
        if option_name in self.global_component_options:
            return self.global_component_options[option_name]
        else: 
            return None
    
    def get_global_test_option(self,test_name,option_name):
        if not self.global_test_options:
            self.parse_global_ini() 
        
        if test_name in self.global_test_options:
            if option_name in self.global_component_options[test_name]:
                return self.global_component_options[test_name][option_name]
            else:
                return None
        else: 
            return None
        
    def component_test_main(self,test_options=None):
        status = 0
        debug = 1 
        
        if test_options and "process_commandline_options" in test_options and test_options["process_commandline_options"]:
            self.process_commandline_options()
        
        if self.initialize(test_options):
            print "test failed: unable to initialize"
        else:
            validation_errors = self.validate_setup()
            if not validation_errors:
                return_value = self.run()
                if return_value:
                    self.logger.error("component_test_main: run method returned non-zero")
                self.post_run_tasks() 
                json_dump_file_name = self.work_root + "/" + self.MODULE_NAME + ".last_state.json"
                self.dump_state_as_json(json_dump_file_name)
                status = self.get_main_return_status()
            else:
                self.logger.error("component_test_main: test failed due to validation errors")
                self.logger.error(validation_errors)
                status = 1
        return status

    def component_check_main(self,test_options=None):
        debug = 1
        
        display_results = False 
        if test_options and 'display_results' in test_options:
            display_results = True 
        
        if test_options and "process_commandline_options" in test_options and test_options["process_commandline_options"]:
            self.process_commandline_options()
        
        if self.initialize(test_options,report_mode=True):
            print "test failed: unable to initialize"
        else:
            component_check_name = self.MODULE_NAME.replace("_test","")
            error_tuples_list = []
            searchable_log_files_list = []
            
            if test_options and 'xtsystest_session_timestamp' in test_options and test_options['xtsystest_session_timestamp']:
                #when component check module is called from xtsystest.py 
                self.reporting_session_timestamp = test_options['xtsystest_session_timestamp']
            
            if self.reporting_session_timestamp:
                if self.get_component_option("single_logfile_per_job"): 
                    if self.verbose: 
                        print "calling sysconfig.get_session_single_job_logfiles"
                    job_logs_root = self.work_root + "/job_log"
                    searchable_log_files_list = sysconfig.get_session_single_job_logfiles(job_logs_root,self.reporting_session_timestamp) 
                elif self.get_component_option("application_managed_logfile_name"):
                    if self.verbose:
                        print "calling sysconfig.get_session_application_managed_logfiles"
                    job_logs_root = self.work_root + "/job_log"
                    searchable_log_files_list = sysconfig.get_session_application_managed_logfiles(job_logs_root,self.get_component_option("application_managed_logfile_name"),self.reporting_session_timestamp)
            else:    
                last_state_dict = self.load_last_state_as_json()
                if last_state_dict:
                    self.reporting_session_timestamp = last_state_dict['session_timestamp']
                    if 'validated_test_commands' in last_state_dict and last_state_dict['validated_test_commands']:
                        for validated_command in last_state_dict['validated_test_commands']:
                            if 'test_logfile_name' in validated_command and validated_command['test_logfile_name']:
                                searchable_log_files_list.append(str(validated_command['test_logfile_name']))
            
            #add top-level component test session and error logs    
            if self.verbose:
                print "calling sysconfig.get_session_component_test_toplevel_logfiles"
            searchable_log_files_list.extend(sysconfig.get_session_component_test_toplevel_logfiles(self.work_root,self.MODULE_NAME,self.reporting_session_timestamp))

            if searchable_log_files_list:
                searchable_log_files_list = list(set(searchable_log_files_list))
                searchable_log_files_list.sort()
                print "\nchecking " + component_check_name + " session " + str(self.reporting_session_timestamp) + " for errors..."
                if self.verbose:
                    print component_check_name + ": calling self.check_logs with params:"
                    print "\tsearchable_log_files_list: " + sysconfig.dump_data(searchable_log_files_list) 
                    print "\terror_keyword_list: " + str(self.error_keyword_list)
                error_tuples_list = self.check_logs(searchable_log_files_list,self.error_keyword_list,0,self.error_match_exclusion_list)
            else:
                print component_check_name + ": no log files"
            
            if display_results:
                if len(error_tuples_list) > 0:
                    self.display_and_log_error_tuples_list(error_tuples_list)
                elif self.verbose:
                    failure_message = component_check_name + ": no errors found\n"
                    print failure_message 

            return error_tuples_list
    
    def display_and_log_error_tuples_list(self,error_tuples_list):
        if error_tuples_list:
            #create/open the output log
            out_file_name = self.work_root + "/session_error_summary_" + self.reporting_session_timestamp + ".log" 
            out_file_handle = open(out_file_name,"a")
            failure_summary_message = "\n" + self.MODULE_NAME + " found " + str(len(error_tuples_list)) + " errors: "
            print failure_summary_message
            out_file_handle.write(failure_summary_message)
            for (timestamp,cname,error_message) in error_tuples_list:
                failure_message = "\n" + timestamp
                if cname:
                    failure_message = failure_message + ": " + cname
                failure_message = failure_message + ": " + error_message
                print failure_message 
                out_file_handle.write(failure_message)
            #close the output log 
            out_file_handle.close()
            print "\nerror summary available here:"
            print out_file_name + "\n"
    
    def get_gpu_test_script_parameters(self,number_of_test_copies=1,node_list_string=None,num_PEs=None,job_label=None):
        test_script_parameters = "" 
        node_list_model_names = sysconfig.get_accelerator_model_names_from_node_list(sysconfig.expand_node_list(node_list_string))
        if node_list_model_names and len(node_list_model_names) > 0:
            model_name = node_list_model_names[0]
            if "P100" in model_name:
                if "12GB" in model_name and self.get_component_option("test_script_parameters_p100_12gb"):
                    test_script_parameters = self.get_component_option("test_script_parameters_p100_12gb")
                else:
                    test_script_parameters = self.get_component_option("test_script_parameters_p100")
            else:
                test_script_parameters = self.get_component_option("test_script_parameters")

        return test_script_parameters 
    
    def get_mem_per_cpu(self,nid):
        mem_per_cpu = None
        
        if self.sysconfig.get_wlm() == self.sysconfig.SLURM and self.sysconfig.get_sconfig_option('MemLimitEnforce'):
            node_mem_size = int(sysconfig.get_node_mem_size(nid))
            node_core_size = int(self.num_cores_dict[str(nid)])
            equal_mem_per_cpu = node_mem_size/node_core_size
            mem_per_cpu = equal_mem_per_cpu
            if self.sysconfig.get_sconfig_option('MaxMemPerCPU') and (self.sysconfig.get_sconfig_option('MaxMemPerCPU') < equal_mem_per_cpu):
                mem_per_cpu = self.sysconfig.get_sconfig_option('MaxMemPerCPU')

        return str(mem_per_cpu)
    
    def check_for_execution_errors(self,error_keyword_list=None):
        
        execution_error_list = []

        error_log_error_list = self.check_error_log(error_keyword_list) 
        if error_log_error_list:
            execution_error_list.extend(error_log_error_list)
        
        session_log_error_list = self.check_session_log(error_keyword_list) 
        if session_log_error_list:
            execution_error_list.extend(session_log_error_list)
        
        memory_error_list = self.check_for_memory_limit_error() 
        if memory_error_list:
            execution_error_list.extend(memory_error_list)
        
        return execution_error_list 
    
    def check_for_memory_limit_error(self,memory_error_string_list=None):
        found_memory_error_list = []
        if not memory_error_string_list: 
            memory_error_string_list = [self.slurm_memory_error_limit_string]
        if self.sysconfig.get_wlm() == self.sysconfig.SLURM and self.sysconfig.get_sconfig_option('MemLimitEnforce'):
           found_memory_error_list = self.check_error_log(memory_error_string_list) 
        return found_memory_error_list
    
    def check_error_log(self,error_string_list=None):
        found_error_list = [] 
        if not error_string_list:
            error_string_list = ["error"]
        if "error_log_file_name" in self and self.error_log_file_name:
            found_error_list = self.sysconfig.search_log(self.error_log_file_name,error_string_list)
        
        return found_error_list
    
    def check_session_log(self,error_string_list=None):
        found_error_list = [] 
        if not error_string_list:
            error_string_list = ["error"]
        if "log_file_name" in self and self.log_file_name:
            found_error_list = self.sysconfig.search_log(self.log_file_name,error_string_list)
        
        return found_error_list
                    
def main(test_options):
    base = BaseTestComponent()
    if base:
        #test some functionality in base
        print "Hello from base"

if __name__ == "__main__":
    test_options = []
    main(test_options)
    
