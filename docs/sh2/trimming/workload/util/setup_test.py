#!/usr/bin/env python
import sys,os,subprocess,time,string,shlex,getpass,json,shutil,ConfigParser
from optparse import OptionParser

#determine path to default source dir
FULL_PATH_TO_DEFAULT_SOURCE_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__))).replace("/util","")

try:
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(FULL_PATH_TO_DEFAULT_SOURCE_DIR + "/.."))
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

def process_commandline_options():

    config = {}
    
    parser = OptionParser(usage="%prog [-s source_dir] [-t target_dir] [--version]", version="%prog 1.0")
    
    parser.add_option("-s","--source",dest="sourceDir",default=None,
        help="source directory")

    parser.add_option("-t","--target",dest="targetDir",default=None,
        help="target directory")

    (options, args) = parser.parse_args()
    if options:
        config['source_dir'] = options.sourceDir
        config['target_dir'] = options.targetDir

    return config

def verify_and_copy_source_ini_to_target_ini(source_ini,target_ini):
    if source_ini and target_ini:
        if os.path.isfile(source_ini):
            target_dir = os.path.dirname(target_ini)
            try:
                print "copying " + source_ini
                print " to " + target_ini
                #make directories if necessary
                if not os.path.isdir(target_dir):
                    os.makedirs(target_dir)
                shutil.copy(source_ini,target_ini)
            except Exception as e:
                print "%s verify_and_copy_source_ini_to_target_ini caught exception: %s" % (time.strftime("%Y%m%d%H%M%s"),str(e))
                print "%s please verify permissions to write to target_dir: %s" % (time.strftime("%Y%m%d%H%M%s"),target_dir)
                return 0
        else:
            print "%s verify_and_copy_source_ini_to_target_ini: unable to verify source_ini file: %s" % (time.strftime("%Y%m%d%H%M%s"),source_ini)
    else:
        print "%s verify_and_copy_source_ini_to_target_ini: incomplete input params, check source and target values: %s %s" % (time.strftime("%Y%m%d%H%M%s"),source_ini,target_ini)

def update_target_xtsystest_component_test_ini_file_paths(ini_file_list):
   
    xtsystest_ini = ""
    component_ini_mapping = {}
    if ini_file_list:
        #get the tuple for xtsystest
        for ini_tuple in ini_file_list:
            (source_ini,target_ini) = ini_tuple
            if 'xtsystest.ini' in target_ini:
                xtsystest_ini = target_ini
            else:
                (target_ini_path,target_ini_file_name) = os.path.split(target_ini)
                component_ini_mapping[target_ini_file_name.replace('.ini','')] = target_ini

        if xtsystest_ini:
            # use the ConfigParser module to update the ini_file_paths xtsystest_ini
            fp = None
            config = ConfigParser.ConfigParser()
            if os.path.isfile(xtsystest_ini):
                fp = open(xtsystest_ini,'r')
                config.readfp(fp)
                
                fp.close()
                for key in component_ini_mapping.keys():
                    config.set(key,'ini_file_path',component_ini_mapping[key])
               
                #now update the default workroot to be the same dir as the one that contains xtsystest_ini
                config.set("defaults","work_root",os.path.dirname(xtsystest_ini))
                
                fp = open(xtsystest_ini,'w')
                config.write(fp)
                fp.close() 
                
                
    else:
        print "ini_file_list is empty, unable to update ini_file_paths"

def main(config=None):
    if config:
        if 'target_dir' in config and config['target_dir']:
            
            target_dir = config['target_dir']
            if 'source_dir' in config and config['source_dir']:
                source_dir = config['source_dir'] 
                xtsystest_ini = config['source_dir'] + "/xtsystest.ini"
            else:
                source_dir = FULL_PATH_TO_DEFAULT_SOURCE_DIR
                xtsystest_ini = FULL_PATH_TO_DEFAULT_SOURCE_DIR + "/xtsystest.ini"

            #try parsing xtsystest_ini using the xtsystest module
            try:
                if 'runnable_tests' in config and config['runnable_tests']:
                    runnable_tests = config['runnable_tests']
                elif xtsystest:
                    #get list of source ini files 
                    xtsystest.parse_config(xtsystest_ini)
                    runnable_tests = xtsystest.validate_requested_tests(xtsystest.MODULE_CONFIG['requested_tests'],sysconfig.get_standard_modules_list())
                else:
                    runnable_tests = []
                    print "xtsystest_module is undefined after import"
                 
                if runnable_tests: 
                    ini_file_list = []
                    #copy the ini's over
                    for i,test in enumerate(runnable_tests):
                        if 'path' in test and test['path']:
                            print "ignoring custom test: " + test['name']
                        else:
                            source_ini_file = source_dir + "/tests/" + test['name'] + ".ini"
                            target_ini_file = target_dir + "/tests/" + test['name'] + ".ini"
                            ini_file_list.append((source_ini_file,target_ini_file))
                    #now tack on xtsystest.ini
                    ini_file_list.append((xtsystest_ini,target_dir + "/xtsystest.ini"))

                    print "copying files..." 
                    for ini_tuple in ini_file_list:
                        #print sysconfig.dump_data(ini_tuple)
                        (source_ini,target_ini) = ini_tuple
                        verify_and_copy_source_ini_to_target_ini(source_ini,target_ini)
                    
                    #now update the ini_file_paths in the target xtsystest.ini
                    update_target_xtsystest_component_test_ini_file_paths(ini_file_list)
                else:
                    print "Incomplete set of input parameters, cannot proceed...to review usage, try the --help option" 

          
            except RuntimeError as e:
                print "Caught RuntimeError: " + str(e)
            
            print "done..." 
        
        else:
            print "No target directory specified, cannot proceed...please check provided input parameters" 
    else:
        print "Incomplete set of input parameters, cannot proceed...to review usage, try the --help option" 
    

if __name__ == '__main__':
    try:
        from workload import xtsystest 
    except:
        sys.path.append(os.path.abspath(FULL_PATH_TO_DEFAULT_SOURCE_DIR + "/.."))
        from workload import xtsystest 
    
    main(process_commandline_options())
    
