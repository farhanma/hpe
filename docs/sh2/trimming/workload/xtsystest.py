#!/usr/bin/env python
###############################################################################
# Copyright 2014,2016 Cray Inc. All Rights Reserved.
#
# xtsystest.py - a script that can be used to run an arbitray set of tests
# against an arbitrary set of system resources. 
#
# author: Pete Halseth
#
# The purpose of the xtsystest.py script is to provide a mechanism for grouping
# an arbitray, end-user defined mix of tests together, and then execute them in an ordered
# sequence against an arbitray set of system resources.  
#
# Usage:
# -------
# ./xtsystest.py <options> 
# to see the list of options, type ./xtsystest.py -h
# 
################################################################################
##@package workload
# a basic script to run a list of tests
# this file can be run as a standalone, top-level script
# or imported as module
import os, sys, time, logging, ConfigParser, json, resource, copy
from optparse import OptionParser
from datetime import datetime
# 
# set MODULE_NAME from __file__ magic variable
(file_root,file_name) = os.path.split(os.path.realpath(__file__))
(MODULE_NAME,ext) = os.path.splitext(file_name)

FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
FULL_PATH_TO_UTIL_DIR = FULL_PATH_TO_SCRIPT_DIR + "/util"  

## dictionary to hold module configuration settings
MODULE_CONFIG={}
MODULE_CONFIG['user_options'] = {} 
MODULE_CONFIG['session_timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S%f") 

## standard logger
logger = None 

try:
	from workload.util import system_configuration 
except:
	sys.path.append(os.path.abspath(FULL_PATH_TO_SCRIPT_DIR + "/.."))
	from workload.util import system_configuration 
sysconfig = system_configuration.BaseConfig.factory()

## method to parse commandline options  
def process_commandline_options():
    user_options = {}
    parser = OptionParser(usage="%prog [-h] [-r] [-s SETUPDIR] [-i INIFILEPATH] [-c CNAME] [-d WORKROOT] [-e SECONDS] [-t TESTORDER] [-p PARTITION] [-a RESERVATION] [-k NOPROMPT] [-m MARGIN] [-n NODECOUNT] [-l MAXLOOPS] [-x CNAMEEXCLUSIONS] [-y] [-f] [--version]", version="%prog CAEXC-975")
    
    parser.add_option("-a","--reservation",dest="reservation",default=None,
        help="name of pre-allocated reservation to execute on")

    parser.add_option("-c","--cname",dest="cname",default=None,
        help="a cname value representing the system resources to target")

    parser.add_option("-d","--workroot",dest="workRoot",default=None,
        help="user specified work and log output directory")
    
    parser.add_option("-e","--seconds",dest="secondsUntilLaunchFailure",default=None,
        help="user specified number of seconds until test launch failure")
		
    parser.add_option("-f","--fail",action='store_true',dest="failOnError",
        help="stop test immediately when an error is encountered")
    
    parser.add_option("-i","--ini",dest="iniFilePath",default=None,
        help="path to user specified INI file")
    
    parser.add_option("-k","--noprompt",action='store_true',dest="noPrompt",
        help="skip warning when running against all computes")
    
    parser.add_option("-l","--loops",dest="maxLoops",default=None,
        help="allows setting a limit on the maximum number of iterations")
    
    parser.add_option("-m","--margin",dest="margin",default="",
        help="used as a prefix for log file names to provide additional testing context during post-run analysis")
    
    parser.add_option("-n","--nodecount",dest="nodeCount",default=None,
            help="an integer value representing the number of nodes to run on (note: this is eclipsed by -c/--cname)")
    
    parser.add_option("-p","--partition",dest="partition",default=None,
        help="name of partition to execute on")
    
    parser.add_option("-r","--report",action='store_true',dest="runReport",
        help="generate report using most recent log results")
    
    parser.add_option("-s","--setup",dest="setupDir",default=None,
        help="user specified setup directory")
    
    parser.add_option("-t","--tests",dest="testOrder",default="",
        help="comma-separated, ordered list of test names which can be used to override the list and order of tests to run")
    
    parser.add_option("-w","--session",dest="reportingSessionTimestamp",default=None,
        help="user specified session timestamp for reporting purposes")
    
    parser.add_option("-x","--exclude",dest="cnameExclusions",default=None,
        help="a cname value representing the system resources to exclude")
    
    parser.add_option("-y","--dry",action='store_true',dest="dryRun",
        help="dump config settings and exit")
	
    (options, args) = parser.parse_args()
    if options:
        user_options['run_report']=options.runReport
        user_options['setup_dir']=options.setupDir
        
        if options.iniFilePath:
            input_file_path = sysconfig.expand_and_verify_file_system_path(options.iniFilePath)
            if (input_file_path):
                user_options['input_file_path']=input_file_path
            else:
                #unable to verify user provided ini file path 
                sys.exit("error: invalid ini file path: " + str(options.iniFilePath))
        else:
            user_options['input_file_path']=None
        
        if options.workRoot:
            work_root = sysconfig.expand_and_verify_work_root(options.workRoot)
            if (work_root):
                user_options['work_root']=work_root
            else:
                #unable to verify user provided ini file path 
                sys.exit("error: invalid work root directory: " + str(options.workRoot))
        else:
            user_options['work_root']=None
       
        user_options['cname']=options.cname
        user_options['node_count']=options.nodeCount
        user_options['test_order']=options.testOrder
        user_options['margin']=options.margin
        user_options['max_loops']=options.maxLoops
        user_options['dry_run']=options.dryRun
        user_options['fail_on_error']=options.failOnError
        user_options['partition']=options.partition
        user_options['reservation']=options.reservation
        user_options['seconds_until_launch_failure']=options.secondsUntilLaunchFailure
        user_options['reporting_session_timestamp']=options.reportingSessionTimestamp
        user_options['cname_exclusions']=options.cnameExclusions
        user_options['no_prompt']=options.noPrompt

    MODULE_CONFIG['user_options'] = user_options
		
## a function to parse config files
def parse_config(input_file_path):
    try:
        config_prefixes = {} 
        config_prefix_endings = ['_bin_root_prefix','_etc_root_prefix','_ini_file_prefix','_ld_library_prefix']
        
        requested_tests = []
        defaults = {}
        fp = None
        config = ConfigParser.ConfigParser()
        if input_file_path and os.path.isfile(input_file_path):
            fp = open(input_file_path)
            config.readfp(fp)
            sections = config.sections()
		    	
            for i,section in enumerate(sections):
                options = None
                if section == "defaults":
                    global_options = ['work_root']
                    options = config.options(section)
                    for option in options:
                        try:
                            #populate local data structure to share config prefixes
                            for config_prefix_ending in config_prefix_endings:
                                if config_prefix_ending in option:
                                    config_prefixes[option] = config.get(section,option)
                            
                            if option in global_options:
                                MODULE_CONFIG[option] = config.get(section,option)	
                            defaults[option] = config.get(section,option)
                        
                        except Exception as e:
                            print "%s %s parse_config exception on %s: %s" % (time.strftime("%Y%m%d%H%M%S"),MODULE_NAME,option,str(e))
            
            for i,section in enumerate(sections):
                options = None
                if section != "defaults":
                    test = {}
                    test['name'] = section
                    options = config.options(section)
                    for option in options:
                        test[option] = config.get(section,option)
                    
                    #append all of the config prefixes to each test 
                    test.update(config_prefixes)

                    if 'cname' in test and test['cname']:
                        pass
                    elif 'cname' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['cname']:
                        test['cname'] = MODULE_CONFIG['user_options']['cname']
                    elif 'cname' in defaults and defaults['cname']: 
                        test['cname'] = defaults['cname']
                    
                    if 'cname_exclusions' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['cname_exclusions']:
                        test['cname_exclusions'] = MODULE_CONFIG['user_options']['cname_exclusions']
                    
                    if 'partition' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['partition']:
                        test['partition'] = MODULE_CONFIG['user_options']['partition']
                    
                    if 'reservation' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['reservation']:
                        test['reservation'] = MODULE_CONFIG['user_options']['reservation']
                   
                    if 'error_keyword_list' in test and test['error_keyword_list']:
                        test['top_level_ini_error_keyword_list_override'] = True
                    elif 'error_keyword_list' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['error_keyword_list']:
                        test['error_keyword_list'] = MODULE_CONFIG['user_options']['error_keyword_list']
                    elif 'error_keyword_list' in defaults and defaults['error_keyword_list']:
                        test['error_keyword_list'] = defaults['error_keyword_list']

                    if 'wall_clock_time_limit_value' in test and test['wall_clock_time_limit_value']:
                        test['top_level_ini_wall_clock_time_limit_value_override'] = True
                    elif 'wall_clock_time_limit_value' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['wall_clock_time_limit_value']:
                        test['wall_clock_time_limit_value'] = MODULE_CONFIG['user_options']['wall_clock_time_limit_value']
                    elif 'wall_clock_time_limit_value' in defaults and defaults['wall_clock_time_limit_value']: 
                        test['wall_clock_time_limit_value'] = defaults['wall_clock_time_limit_value']
                    
                    if 'work_root' in test and test['work_root']:
                        test['top_level_ini_work_root_override'] = True
                    elif 'work_root' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['work_root']:
                        test['work_root'] = MODULE_CONFIG['user_options']['work_root']
                    elif 'work_root' in defaults and defaults['work_root']: 
                        test['work_root'] = defaults['work_root']
                    
                    if 'seconds_until_launch_failure' in test and test['seconds_until_launch_failure']:
                        pass
                    elif 'seconds_until_launch_failure' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['seconds_until_launch_failure']:
                        test['seconds_until_launch_failure'] = MODULE_CONFIG['user_options']['seconds_until_launch_failure']
                    elif 'seconds_until_launch_failure' in defaults and defaults['seconds_until_launch_failure']:
                        test['seconds_until_launch_failure'] = defaults['seconds_until_launch_failure']

                    if 'system_bin_average' in test and test['system_bin_average']:
                        pass
                    elif 'system_bin_average' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['system_bin_average']:
                        test['system_bin_average'] = MODULE_CONFIG['user_options']['system_bin_average']
                    
                    if 'system_bin_average_offset' in test and test['system_bin_average_offset']:
                        pass
                    elif 'system_bin_average_offset' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['system_bin_average_offset']:
                        test['system_bin_average_offset'] = MODULE_CONFIG['user_options']['system_bin_average_offset']
                    
                    if 'hard_trim' in test and test['hard_trim']:
                        pass
                    elif 'hard_trim' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['hard_trim']:
                        test['hard_trim'] = MODULE_CONFIG['user_options']['hard_trim']
                    
                    if 'first' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['first']:
                        test['first'] = MODULE_CONFIG['user_options']['first']
                    
                    if 'last' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['last']:
                        test['last'] = MODULE_CONFIG['user_options']['last']
                    
                    if 'smw_utils_path' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['smw_utils_path']:
                        test['smw_utils_path'] = MODULE_CONFIG['user_options']['smw_utils_path']
                    
                    if 'blades' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['blades']:
                        test['blades'] = MODULE_CONFIG['user_options']['blades']
                    
                    if 'notrim' in MODULE_CONFIG['user_options']:
                        test['notrim'] = MODULE_CONFIG['user_options']['notrim']
                    
                    if 'ssh_timeout' in MODULE_CONFIG['user_options']:
                        test['ssh_timeout'] = MODULE_CONFIG['user_options']['ssh_timeout']
                    
                    if 'destination' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['destination']:
                        test['destination'] = MODULE_CONFIG['user_options']['destination']
                    
                    if 'destination_filename' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['destination_filename']:
                        test['destination_filename'] = MODULE_CONFIG['user_options']['destination_filename']
                    
                    if 'transfer_results' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['transfer_results']:
                        test['transfer_results'] = MODULE_CONFIG['user_options']['transfer_results']
                    
                    if 'dry_run' in test and test['dry_run']:
                        pass
                    elif 'dry_run' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['dry_run']:
                        test['dry_run'] = MODULE_CONFIG['user_options']['dry_run']
                    elif 'dry_run' in defaults and defaults['dry_run']: 
                        test['dry_run'] = defaults['dry_run']
                    
                    if 'margin' in test and test['margin']:
                        pass
                    elif 'margin' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['margin']:
                        test['margin'] = MODULE_CONFIG['user_options']['margin']
                    elif 'margin' in defaults and defaults['margin']: 
                        test['margin'] = defaults['margin']
                    
                    if 'fail_on_error' in test and test['fail_on_error']:
                        pass
                    elif 'fail_on_error' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['fail_on_error']:
                        test['fail_on_error'] = MODULE_CONFIG['user_options']['fail_on_error']
                    elif 'fail_on_error' in defaults and defaults['fail_on_error']: 
                        test['fail_on_error'] = defaults['fail_on_error']

                    if 'xtvrmtrim_last_report' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['xtvrmtrim_last_report']:
                        test['xtvrmtrim_last_report'] = MODULE_CONFIG['user_options']['xtvrmtrim_last_report']
                        
                    if 'post_processing_mode' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['post_processing_mode']:
                        test['post_processing_mode'] = MODULE_CONFIG['user_options']['post_processing_mode']

                    test['session_timestamp'] = MODULE_CONFIG['session_timestamp']

                    requested_tests.append(test)

            fp.close()
            #honor commandline --order option  
            if 'test_order' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['test_order']:
                defaults['test_order'] = MODULE_CONFIG['user_options']['test_order'] 

            MODULE_CONFIG['defaults'] = defaults
            if 'test_order' in defaults and defaults['test_order']:
                ordered_tests = []
                test_order_list = defaults['test_order'].split(",")
                for test_order in test_order_list:
                    for test in requested_tests:
                        if test['name'] == test_order:
                            ordered_tests.append(test)
                            requested_tests.remove(test)
                #implement as feature later ?
                #if requested_tests and len(requested_tests) > 0:
                #    ordered_tests = ordered_tests + requested_tests
                requested_tests = ordered_tests

            MODULE_CONFIG['requested_tests'] = requested_tests
        else:					
            print "%s %s: parse_config unable to find input_file_path: %s" % (time.strftime("%Y%m%d%H%M%S"),MODULE_NAME,str(input_file_path))
			
    except Exception as e:
        print "%s %s: parse_config caught exception: %s" % (time.strftime("%Y%m%d%H%M%S"),MODULE_NAME,str(e))

def print_config():
        try:
		print json.dumps(MODULE_CONFIG,indent=1)
        except Exception as e:
		print "%s %s: print_config caught exception: " % (time.strftime("%Y%m%d%H%M%S"),MODULE_NAME,str(e))	

def logging_setup():
    success = 0
    global logger
    
    if 'log_file_name' in MODULE_CONFIG and MODULE_CONFIG['log_file_name']:
        if not logger:
            # create logger
            logger = logging.getLogger(MODULE_NAME)
            logger.setLevel(logging.DEBUG)

            #print "log_file_name: " + MODULE_CONFIG['log_file_name']
            # create file handler which logs even debug messages
            fh = logging.FileHandler(MODULE_CONFIG['log_file_name'])
            fh.setLevel(logging.INFO)

            # create console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)

            # create formatter and add it to the handlers
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            # add the handlers to the logger
            logger.addHandler(fh)
            logger.addHandler(ch)
	
        success = 1
    
    else:
        pass
        #print "log_file_name is undefined"
        
    return success

## a function for doing any preliminary setup
def init(user_options=None):
    #determine the currrent user name 
    current_user_name = sysconfig.get_current_user_name()
    if 'root' in current_user_name:
        print "Running as root is not allowed. Please change user and run using a non-root account."
        return 0 #False

    (soft_limit,hard_limit) = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE,(hard_limit,hard_limit))
    (soft_limit,hard_limit) = resource.getrlimit(resource.RLIMIT_NOFILE)
    print "RLIMIT_NOFILE set to %d." % soft_limit
    (soft_limit,hard_limit) = resource.getrlimit(resource.RLIMIT_NPROC)
    resource.setrlimit(resource.RLIMIT_NPROC,(hard_limit,hard_limit))
    (soft_limit,hard_limit) = resource.getrlimit(resource.RLIMIT_NPROC)
    print "RLIMIT_NPROC set to %d." % soft_limit
    (soft_limit,hard_limit) = resource.getrlimit(resource.RLIMIT_STACK)
    resource.setrlimit(resource.RLIMIT_STACK,(hard_limit,hard_limit))
    (soft_limit,hard_limit) = resource.getrlimit(resource.RLIMIT_STACK)
    print "RLIMIT_STACK set to %d." % soft_limit
    
    mode = 0
    # always start by parsing the default ini, which will located in the same directory
    # as the currently running script
    default_ini_file = FULL_PATH_TO_SCRIPT_DIR + "/" + MODULE_NAME + ".ini"
    if os.path.isfile(default_ini_file):
        parse_config(default_ini_file)
			
    # override defaults with any user specified options	
    if user_options:
        if 'input_file_path' in user_options and user_options['input_file_path'] is not None:
            print "xtsystest.py init: parsing user specified ini_file_path: " + user_options['input_file_path'] 
            parse_config(user_options['input_file_path'])
        
        #determine work_root
        if 'work_root' in user_options and user_options['work_root'] is not None:
            MODULE_CONFIG['work_root'] = user_options['work_root']	
    
        if 'setup_dir' in user_options and user_options['setup_dir']:
            MODULE_CONFIG['user_options']['setup_dir'] = user_options['setup_dir']
            mode = "setup"
            return mode 
        
        if 'run_report' in user_options and user_options['run_report']:
            mode = "report"
            return mode 

    # "run" mode specific logic 
    if 'work_root' in MODULE_CONFIG:
        MODULE_CONFIG['work_root'] = sysconfig.expand_and_verify_work_root(MODULE_CONFIG['work_root'])
    else:
        MODULE_CONFIG['work_root'] = sysconfig.expand_and_verify_work_root()
    MODULE_CONFIG['log_file_name'] = MODULE_CONFIG['work_root'] + "/" + MODULE_NAME + "_" + MODULE_CONFIG['session_timestamp'] + ".log"
    
    node_list = []
    frontend_host_arch = sysconfig.get_frontend_host_arch()
    arch_specific_node_list = sysconfig.get_arch_specific_node_list(frontend_host_arch)
    partition_available_nodes = []
    if 'partition' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['partition']:
        print "user specified partition: " + str(MODULE_CONFIG['user_options']['partition'])
        partition_available_nodes = sysconfig.get_partition_available_node_list(MODULE_CONFIG['user_options']['partition'])

    #populate the node_info_dict and node_code_names_dict
    if 'cname' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['cname']:
        node_list = sysconfig.get_user_specified_node_list(None,MODULE_CONFIG['user_options']['cname'])
        if 'cname_exclusions' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['cname_exclusions']:
            node_exclusion_list = sysconfig.get_user_specified_node_list(None,MODULE_CONFIG['user_options']['cname_exclusions'])
            if node_exclusion_list: 
                node_list = [nid for nid in node_list if nid not in node_exclusion_list] 
        
        if partition_available_nodes: 
            node_list = [nid for nid in node_list if nid in partition_available_nodes] 
        
        #handle arch  
        if node_list:
            node_list = [nid for nid in node_list if nid in arch_specific_node_list] 
            if not node_list:
                sys.exit("stopping execution: node list is empty after filtering out non-" + frontend_host_arch + " nodes") 
        
        if node_list:
            MODULE_CONFIG['user_specified_node_list'] = node_list
            MODULE_CONFIG['node_info_dict'] = sysconfig.get_node_info_dictionary(FULL_PATH_TO_UTIL_DIR + "/get_node_info.sh",node_list,None,MODULE_CONFIG['user_options']['partition'])
            MODULE_CONFIG['node_code_names_dict'] = sysconfig.get_node_code_names_dictionary(MODULE_CONFIG['node_info_dict'])
        else:
            sys.exit("stopping execution: user specified node list is empty") 

    elif 'node_count' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['node_count']:
        print "init node_count case: node_count: " + str(MODULE_CONFIG['user_options']['node_count'])
        use_node_info_probe = 1
        sysconfig.set_node_info_dictionary(None)
        MODULE_CONFIG['node_info_dict'] = sysconfig.get_node_info_dictionary(FULL_PATH_TO_UTIL_DIR + "/get_node_info.sh",None,MODULE_CONFIG['user_options']['node_count'],MODULE_CONFIG['user_options']['partition'],use_node_info_probe)
        MODULE_CONFIG['node_code_names_dict'] = sysconfig.get_node_code_names_dictionary(MODULE_CONFIG['node_info_dict'])
        node_list = sysconfig.get_user_specified_node_list_from_node_code_names_dictionary(MODULE_CONFIG['node_code_names_dict'])
        
        #handle cname exclusions
        if node_list: 
            if 'cname_exclusions' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['cname_exclusions']:
                node_exclusion_list = sysconfig.get_user_specified_node_list(None,MODULE_CONFIG['user_options']['cname_exclusions'])
                if node_exclusion_list: 
                    node_list = [nid for nid in node_list if nid not in node_exclusion_list] 
                if not node_list:
                    sys.exit("stopping execution: node list is empty after filtering out cname exclusions") 
        
        #handle arch exclusions
        if node_list: 
            node_list = [nid for nid in node_list if nid in arch_specific_node_list] 
            if not node_list:
                sys.exit("stopping execution: node list is empty after filtering out non-" + frontend_host_arch + " nodes") 
        
        if node_list: 
            MODULE_CONFIG['user_specified_node_list'] = node_list
        else:
            sys.exit("stopping execution: user specified node list is empty after requesting node count " + str(MODULE_CONFIG['user_options']['node_count'])) 
    elif 'cname_exclusions' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['cname_exclusions']:
        node_list = sysconfig.expand_node_list(sysconfig.get_node_list())
        node_exclusion_list = sysconfig.get_user_specified_node_list(None,MODULE_CONFIG['user_options']['cname_exclusions'])
        
        if node_exclusion_list: 
            node_list = [nid for nid in node_list if nid not in node_exclusion_list] 
        
        if partition_available_nodes: 
            node_list = [nid for nid in node_list if nid in partition_available_nodes] 
        
        #handle arch 
        if node_list:
            node_list = [nid for nid in node_list if nid in arch_specific_node_list] 
            if not node_list:
                sys.exit("stopping execution: node list is empty after filtering out non-" + frontend_host_arch + " nodes") 
        
        if node_list:
            MODULE_CONFIG['user_specified_node_list'] = node_list
            MODULE_CONFIG['node_info_dict'] = sysconfig.get_node_info_dictionary(FULL_PATH_TO_UTIL_DIR + "/get_node_info.sh",node_list,None,MODULE_CONFIG['user_options']['partition'])
            MODULE_CONFIG['node_code_names_dict'] = sysconfig.get_node_code_names_dictionary(MODULE_CONFIG['node_info_dict'])
        else:
            sys.exit("stopping execution: user specified node list is empty after cname exclusions " + str(MODULE_CONFIG['user_options']['node_count'])) 
    else:
        if 'no_prompt' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['no_prompt']:
            pass 
        else:
            user_response = raw_input("\nProceed to run this test against all available compute nodes?\nPress Y or y followed by enter key to proceed\n\nJust hit enter key alone to exit\n")
            if user_response.lower() == "y":
                print "Proceeding with test, press Ctrl-C to stop at anytime\n"
            else:
                sys.exit("stopping execution") 
        
        node_list = sysconfig.expand_node_list(sysconfig.get_node_list())
        node_list = [nid for nid in node_list if nid in arch_specific_node_list] 
        if not node_list:
            sys.exit("stopping execution: node list is empty after filtering out non-" + frontend_host_arch + " nodes") 
        MODULE_CONFIG['node_info_dict'] = sysconfig.get_node_info_dictionary(FULL_PATH_TO_UTIL_DIR + "/get_node_info.sh",node_list,None,MODULE_CONFIG['user_options']['partition'])
        MODULE_CONFIG['node_code_names_dict'] = sysconfig.get_node_code_names_dictionary(MODULE_CONFIG['node_info_dict'])

    if not logging_setup():
        mode = 0
    else: 
        mode = "run"	       
    
    return mode   	 

