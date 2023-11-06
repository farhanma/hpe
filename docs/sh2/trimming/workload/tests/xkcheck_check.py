#!/usr/bin/env python
import os
from xkcheck_test import XKCheckTest

def main(test_options=None):
    test = XKCheckTest()
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    test_options["add_global_error_keywords"] = True
    main(test_options)
