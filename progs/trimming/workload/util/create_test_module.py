#!/usr/bin/env python
import sys,os,subprocess,time,string,shlex,getpass,json,shutil
from optparse import OptionParser

def process_commandline_options():

    config = {}
    
    parser = OptionParser(usage="%prog [-s source_file] [-t target_file] [-m module_names] [-c class_names] [--version]", version="%prog 1.0")
    
    parser.add_option("-s","--source",dest="sourceFile",default=None,
        help="source test file")

    parser.add_option("-t","--target",dest="targetFile",default=None,
        help="target test file")

    parser.add_option("-m","--module_names",dest="module_names",default="",
        help="comma separated pair of module names")
	
    parser.add_option("-c","--class_names",dest="class_names",default="",
        help="comma separated pair of class names")
    
    (options, args) = parser.parse_args()
    if options:
        config['source_file'] = options.sourceFile
        config['target_file'] = options.targetFile
        config['module_names'] = options.module_names
        config['class_names'] = options.class_names

    return config

def verify_and_copy_source_test_to_target_test(source_test,target_test):
    if source_test and target_test:
        if os.path.isfile(source_test):
            print "copying " + source_test
            print " to " + target_test
            shutil.copy(source_test,target_test)
        else:
            print "%s verify_and_copy_source_test_to_target_test: unable to verify source_test file: %s" % (time.strftime("%Y%m%d%H%M%s"),source_test)
    else:
        print "%s verify_and_copy_source_test_to_target_test: incomplete input params, check source and target values: %s %s" % (time.strftime("%Y%m%d%H%M%s"),source_test,target_test)


def update_module_and_class_name_references(target_test_file,source_class_name,source_module_name,target_class_name,target_module_name):
    if target_test_file and source_class_name and source_module_name and target_class_name and target_module_name:
        if os.path.isfile(target_test_file):
            fh = open(target_test_file, "r")
            #get the file contents as a string
            data = fh.read()
            if data:
                fh.close()
                #do the string substitutions
                print "updating " + target_test_file 
                print "replacing " + source_class_name + " with " + target_class_name
                data = data.replace(source_class_name,target_class_name)
                print "replacing " + source_module_name + " with " + target_module_name
                data = data.replace(source_module_name,target_module_name)
                #print "new data: " 
                #print data
                time.sleep(2)
                fh = open(target_test_file, "w")
                #write the updated data back out to the file
                fh.write(data)
            fh.close()
        else:
            print "%s update_module_and_class_name_references: unable to verify target_test_file: %s" % (time.strftime("%Y%m%d%H%M%s"),target_test_file)
    else:
        print "%s update_module_and_class_name_references: incomplete input params" % (time.strftime("%Y%m%d%H%M%s"))

if __name__ == '__main__':
    config = process_commandline_options()
    if config:
        print json.dumps(config)
        #get tests dir
        FULL_PATH_TO_TEST_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__))).replace("util","tests")
       
        source_file = FULL_PATH_TO_TEST_DIR + "/" + config['source_file']
        target_file = FULL_PATH_TO_TEST_DIR + "/" + config['target_file']
        source_ini_file = source_file.replace(".py",".ini")
        target_ini_file = target_file.replace(".py",".ini") 
        source_check_file = source_file.replace("test.py","check.py")
        target_check_file = target_file.replace("test.py","check.py") 
        source_module_name,target_module_name = config['module_names'].split(",") 
        source_class_name,target_class_name = config['class_names'].split(",") 
        
        print "copying files..." 
        #copy the main test script
        verify_and_copy_source_test_to_target_test(source_file,target_file)
        #copy the ini
        verify_and_copy_source_test_to_target_test(source_ini_file,target_ini_file)
        #copy the check script    
        verify_and_copy_source_test_to_target_test(source_check_file,target_check_file)
        
        print "sleeping for 2 ..." 
        time.sleep(2) 
        print "doing substitutions..." 
        
        update_module_and_class_name_references(target_file,source_class_name,source_module_name,target_class_name,target_module_name)
        update_module_and_class_name_references(target_ini_file,source_class_name,source_module_name,target_class_name,target_module_name)
        update_module_and_class_name_references(target_check_file,source_class_name,source_module_name,target_class_name,target_module_name)
        print "done..." 
    else:
        print "process command line options returned nothing"
    
