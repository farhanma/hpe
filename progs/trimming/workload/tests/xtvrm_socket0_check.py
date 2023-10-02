#!/usr/bin/env python
import os
from xtvrm_socket0_test import XTVrmScreen_Socket0 

def main(test_options=None):
    test = XTVrmScreen_Socket0()
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    main()

