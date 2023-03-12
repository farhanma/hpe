#!/usr/bin/env python
import os
from xtvrm_socket1_test import XTVrmScreen_Socket1 

def main(test_options=None):
    test = XTVrmScreen_Socket1() 
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    main()

