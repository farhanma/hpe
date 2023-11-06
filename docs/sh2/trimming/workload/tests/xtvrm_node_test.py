#!/usr/bin/env python
###############################################################################
# Copyright 2015 Cray Inc. All Rights Reserved.
#
# xtvrm_node_test.py - a wrapper script used in conjunction with xtvrm_node_test.ini
#                       to execute the standard Cray xtcpudgemm diagnostic
#
# author: Andrew Litt
#
# The purpose of xtvrm_node_test.py is to provide the means to include 
# the standard Cray xtcpudgemm diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtvrm_node_test.py <options> 
#    To see the available options, type: ./xtvrm_node_test.py -h 
#
# 2. To use within a script, just include the "import xtvrm_node_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xtvrm_node_test
# a tool to execute the Cray xtcpudgemm diagnostic 
import os,shutil,time,subprocess,shlex,json

from xtvrm_screen_test import XTVrmScreen

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XTVrmScreen_Node(XTVrmScreen):

    def __init__(self):

        # set self.FULL_PATH_TO_SCRIPT_DIR 
        self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

        # set self.COMPONENT_NAME
        self.COMPONENT_NAME = self.__class__.__name__ 

        # set self.MODULE_NAME
        (file_root,file_name) = os.path.split(os.path.realpath(__file__))
        (self.MODULE_NAME,ext) = os.path.splitext(file_name)

        # initialize parent
        XTVrmScreen.__init__(self)

def main(test_options=None):
    status = 0
    test = XTVrmScreen_Node()
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
                status = test.screen_process_results(not test.notrim)
            else:
                test.logger.error("main: test failed due to validation errors")
                test.logger.error(validation_errors)

    return status

if __name__ == "__main__":
    main()


# vim: set expandtab tabstop=4 shiftwidth=4:
