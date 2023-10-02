#!/usr/bin/env python
import os
from xtvrm_node_test import XTVrmScreen_Node 

def main(test_options=None):
    test = XTVrmScreen_Node()
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    main()

