#!/usr/bin/env python
from xtmemory_test import XtMemoryTest 

def main(test_options=None):
    test = XtMemoryTest()
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    test_options = {}
    test_options["process_commandline_options"] = True
    test_options["add_global_error_keywords"] = True
    test_options["display_results"] = True
    main(test_options)