## a function that makes a copy of all ini files in a user-specified location
# leverages util/setup_test.py module
def setup_test():
    try:
        setup_module = __import__("workload.util.setup_test",fromlist=["workload.util"])
        if setup_module:
            # SETUP THE TEST 
            print "initializing test using setup_dir: " + MODULE_CONFIG['user_options']['setup_dir']
            setup_config = {}
            setup_config['target_dir'] = MODULE_CONFIG['user_options']['setup_dir']
            setup_config['runnable_tests'] = MODULE_CONFIG['requested_tests'] 
            setup_module.main(setup_config)
        else:
            print "unable to initialize test using setup_dir: " + user_options['setup_dir']
            
    except ImportError as e:
        print "unable to initialize test using setup_dir: " + user_options['setup_dir']

## a function to validate the test is ready to run
def validate_setup():
    success = 1
    runnable_tests = []
    if 'requested_tests' in MODULE_CONFIG:
        runnable_tests = validate_requested_tests(MODULE_CONFIG['requested_tests'],sysconfig.get_standard_modules_list())
    else: 
        logger.error("validate_setup: list of requested_tests is empty")
        
    if runnable_tests:
        MODULE_CONFIG['runnable_tests'] = runnable_tests
    else:
        logger.error("list of runnable tests is empty")
        success = 0
    
    return success

