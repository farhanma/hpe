#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# xthpl_thermal_test.py - a wrapper script used in conjunction with xthpl_thermal_test.ini
#                       to execute the standard xhpl benchmarking tool 
#
# author: Pete Halseth
#
# The purpose of xthpl_thermal_test.py is to provide the means to include 
# the standard xhpl benchmarking tool as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xthpl_thermal_test.py <options> 
#    To see the available options, type: ./xthpl_thermal_test.py -h 
#
# 2. To use within a script, just include the "import xthpl_thermal_test" statement at 
# the top of the script
# 
################################################################################
##@package tests.xthpl_thermal_test
# a tool to execute the standard xhpl benchmark 
import os,sys
from xthpl_test import XTHplTest

class XTHplThermalTest(XTHplTest):

    def __init__(self):
     
        # set self.FULL_PATH_TO_SCRIPT_DIR 
        self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        
        # set self.COMPONENT_NAME
        self.COMPONENT_NAME = self.__class__.__name__ 

        # set self.MODULE_NAME
        (file_root,file_name) = os.path.split(os.path.realpath(__file__))
        (self.MODULE_NAME,ext) = os.path.splitext(file_name)

        # initialize parent
        XTHplTest.__init__(self)  

def main(test_options=None):
    status = 0 
    test = XTHplThermalTest()
    status = test.component_test_main(test_options) 
    return status 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    main(test_options)

# vim: set expandtab tabstop=4 shiftwidth=4:
