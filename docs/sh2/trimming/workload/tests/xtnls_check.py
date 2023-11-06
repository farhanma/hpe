#!/usr/bin/env python
from xtnls_test import XtNlsTest 

def main(test_options=None):
    test = XtNlsTest()
    return test.component_check_main(test_options) 

if __name__ == "__main__":
    main()