## a function to run the test
def run():
    status = 0
    standard_tests_list = sysconfig.get_standard_modules_list()
    time_limit_in_seconds = get_time_limit_in_seconds()
    max_loops = get_max_loops() 
    
    logger.info("starting run with time_limit_in_seconds: " + str(time_limit_in_seconds))
    logger.info("starting run with max_loops: " + str(max_loops))
    start_time = time.time() 
    loop_counter = 0 
    
    try: 
        keep_running_tests = True
        while keep_running_tests:
            run_tests(MODULE_CONFIG['runnable_tests'],standard_tests_list,loop_counter)
            loop_counter = loop_counter + 1 
            if time_limit_in_seconds:
                now = time.time()
                if now - start_time >= time_limit_in_seconds:
                    keep_running_tests = False 
            elif max_loops and loop_counter >= max_loops:
                keep_running_tests = False
                logger.info("run reached max loops [" + str(max_loops) + "], stopping execution at %s" % (time.strftime("%Y-%m-%d %H:%M:%S")))
        run_component_checks()
    except KeyboardInterrupt as e:
        logger.info("User stopped execution at %s after %s loops" % (time.strftime("%Y-%m-%d %H:%M:%S"),loop_counter))
        run_component_checks()
     
    return status	  

def get_max_loops():
    max_loops = 0
    #give preference to command-line max loops option
    if 'max_loops' in MODULE_CONFIG['user_options'] and MODULE_CONFIG['user_options']['max_loops']:
        max_loops = MODULE_CONFIG['user_options']['max_loops'] 
        if max_loops.isdigit() and not max_loops == "0": 
            return int(max_loops)
        else:    
            return float('inf')
    elif 'max_loops' in MODULE_CONFIG['defaults'] and MODULE_CONFIG['defaults']['max_loops']:
        max_loops = MODULE_CONFIG['defaults']['max_loops'] 
        if max_loops.isdigit() and not max_loops == "0": 
            return int(max_loops)
        else:    
            return float('inf')
    else:    
        return float('inf')
     
def get_time_limit_in_seconds():
    if 'wall_clock_time_limit_unit' in MODULE_CONFIG['defaults'] and 'wall_clock_time_limit_value' in MODULE_CONFIG['defaults']:
        time_limit_in_seconds = 0 
        time_unit = MODULE_CONFIG['defaults']['wall_clock_time_limit_unit']
        time_value = MODULE_CONFIG['defaults']['wall_clock_time_limit_value']
        multiplier = 1
        
        if time_unit == "h":
            multiplier = 3600
        elif time_unit == "m":
            multiplier = 60

        if time_value:
            time_limit_in_seconds = multiplier * int(time_value)
        
        return time_limit_in_seconds 

def run_tests(runnable_tests,standard_tests,loop_counter):
        if standard_tests and runnable_tests and len(runnable_tests)>0 and len(standard_tests)>0:
            spinner = sysconfig.spinning_cursor()
            for i,runnable_test in enumerate(runnable_tests):
                    if runnable_test['name'] not in standard_tests:
                        #custom test
                        try:
                            if runnable_test['path']:
                                status = sysconfig.run_shell_command(runnable_test['path'],logger,MODULE_CONFIG['work_root'])
                                if not status:
                                    logger.info(runnable_test['name'] + " executed without error")
                                else:
                                    logger.error(runnable_test['name'] + " returned error status: " + str(status))
                        except Exception as e:
                            logger.error("run_tests caught exception running custom test " + runnable_test['name'] + ": " + str(e))
                    else:
                        try:
                            test_module = __import__("workload.tests.%s" % (runnable_test['name']),fromlist=["workload.tests"])
                            if test_module:
                                
                                # only use global session_timestamp for first iteration 
                                if loop_counter > 0: 
                                    runnable_test['session_timestamp'] = None 
                                
                                # append the node_info_dict
                                if 'node_info_dict' in MODULE_CONFIG:
                                    runnable_test['node_info_dict'] = MODULE_CONFIG['node_info_dict']
                                
                                # append the node_code_names_dict
                                if 'node_code_names_dict' in MODULE_CONFIG:
                                    runnable_test['node_code_names_dict'] = MODULE_CONFIG['node_code_names_dict']
                                
                                # append the user_specified_node_list 
                                if 'user_specified_node_list' in MODULE_CONFIG:
                                    runnable_test['user_specified_node_list'] = MODULE_CONFIG['user_specified_node_list']
                                
                                # append the sysconfig 
                                if sysconfig is not None:
                                    runnable_test['sysconfig'] = copy.deepcopy(sysconfig) 
                                
                                # RUN THE TEST
                                if 'wall_clock_time_limit_value' in runnable_test and runnable_test['wall_clock_time_limit_value']:
                                    logger.info("starting test: " + runnable_test['name'] + " with wall_clock_time_limit_value: " + str(runnable_test['wall_clock_time_limit_value']))
                                else: 
                                    logger.info("starting test: " + runnable_test['name'])
                                status = test_module.main(runnable_test)
                                if not status:
                                    logger.info("finished test: " + runnable_test['name'])
                                else:
                                    logger.error(runnable_test['name'] + " returned error status: " + str(status))
                                
                                logger.info("sleeping 3 secs to allow system to clean up after " + runnable_test['name'])
                                
                                for iteration in range(3):
                                    status_string = spinner.next() + str(iteration) 
                                    sys.stdout.write(status_string)
                                    sys.stdout.flush()
                                    time.sleep(0.1)
                                    sys.stdout.write('\b' * len(status_string))
                                    time.sleep(1)
                            else:
                                logger.error(runnable_test['name'] + " module is null")
                        except ImportError as e:
                            logger.error(runnable_test['name'] + " import error")
        else:
            logger.error("run_tests: there are no runnable_tests")
                            
