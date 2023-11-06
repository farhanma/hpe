#!/usr/bin/env python
import os
from xkdgemm_test import XKDgemmTest 

def main(test_options=None):
    test = XKDgemmTest()
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    test_options["add_global_error_keywords"] = True
    test_options["display_results"] = True
    main(test_options)