def run_component_checks(standalone_report_mode=0):
        debug = 0 
        standard_tests = sysconfig.get_standard_modules_list() 
        runnable_checks = []
        if 'runnable_tests' in MODULE_CONFIG and MODULE_CONFIG['runnable_tests']:
            runnable_checks = copy.deepcopy(MODULE_CONFIG['runnable_tests'])
        elif 'requested_tests' in MODULE_CONFIG:
            runnable_checks = validate_requested_tests(MODULE_CONFIG['requested_tests'],standard_tests)
        else: 
            print "run_component_checks: list of requested_tests is empty"

        if standard_tests and len(standard_tests)>0 and runnable_checks and len(runnable_checks)>0:
            out_file_name = sysconfig.expand_and_verify_work_root(MODULE_CONFIG['work_root']) + "/session_error_summary_" + MODULE_CONFIG['session_timestamp'] + ".log" 
            out_file_handle = open(out_file_name,"w")
            for i,runnable_check in enumerate(runnable_checks):
                if runnable_check['name'] in standard_tests:
                    try:
                        component_check = runnable_check['name'].replace("_test","_check")
                        check_module = __import__("workload.tests.%s" % (component_check),fromlist=["workload.tests"])
                        if check_module:
                            if standalone_report_mode:
                                if MODULE_CONFIG['user_options']['reporting_session_timestamp']:
                                    runnable_check['xtsystest_session_timestamp'] = MODULE_CONFIG['user_options']['reporting_session_timestamp']
                                else:
                                    runnable_check['xtsystest_session_timestamp'] = MODULE_CONFIG['session_timestamp'][:-12] + "000000" 
                            else:
                                runnable_check['xtsystest_session_timestamp'] = MODULE_CONFIG['session_timestamp'][:-6] + "000000" 
                            runnable_check['report_mode'] = 1
                            if debug: 
                                print "xtsystest run_component_checks checking results: " + component_check + ", using config:"
                                runnable_check_keys = runnable_check.keys()
                                for key in runnable_check.keys():
                                    if key is not "sysconfig":
                                        print key + ": " + str(runnable_check[key])
                    
                                 
                            # RUN THE CHECK 
                            status = check_module.main(runnable_check)
                            if status:
                                if len(status) > 0:
                                    out_file_handle.write("\n" + component_check + " found " + str(len(status)) + " errors")
                                    for (timestamp,cname,error_message) in status:
                                        failure_message = "\n" + timestamp
                                        if cname:
                                            failure_message = failure_message + ": " + cname
                                        failure_message = failure_message + ": " + error_message
                                        print failure_message 
                                        out_file_handle.write(failure_message)
                                else:
                                    status_message = component_check + ": no errors found"
                                    print status_message 
                                    out_file_handle.write("\n" + status_message)
                            else:
                            	status_message = component_check + ": no errors found"
                                print status_message 
                                out_file_handle.write("\n" + status_message)

                        else:
                            print component_check + " module is null"
                    except ImportError as e:
                        print component_check + " import error"
                else:
                    print runnable_check['name'] + " not in standard tests" 
            print "\nerror summary available here:"
            print out_file_name + "\n" 
            out_file_handle.close()
        else:
            print "run_component_checks: there are no runnable_checks"


def validate_requested_tests(requested_tests,standard_tests):
     
    accelerator_configuration = sysconfig.get_accelerator_configuration()
    knc_model_names = sysconfig.get_knc_model_names(accelerator_configuration) 
    nvidia_model_names = sysconfig.get_nvidia_model_names(accelerator_configuration) 
    phi_model_names = ['knl'] 
    if not 'run_report' in MODULE_CONFIG['user_options']: 
        phi_model_names = sysconfig.get_phi_model_names()

    runnable_tests = []
    try:
        if standard_tests:
            if requested_tests:
                for test in requested_tests:
                    if test['name'] in standard_tests:
                        if 'type' in test:
                            if test['type'] == "knc":
                                if knc_model_names:
                                    runnable_tests.append(test)
                                else:
                                    print "dropping knc test: " + test['name'] 
                            elif test['type'] == "nvidia": 
                                if nvidia_model_names:
                                    runnable_tests.append(test)
                                else:
                                    print "dropping nvidia test: " + test['name']
                            elif test['type'] == "phi": 
                                if phi_model_names:
                                    runnable_tests.append(test)
                                else:
                                    print "dropping phi test: " + test['name']
                            else:
                                #unregulated standard-test type
                                runnable_tests.append(test)
                        else:
                            #un-typed standard-test
                            runnable_tests.append(test)
                    else:
                        if not 'path' in test:
                            print test['name'] + ": path undefined"
                        else:
                            runnable_tests.append(test)
            else:
                print "validate_requested_tests: list of requested tests is empty"
        else:
            print "validate_requested_tests: list of standard tests is empty"
                    
    except Exception as e:
        print "validate_requested_tests caught exception: " + str(e)
    
    return runnable_tests

def report():
    success = 0
    #print "generate overall report here..."
    return success

def main(user_options):
    init_status = init(user_options)
    if init_status:
        if init_status == "run":
            if validate_setup():
                run()
                report()
            else:
                print "%s %s: main call to validate_setup() failed" % (time.strftime("%Y%m%d%H%M%S"),MODULE_NAME)
        elif init_status == "setup":
            setup_test()
        elif init_status == "report":
            run_component_checks(standalone_report_mode=1)
    else:
        print "%s %s: main call to init() failed" % (time.strftime("%Y%m%d%H%M%S"),MODULE_NAME)

if __name__ == '__main__':
    process_commandline_options()
    main(MODULE_CONFIG['user_options'])
# vim: set expandtab tabstop=4 shiftwidth=4:
