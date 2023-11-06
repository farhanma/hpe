#!/usr/bin/env python
###############################################################################
# Copyright 2014 Cray Inc. All Rights Reserved.
#
# Workload default system configuration discovery - system_configuration.py
#
# Python script used to populate various variables that describe 
# the system under test, including:
#
# NUM_NODES
# NUM_CORES_PER _NODE
# MODE
#
# author: Pete Halseth
#
# The purpose of the sysconfig script is to automatically determine
# the values of a number important measurements and aspects of the system under 
# test, which are then used to provide default run settings and/or to 
# verify end-user specified settings.  
#
# Usage:
# -------
# 1. To echo a listing of the current system configuration to the console, type 
# ./system_configuration.py at the command prompt from within the workload directory
#
#
# 2. To use within a script, just include the "from workload.util import system_configuration" statement at 
# the top of the script
# 
# 
################################################################################
##@package util.system_configuration
# a set of tools useful for validating end-user configurations
import re,sys,os,subprocess,time,string,shlex,getpass,json,csv,re,getpass,math
import pexpect
from jinja2 import Template
from datetime import datetime
import xml.etree.cElementTree as ET

def get_wlm():
    wlm = None
    python_init_file = "/opt/cray/pe/modules/default/init/python.py"
    if not os.path.exists(python_init_file):
        python_init_file = "/opt/modules/default/init/python"
        if not os.path.exists(python_init_file):
            python_init_file = "/opt/modules/default/init/python.py"
            if not os.path.exists(python_init_file):
                python_init_file = None 
        
    if python_init_file: 
        python_module = {}
        execfile(python_init_file,python_module)
        python_module['module']('load','wlm_detect')
        command = "wlm_detect"
        proc=subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:
            for out_line in proc.stdout:
                wlm = out_line.strip('\n')
    return wlm 

class BaseConfig(object):
    HOSTNAME_MASK = "nid00000"
    ALPS = "ALPS"
    SLURM = "SLURM"
    RUNTIME_ERROR_INHERITANCE = "accessing BaseConfig implemenation of WLM specific method" 
    FULL_PATH_TO_UTIL_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

    def __init__(self):
        self.SYSTEM_STATE = {}
    
    def check_trim_apply_results(self,results,retryList):
        """Get the number of failures in applying VRM trim from SEEPs
            Args:
                results: string of result output from xtrsh patch_vrm call"
                retryList: list of blades that failed to trim
            Returns:
                number of blades that failed to trim
        """
        if not "OK" in results:
            print "Remote command xtrsh did not complete on the SMW"
            print "Can not continue"
            raise Exception
            
        if results.count('FAIL') > 0:
            test = results.split("\n")
            for result in test:
                if result.find('FAIL') > -1:
                    temp = result.split(":")[0]
                    temp.replace(' ','')
                    retryList.append(str(temp[:-1]))
        return results.count('FAIL')
    
    def check_xtvrmscreen_results(self,results):
        """Get the number of failed PDCs from xtvrmscreen output
            Args:
                results: string of result output from xtvrmscreen_helper call"
            Returns:
                number of PDC SEEPs that failed to program
        """
        if not "passed" in results:
            print "Remote command xtvrmscreen_smwhelper did not complete on the SMW"
            print "Can not continue"
            raise Exception
        fail_filter = re.compile(r'([0-9]*)(?: PDCs failed)')
        failed_pdcs = fail_filter.findall(results)
        return int(failed_pdcs[0])

    def concatenate_list_of_data_files(self,input_file_list,output_filename=None):
        out_file =  "/tmp/my_concatenated_file.csv"
        if output_filename and self.sane_filename_request(output_filename):
            out_file = output_filename

        if os.path.exists(out_file):
            #todo: remove this outfile
            f = open(out_file, 'r+')
            f.seek(0)
            f.truncate()
            f.close()

        if input_file_list:
            file_buffer = ""
            #concatenate each of the file in input_file_list, store the results in a somefile
            for i,infile in enumerate(input_file_list):
                if os.path.exists(infile):
                    f = open(infile,'r')
                    file_contents = f.read()
                    if not ("n,o," in file_contents):
                        file_buffer += file_contents 
                    f.close()

            if file_buffer:
                #now write file_buffer out
                of = open(out_file,'w')
                if of:
                    of.write(file_buffer)
                    of.close();
                    return out_file;

        return ""

    def convert_hostname_list_to_node_list(self,hostname_list):
        node_list = []
        for hostname in hostname_list:
            nid_string = self.get_nid_from_hostname(hostname)
            if nid_string:
                node_list.append(int(nid_string))
        return node_list
    
    def convert_hostname_list_to_sparse_string(self,hostname_list):
        sparse_string = "nid"
        
        len_longest_hostname = 0
        len_shortest_zero_sequence = float("inf") 
        node_list = []
        
        #first convert hostname list to a node list
        if hostname_list: 
            for hostname in hostname_list:
                if "nid" in hostname:
                    hostname_without_nid_prefix = hostname.replace("nid","")
                    if len(hostname_without_nid_prefix) > len_longest_hostname:
                        len_longest_hostname = len(hostname_without_nid_prefix)
                    if int(hostname_without_nid_prefix) == 0:
                        hostname_without_zero_sequence = "0"
                    else:
                        hostname_without_zero_sequence = hostname_without_nid_prefix.lstrip("0")
                    node_list.append(int(hostname_without_zero_sequence))
                    len_cur_zero_sequence = len(hostname_without_nid_prefix) - len(hostname_without_zero_sequence) 
                    if len_cur_zero_sequence < len_shortest_zero_sequence:
                        len_shortest_zero_sequence =  len_cur_zero_sequence 
        
        if node_list:
            #print "working with node_list: " + str(node_list)
            for i in xrange(0,len_shortest_zero_sequence):
                sparse_string = sparse_string + "0"
            sparse_string = sparse_string + "["
            comma = ""
            sparse_node_list_string = self.convert_node_list_to_sparse_string(node_list)
            list_of_contiguous_components = sparse_node_list_string.split(",")
            #print "working with list_of_contiguous_components: " + str(list_of_contiguous_components)
            for contiguous_component in list_of_contiguous_components:
                updated_component_string = ""
                if "-" in contiguous_component:
                    contiguous_components = contiguous_component.split("-")
                    dash = ""
                    for contig_component in contiguous_components:
                        num_zeros = len_longest_hostname - len(contig_component) - len_shortest_zero_sequence
                        if num_zeros > 0:
                            for j in xrange(0,num_zeros):
                                contig_component = "0" + contig_component
                        updated_component_string = updated_component_string + dash + contig_component
                        dash = "-"
                else:
                    num_zeros = len_longest_hostname - len(contiguous_component) - len_shortest_zero_sequence
                    if num_zeros > 0:
                        for j in xrange(0,num_zeros):
                            contiguous_component = "0" + contiguous_component
                    updated_component_string = updated_component_string + contiguous_component
                sparse_string = sparse_string + comma + updated_component_string
                comma = ","
            sparse_string = sparse_string + "]"

        return sparse_string 

    def convert_node_list_to_hostname_list(self,node_list):
        hostname_list = []
        for nid in node_list:
            hostname = self.get_hostname_from_nid(str(nid))
            if hostname:
                hostname_list.append(hostname)
        return hostname_list 
 
    def convert_node_list_to_hostname_list_string(self,node_list):
        hostname_list = self.convert_node_list_to_hostname_list(node_list) 
        return ",".join(hostname_list) 
 
    def convert_node_list_to_sparse_string(self,node_list,use_cnames=None):
        compact_string = ""
        unique_node_list = list(set(node_list))
        unique_node_list.sort(key=int)
        num_nids = len(unique_node_list)
        comma = ","
        dash = ""
        for i,nid in enumerate(unique_node_list):
            node_string = str(nid)
            if use_cnames:
                node_string = self.get_cname_from_nid_using_cnames_dictionary(nid)
        
            #beginning: i == 0 or nid + 1 < unique_node_list[i+1] 
            if i == 0:
                #print "first: " + str(nid)
                compact_string = node_string 
            elif nid - 1 > unique_node_list[i-1]:
                #print "beginning: " + str(nid)
                compact_string = compact_string + "," + node_string 
            elif i+1 < num_nids and nid + 1 == unique_node_list[i+1]:
                #print "middle: " + str(nid)
                dash = "-"
            elif i+1 < num_nids and nid + 1 < unique_node_list[i+1]:
                #print "end: " + str(nid)
                if dash:
                    compact_string = compact_string + dash + node_string 
                    dash = ""
                else:
                    compact_string = compact_string + comma + node_string 
            elif i + 1 == num_nids:
                #print "last: " + str(nid)
                if dash:
                    compact_string = compact_string + dash + node_string 
                    dash = ""
                else:
                    compact_string = compact_string + comma + node_string 
           
        return compact_string

    def cpubrand_filter(self, brand):
        """Create a more easily processed brand string.  Strips
        the common "Intel(R) Xeon(R) CPU " string from
        the beginning, removes whitespace, and upcases
        the remainder.  Example:
            "Intel(R) Xeon(R) CPU E5-2698 v3 @ 2.30GHz"
            becomes
            "E5-2698V3@2.30GHZ"
        Args:
            brand: Raw CPU brand string
        Returns:
            Cleaned CPU brand string     
        """
        (dummy, filtered) = brand.replace(' ','').upper().split("CPU")

        """
        Due to changes in the naming for SKL, if we try to read from a split
        on CPU, there will be a @<clock speed>. Spliting on (R) instead, but 
        still removing "CPU" from the string give a working string
        Example:
            "Intel(R) Xeon(R) Gold 6148 CPU @ 2.40GHz"
            would first produce 
            "@2.40GHZ"
            and then becomes
            "GOLD6148@2.40GHZ"
        """
        if (filtered[0] == "@"):
            (dummy, dummy, filtered) = brand.replace(' ','').upper().replace('CPU','').split("(R)")

        return filtered

    def create_integer_csv_list(self,processor_cpu_start,avail_cores,stride):
        int_list = list(range(int(processor_cpu_start), int(avail_cores), int(stride)))
        if len(int_list) == 0:
            print "Empty integer range list."
            return int_list

        int_csv_list = ','.join(map(str, int_list))
        return int_csv_list

    def dump_data(self,data_container):
        if data_container:
            return json.dumps(data_container,indent=4,sort_keys=True,separators=(',',': '))
        else:
            return "no data"

    def execute_trim_apply(self,destination_hostname,first,last, blade_list,timeout=180,retries=10):
        """Runs patch_vrm on all BCs to reload trims from the SEEPs to
        the VRMs.  Uses SSH to call xtrsh on the SMW. 
        Args:
            destination_hostname: the host to contact
            first: username
            last: password
            blade_list: list of blades to constrain the operation to
            timeout=180: Timeout in s for the xtrsh to complete on the SMW
            retries=5: Number of time to try applying the trim. Used when
                       i2c errors causes the trim to fail to apply
        Returns:
            None
        """
        old_blade_list = blade_list
		
        #Due to issues with i2c communications to the SEEPs, there is a need to
        #  retry the trim multiple times. 
        for i in range(retries):
            retryList = []
            helper_command = "xtrsh -l root -m s -s \'patch_vrm\' " + ",".join(blade_list)

            ssh_command = "ssh " + first + "@" + destination_hostname + " \"" + helper_command + "\""
            data = self.run_ssh_command(ssh_command, last, cmd_timeout=timeout)

            failed = self.check_trim_apply_results(data, retryList)
            if failed > 0:
                print "Trim set failed for " + str(failed) + " blades."
                print "retry ", i
                blade_list = retryList
            else:
                break

        blade_list = old_blade_list
        if failed > 0:
            print "Trim set failed for " + str(failed) + " blades."
            raise Exception
        else:
            print "Trims applied to nodes from SEEPs successfully."

    def execute_xtvrmscreen_smwhelper(self,destination_hostname,smw_utils_path,first,last,blade_list,trim_rpt,trim_csv=None,dryrun=False,timestamp=None,test_percent=None,timeout=180,workroot=None,post_processing=None):
        """Runs xtvrmscreen_smwhelper on the SMW to apply trims
        of blades
        Args:
            destination_hostname: the host to contact
            smw_utils_path: path override to xtvrmscreen_smwhelper
            first: username
            last: password
            blade_list: list of blades to constrain the operation to
            trim_rpt: filename to write pre/post trim write data to
            trim_csv=None: filename of the trim deltas CSV on the SMW.
                Calls xtvrmscreen_smwhelper with -z if not set
            dryrun=False: Do not write trims to the SEEPs if True
            timestamp=None: Set timestamp in metadata to this string
            test_percent=None: Call xtvrmscreen with -u <test_percent> if
                set to a float.
            timeout=180: Timeout in seconds for xtvrmscreen_smwhelper to
                complete on the SMW
        Returns:
            None
        """
        print "Writing SEEPs on target..."
        helper_command = smw_utils_path + "/xtvrmscreen_smwhelper "
        if dryrun:
            helper_command += "-d "
        if timestamp != None:
            helper_command += "-S " + timestamp + " "
        if trim_csv:
            helper_command = helper_command + "-t " + trim_csv + " -r " + trim_rpt + " " + ",".join(blade_list)
        elif test_percent:
            helper_command = helper_command + "-u " + str(test_percent) + " -r " + trim_rpt + " "  + ",".join(blade_list)
        else:
            helper_command = helper_command + "-z -r " + trim_rpt + " " + ",".join(blade_list)

        ssh_command = "ssh " + first + "@" + destination_hostname + " \"" + helper_command + "\""
        data = self.run_ssh_command(ssh_command, last, cmd_timeout=timeout)
        print data
        failed = self.check_xtvrmscreen_results(data)
        if failed > 0:
            print "SEEP write failed for " + failed[0] + " PDCs."
            raise Exception
        else:
            print "SEEPs written successfully."
            
        if post_processing:
            time.sleep(5)
            self.transfer_results_from_smw(destination_hostname,workroot + trim_rpt.split("/")[2], trim_rpt,first,last)

    def expand_and_verify_file_system_path(self,file_path):
        try:
            #real_path doesn't expand ~
            if "~" in file_path:
                #print "expand_and_verify_file_system_path: file_path before tilde expansion: " + file_path
                file_path = string.replace(file_path,"~",os.path.expanduser("~"))
                #print "expand_and_verify_file_system_path: file_path after tilde expansion: " + file_path
            #print "expand_and_verify_file_system_path: file_path before real_path: " + file_path 
            file_path = os.path.realpath(file_path)
            #print "expand_and_verify_file_system_path: file_path after real_path: " + file_path 
            if not os.path.exists(file_path):
                return 0 
        except Exception as e:
            print "%s expand_and_verify_file_system_path caught exception: %s" % (time.strftime("%Y%m%d%H%M%s"),str(e))
            return 0 

        return file_path 

    def expand_and_verify_work_root(self,work_root=None):
        try: 
            if not work_root:
                work_root = "~"
            if work_root.startswith("~"):
                work_root = string.replace(work_root,"~",os.path.expanduser("~"))
            work_root = os.path.realpath(work_root)
            if not os.path.isdir(work_root):
                os.makedirs(work_root)
        except Exception as e:
            print "%s expand_and_verify_work_root caught exception: %s" % (time.strftime("%Y%m%d%H%M%s"),str(e))
            return 0 

        return work_root

    def expand_node_list(self,node_lists_string):
        list_of_individual_nodes = []
        node_lists = node_lists_string.strip("\n").split(",")
        for node_list in node_lists:
            if "-" in node_list:
                start_node_id,end_node_id = node_list.split("-")
                for i in xrange(int(start_node_id),int(end_node_id)+1):
                    list_of_individual_nodes.append(i)
            elif node_list and not "error" in node_list:
                list_of_individual_nodes.append(int(node_list))
        return list_of_individual_nodes

    def factory(type=None):
        if not type:
            type = get_wlm()
        if type == "ALPS": return AlpsConfig()
        if type == "SLURM": return SlurmConfig()
        assert 0, "Bad SysConfig creation: " + type
    factory = staticmethod(factory)

    def get_accelerator_configuration(self):
        accelerator_configuration = {} 
        accelerator_names = self.get_accelerator_model_names()
        if accelerator_names and len(accelerator_names)>0:
            for model_name in accelerator_names:
                node_count = self.get_accelerator_model_node_count(model_name)
                node_list = self.get_accelerator_model_node_list(model_name)
                accelerator_configuration[model_name] = (node_count,node_list)

        return accelerator_configuration

    def get_accelerator_model_names(self):
        accelerator_names = []
        command = "cnselect -L name"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:	
            for out_line in proc.stdout:
                accelerator_names.append(out_line.strip('\n')) 
        return accelerator_names
    
    def get_accelerator_model_names_from_node_list(self,node_list):
        model_name_list = []
        node_model_name_map = self.get_node_accelerator_model_name_map()
        if node_model_name_map:
            for nid in node_list:
                if nid in node_model_name_map:
                    node_model_name = node_model_name_map[nid]
                    if not node_model_name in model_name_list:
                        model_name_list.append(node_model_name)

        return model_name_list 
    
    def get_node_accelerator_model_name_map(self):
        node_model_name_map = {}
        if "node_accelerator_model_name_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["node_accelerator_model_name_map"]:
            node_model_name_map = self.SYSTEM_STATE["node_accelerator_model_name_map"] 
        else: 
            model_names = self.get_accelerator_model_names()
            if model_names:
                for model_name in model_names:
                    model_name_node_list = self.get_accelerator_model_node_list(model_name)
                    if model_name_node_list:
                        for nid in model_name_node_list:
                            node_model_name_map[nid] = model_name
                self.SYSTEM_STATE["node_accelerator_model_name_map"] = node_model_name_map 
        return node_model_name_map
            
    def get_accelerator_model_node_count(self,model_name):
        command = "cnselect -c -e \"name.eq.'" + model_name + "'\""
        fl = os.popen(command)
        num_nodes = fl.read().strip('\n')
        fl.close()
        return num_nodes
    
    def get_accelerator_model_node_list(self,model_name):
        command = "cnselect -e \"name.eq.'" + model_name + "'\""
        fl = os.popen(command)
        node_list_string = fl.read()
        list_of_individual_nodes = self.expand_node_list(node_list_string)
        fl.close()
        return list_of_individual_nodes

    def get_age_user_jobs(self,user,apids,partition=None):
        raise RuntimeError(self.RUNTIME_ERROR_INHERITANCE + ": get_age_user_jobs")

    def get_apids_by_name(self,username,testnames,partition=None):
        raise RuntimeError(self.RUNTIME_ERROR_INHERITANCE + ": get_apids_by_name")

    def get_blade_expansion(self,destination_hostname,first,last,cnames):
        """Calls to the SMW to expand a CNAME string into a deduped list
        of blades
        Args:
            destination_hostname: the host to contact
            first: username
            last: password
            cnames: comma separated string of CNAMEs to expand
        Returns:
            list of blade CNAME strings
        """
        print "Asking SMW for blade list..."
        if cnames == None:
            cnames = "s0"
        ssh_status_command =  "ssh " + first + "@" + destination_hostname + " "
        ssh_status_command += "\"xtcli status -t bc " + cnames + " | grep -e 'c[0-9]*-[0-9]*' | sed -e 's/^[ \t]\+//g' | sed -e 's/[ \t:]\+/ /g'\""  # | sed -ne 's/^ *\(c.*\):.*/\\1/p'\""
        data = self.run_ssh_command(ssh_status_command, last)
        data.strip()
        blades = []
        for line in data.splitlines():
            columns = line.split(" ")
            if len(columns) == 5 and columns[1] == "-" and columns[3] == "ready":
                blades.append(columns[0].strip())

        if len(blades) == 0:
            print "SMW unable to expand CNAMEs"
            raise Exception
        return list(set(blades))

    def get_list_single_node_per_blade(self,node_index=0,cnames_dictionary=None):
        node_list = []
        if not cnames_dictionary:
            cnames_dictionary = self.get_cnames_dictionary()
        module_cnames = cnames_dictionary
        for cname_key in module_cnames:
            requested_node_cname = cname_key + "n" + str(node_index)
            if requested_node_cname in cnames_dictionary:
                node_list.append(cnames_dictionary[requested_node_cname][0])
        
        return node_list

    def get_cnames_dictionary(self,partition=None,reservation=None):
        cnames = {}
        cnames["s0"] = []
        cnames["module_cnames"] = []
        command = "xtprocadmin"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:	
            for outline in proc.stdout:
                columns = outline.split()
                if len(columns)==6 and columns[3] == "compute" and columns[4]=="up":
                    cur_nid = int(columns[0]) 
                    cur_cname = columns[2]
                    cabinet_chassis = cur_cname.strip("c").split("c")
                    cabinet = cabinet_chassis[0]
                    chassis = cabinet_chassis[1]
                    cabinet_row = cabinet.split("-")
                    cabinet = cabinet_row[0]
                    row = cabinet_row[1]
                    chassis_module = chassis.split("s")
                    chassis = chassis_module[0]
                    module = chassis_module[1]
                    module_node=module.split("n")
                    module = module_node[0]
                    node = module_node[1]
                 
                    row_key = "cX-" + row 
                    if row_key in cnames:
                        cnames[row_key].append(cur_nid)
                    else:
                        cnames[row_key] = [cur_nid]
                 
                    cabinet_key = "c" + cabinet + "-" + row 
                    if cabinet_key in cnames:
                        cnames[cabinet_key].append(cur_nid)
                    else:
                        cnames[cabinet_key] = [cur_nid]
                 
                    chassis_key = cabinet_key + "c"  + chassis 
                    if chassis_key in cnames:
                        cnames[chassis_key].append(cur_nid)
                    else:
                        cnames[chassis_key] = [cur_nid]
                 
                    module_key = chassis_key + "s" + module 
                    if module_key in cnames:
                        cnames[module_key].append(cur_nid)
                    else:
                        cnames[module_key] = [cur_nid]
                        
                    if not module_key in cnames["module_cnames"]:
                        cnames["module_cnames"].append(module_key)
                 
                    node_key = module_key + "n" + node 
                    if node_key in cnames:
                        cnames[node_key].append(cur_nid)
                    else:
                        cnames[node_key] = [cur_nid]
                    cnames["s0"].append(cur_nid)              
        
        self.SYSTEM_STATE['cnames_dictionary'] = cnames 
        return cnames
    
    def get_cname_from_hostname(self,hostname):
        cname = ""
        hostname_cname_map = self.get_hostname_cname_map()
        if hostname_cname_map and hostname in hostname_cname_map:
            cname = hostname_cname_map[hostname]
        return cname

    def get_cname_from_nid(self,nid):
        cname = ""
        nid_cname_map = self.get_nid_cname_map()
        if nid_cname_map and nid in nid_cname_map:
            cname = nid_cname_map[nid]
        return cname

    def get_cname_hostname_map(self):
        cname_hostname_map = {}
        #get cname_hostname_map from SYSTEM_STATE cache if possible
        if "cname_hostname_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["cname_hostname_map"]:
            cname_hostname_map = self.SYSTEM_STATE["cname_hostname_map"]
        else:
            found_data = 0
            node_info_dictionary = self.get_node_info_dictionary() 
            nid_list = node_info_dictionary.keys()
            for i,nid in enumerate(nid_list):
                hostname = node_info_dictionary[nid]["hostname"]
                cname = node_info_dictionary[nid]["cname"]
                cname_hostname_map[cname] = hostname 
                found_data = 1
                if found_data:
                    self.SYSTEM_STATE["cname_hostname_map"] = cname_hostname_map
        return cname_hostname_map

    def get_cname_nid_map(self):
        cname_nid_map = {}
        #get cname_nid_map from SYSTEM_STATE cache if possible
        if "cname_nid_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["cname_nid_map"]:
            cname_nid_map = self.SYSTEM_STATE["cname_nid_map"]
        else:
            found_data = 0
            node_info_dictionary = self.get_node_info_dictionary() 
            nid_list = node_info_dictionary.keys()
            for i,nid in enumerate(nid_list):
                cname = node_info_dictionary[nid]["cname"]
                cname_nid_map[cname] = nid 
                found_data = 1
            if found_data:
                self.SYSTEM_STATE["cname_nid_map"] = cname_nid_map
        return cname_nid_map
    
    def get_column_label_index(self,header_list,label):
        idx = 0;
        if header_list and label:
            for i,column_header in enumerate(header_list):
                if str(label) in str(column_header):
                    idx = i 
        return idx
    
    def get_cores_system(self):
        cores_system = {}
        total_num_cores = 0 
    
        #get the list of core sizes
        list_core_sizes = self.get_list_core_sizes()
    
        for core_size in list_core_sizes:
            core_size = int(core_size)
            total_for_core_size = 0
            node_lists_for_core_size = self.get_node_list("numcores.eq." + str(core_size)).split(",") 
            list_of_individual_nodes = []
            for node_list in node_lists_for_core_size:
                if "-" in node_list:
                    start_node_id,end_node_id = node_list.split("-")
                    for i in xrange(int(start_node_id),int(end_node_id)+1):
                        list_of_individual_nodes.append(i)
                        total_for_core_size = total_for_core_size + core_size
                elif node_list:
                    list_of_individual_nodes.append(int(node_list))
                    total_for_core_size = total_for_core_size + core_size
            cores_system[str(core_size)] = (total_for_core_size,list_of_individual_nodes)
            total_num_cores = total_num_cores + total_for_core_size
        cores_system['total_cores'] = total_num_cores
    
        return cores_system 

    def get_current_user_name(self):
        return getpass.getuser()
    
    def get_arch_specific_node_list(self,arch,skip_service_nodes=True):
        arch_specific_node_list = []
        if arch:
            node_info = self.get_node_info_dictionary()
            if node_info:
                for nid in node_info.keys():
                    if 'arch' in node_info[nid]:
                        if node_info[nid]['arch'] == arch:
                            if skip_service_nodes and 'node_type' in node_info[nid] and node_info[nid]['node_type'] == 'service':
                                continue
                            else: 
                                arch_specific_node_list.append(int(nid))
        return arch_specific_node_list

    def get_frontend_host_arch(self):
        frontend_host_arch = ""
        lscpu_dict = self.get_lscpu_dict()
        if lscpu_dict and "Architecture" in lscpu_dict:
            frontend_host_arch = lscpu_dict['Architecture']
        return frontend_host_arch 
    
    def get_lscpu_dict(self):
        lscpu_dict = {}
        command = "lscpu" 
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:
            for outline in proc.stdout:
                try:
                    (name,value) = outline.split(":")
                    lscpu_dict[name.strip()] = value.strip()
                except Exception as e:
                    print "get_lscpu_dict caught exception: " + str(e)
        return lscpu_dict 
    
    def get_hostname_cname_map(self):
        hostname_cname_map = {}
        #get hostname_cname_map from SYSTEM_STATE cache if possible
        if "hostname_cname_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["hostname_cname_map"]:
            hostname_cname_map = self.SYSTEM_STATE["hostname_cname_map"]
        else:
            found_data = 0
            node_info_dictionary = self.get_node_info_dictionary() 
            nid_list = node_info_dictionary.keys()
            for i,nid in enumerate(nid_list):
                hostname = node_info_dictionary[nid]["hostname"]
                cname = node_info_dictionary[nid]["cname"]
                hostname_cname_map[hostname] = cname
                found_data = 1
            if found_data:
                self.SYSTEM_STATE["hostname_cname_map"] = hostname_cname_map
        return hostname_cname_map

    def get_hostname_from_cname(self,cname):
        hostname = ""
        cname_hostname_map = self.get_cname_hostname_map()
        if cname_hostname_map and cname in cname_host_map:
            hostname = cname_hostname_map[cname]
        return hostname
    
    def get_hostname_from_hostname_mask(self,nid):
        hostname = ''
        if nid:
            nid_str = str(nid)
            hostname = self.HOSTNAME_MASK[:-len(nid_str)] + nid_str

        return hostname

    def get_hostname_from_nid(self,nid):
        hostname = ""
        nid_hostname_map = self.get_nid_hostname_map()
        if nid_hostname_map and nid in nid_hostname_map:
            hostname = nid_hostname_map[nid]
        return hostname
    
    def get_hostname_list_from_node_list(self,node_list):
        hostname_list = [] 
        unique_node_list = list(set(node_list))
        unique_node_list.sort(key=int)
        for i,nid in enumerate(unique_node_list):
            nid_str = str(nid)
            hostname = self.HOSTNAME_MASK[:-len(nid_str)] + nid_str
            hostname_list.append(hostname)
        return hostname_list 
    
    def get_hostname_nid_map(self):
        hostname_nid_map = {}
        #get hostname_nid_map from SYSTEM_STATE cache if possible
        if "hostname_nid_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["hostname_nid_map"]:
            hostname_nid_map = self.SYSTEM_STATE["hostname_nid_map"]
        else:
            found_data = 0
            node_info_dictionary = self.get_node_info_dictionary() 
            nid_list = node_info_dictionary.keys()
            for i,nid in enumerate(nid_list):
                hostname = node_info_dictionary[nid]["hostname"]
                hostname_nid_map[hostname] = nid 
                found_data = 1
            if found_data:
                self.SYSTEM_STATE["hostname_nid_map"] = hostname_nid_map
        return hostname_nid_map
    
    def get_knc_model_names(self,accelerator_configuration_dict=None):
        knc_names = ['Xeon_Phi'] 
        if not accelerator_configuration_dict:
            accelerator_configuration_dict = self.get_accelerator_configuration()
    
        if accelerator_configuration_dict:
            keys = accelerator_configuration_dict.keys() 
            for name in knc_names:
                if not (name in keys):
                    knc_names.remove(name)
        else:
            knc_names = []
        return knc_names

    def get_list_core_sizes(self):
        fl = os.popen('cnselect -L numcores')
        num_core_types = fl.read().strip('\n').split('\n')
        fl.close()
        return num_core_types

    def get_list_mem_sizes(self):
        fl = os.popen('cnselect -L availmem')
        mem_types = fl.read().strip('\n').split('\n')
        fl.close()
        return mem_types

    def get_max_power_data(self,windows,node_info_dict):
        socket = "0" #max power is the same for either socket; defaulting to 0
        max_power_data = {}
        max_power_string = ""           
        if node_info_dict:
            print "have node_info_dict"
            for key in node_info_dict.keys():
                sku_key = node_info_dict[key]["sku"]
                sku_key = self.cpubrand_filter(sku_key)
                if sku_key in windows and windows[sku_key]:                      
                    max_power_value = windows[sku_key][socket]["node_pwr_max_limit"]
                else:
                    print "couldn't find the sku, " + sku_key + " in the windows file\n"
                    print "setting node power max limit to 0...\n"
                    max_power_value = 0
                    
                nid = key 
                if max_power_value in max_power_data and max_power_data[max_power_value]:
                    max_power_data[max_power_value].append(int(nid))
                else:
                    max_power_data[max_power_value] = [int(nid)]
            semi = ""
            for key in max_power_data:
                max_power_data[key] = self.convert_node_list_to_sparse_string(max_power_data[key])
                max_power_string = max_power_string + semi + str(key) + ":" + max_power_data[key]
                semi = ";"

        return max_power_string
    
    def get_mem_size_dictionary(self):
        mem_size_dict = {} 
        mem_size_dict["mem_size_nid_lists"] = {} 
        
        #get mem_size_dict from SYSTEM_STATE cache if possible
        if "mem_size_dict" in self.SYSTEM_STATE and self.SYSTEM_STATE["mem_size_dict"]:
            mem_size_dict = self.SYSTEM_STATE["mem_size_dict"]
        else:
            found_data = False 
            command = "xtprocadmin -a availmem"
            proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if proc.stdout:	
                for outline in proc.stdout:
                    if "Error" in outline:
                        return None 
                    else:
                        columns = outline.split()
                        if columns[0] == "NID":
                            continue
                        elif len(columns) > 4:
                            found_data = True
                            mem_size = str(columns[4])
                            nid = str(columns[0])
                            mem_size_dict[nid] = mem_size 
                            if mem_size in mem_size_dict["mem_size_nid_lists"]:
                                mem_size_dict["mem_size_nid_lists"][mem_size].append(int(nid))
                            else:
                                mem_size_dict["mem_size_nid_lists"][mem_size] = [int(nid)]
                if found_data:
                    self.SYSTEM_STATE["mem_size_dict"] = mem_size_dict 

        return mem_size_dict 
    
    def set_invfile(self,invfile):
        '''
        invfile - XML HWINV inventory file to set and load.
        '''
        self.invfile = invfile
        if os.path.isfile(self.invfile):
            self.load_invfile()
    
    def load_invfile(self):
        '''
        load XML tree to search. 
        '''
        self.hwinv_tree = ET.ElementTree() 
        self.hwinv_tree.parse(self.invfile) 
    
    def set_mem_size_dictionary(self,mem_size_dict):
        if mem_size_dict:
            self.SYSTEM_STATE["mem_size_dict"] = mem_size_dict 

    def set_node_info_dictionary(self,node_info_dictionary):
        self.SYSTEM_STATE['node_info_dict'] = node_info_dictionary

    def get_mem_sizes(self):
        mem_sizes = []
        fl = os.popen('cnselect -L availmem')
        mem_sizes = fl.read().strip('\n').split()
        fl.close()
        return mem_sizes
    
    def get_nid_memory_size(self,nid):
        nid_memory_size = None
        mem_size_dict = None 
        
        if nid: 
            nid = str(nid) 
            #get mem_size_dict from SYSTEM_STATE cache if possible
            if "mem_size_dict" in self.SYSTEM_STATE and self.SYSTEM_STATE["mem_size_dict"]:
                mem_size_dict = self.SYSTEM_STATE["mem_size_dict"]
            else:
                mem_size_dict = self.get_mem_size_dictionary()
                if mem_size_dict:
                    self.set_mem_size_dictionary(mem_size_dict)

            if mem_size_dict:
                if nid in mem_size_dict:
                    nid_memory_size = mem_size_dict[nid]

        return nid_memory_size
    
    def get_memory_size_nid_list(self,mem_size):
        mem_size_nid_list = None
        mem_size_dict = None 
        
        if mem_size: 
            mem_size = str(mem_size) 
            #get mem_size_dict from SYSTEM_STATE cache if possible
            if "mem_size_dict" in self.SYSTEM_STATE and self.SYSTEM_STATE["mem_size_dict"]:
                mem_size_dict = self.SYSTEM_STATE["mem_size_dict"]
            else:
                mem_size_dict = self.get_mem_size_dictionary()
                if mem_size_dict:
                    self.set_mem_size_dictionary(mem_size_dict)

            if mem_size_dict and "mem_size_nid_lists" in mem_size_dict:
                if mem_size in mem_size_dict["mem_size_nid_lists"]:
                    mem_size_nid_list = mem_size_dict["mem_size_nid_lists"][mem_size]

        return mem_size_nid_list 

    def get_nid_cname_map(self):
        nid_cname_map = {}
        #get nid_cname_map from SYSTEM_STATE cache if possible
        if "nid_cname_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["nid_cname_map"]:
            nid_cname_map = self.SYSTEM_STATE["nid_cname_map"]
        else:
            found_data = 0
            node_info_dictionary = self.get_node_info_dictionary() 
            nid_list = node_info_dictionary.keys()
            for i,nid in enumerate(nid_list):
                cname = node_info_dictionary[nid]["cname"]
                nid_cname_map[nid] = cname
                found_data = 1
            if found_data:
                self.SYSTEM_STATE["nid_cname_map"] = nid_cname_map
        return nid_cname_map

    def get_nid_from_cname(self,cname):
        nid = ""
        cname_nid_map = self.get_cname_nid_map()
        if cname_nid_map and cname in cname_nid_map:
            nid = cname_nid_map[cname]
        return nid 
    
    def get_nid_from_hostname(self,hostname):
        nid = ""
        hostname_nid_map = self.get_hostname_nid_map()
        if hostname_nid_map and hostname in hostname_nid_map:
            nid = hostname_nid_map[hostname]
        return nid 
    
    def get_nid_hostname_map(self):
        nid_hostname_map = {}
        if "nid_hostname_map" in self.SYSTEM_STATE and self.SYSTEM_STATE["nid_hostname_map"]:
            nid_hostname_map = self.SYSTEM_STATE["nid_hostname_map"]
        else:
            found_data = 0
            node_info_dictionary = self.get_node_info_dictionary() 
            nid_list = node_info_dictionary.keys()
            for i,nid in enumerate(nid_list):
                if "hostname" in node_info_dictionary[nid]:
                    hostname = node_info_dictionary[nid]["hostname"]
                else:
                    hostname = self.get_hostname_from_hostname_mask(nid)
                nid_hostname_map[nid] = hostname 
                found_data = 1
            if found_data:
                self.SYSTEM_STATE["nid_hostname_map"] = nid_hostname_map
        return nid_hostname_map
    
    def get_node_code_names_dictionary(self,node_info_dictionary=None):
        node_code_names_dict = None
        if node_info_dictionary: 
            node_code_names_dict = self.get_node_code_names_dictionary_from_node_info_dictionary(node_info_dictionary)  
        else:
            node_code_names_dict = self.get_node_code_names_dictionary_from_node_info_dictionary(self.get_node_info_dictionary())
        return node_code_names_dict

    def get_node_code_names_dictionary_from_node_info_dictionary(self,node_info_dictionary):
        node_code_names_dict = {} 
        for nid in node_info_dictionary.keys():
            if "cpu_type" in node_info_dictionary[nid] and node_info_dictionary[nid]["cpu_type"]:
                cpu_type = node_info_dictionary[nid]["cpu_type"]
                if (cpu_type in node_code_names_dict) and node_code_names_dict[cpu_type]:
                    node_code_names_dict[cpu_type].append(int(nid))
                else:
                    node_code_names_dict[cpu_type] = [int(nid)]

        return node_code_names_dict
    
    def get_xtprocadmin_info_dictionary(self,key_column_name="nid",attrs={"class":None,"status":"up"},field_key_map={"class":"cpu_type","nodename":"cname","type":"node_type"}):
        info_dictionary = {}
        field_index_map = {}
        requested_attribute_keys = []
        attribute_parameters = ""

        #force default to nid
        if not key_column_name:
            key_column_name = "nid"

        #build the -a paramater from attrs
        if attrs and isinstance(attrs,dict):
            requested_attribute_keys = attrs.keys()
            if requested_attribute_keys:
                attribute_parameters = " -a "
                comma = ""
                for attribute_key in requested_attribute_keys:
                    attribute_parameters = attribute_parameters + comma + attribute_key
                    comma = ","
        
        requested_attribute_keys = list(set(requested_attribute_keys + ["nid","nodename","type"]))

        command = "xtprocadmin" + attribute_parameters
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:	
            for i,out_line in enumerate(proc.stdout):
                fields = out_line.split()
                len_fields = len(fields)
                if i == 0:
                    field_index_map[key_column_name] = self.get_column_label_index(fields,attribute_key)
                    if requested_attribute_keys:
                        for attribute_key in requested_attribute_keys:
                            field_index_map[attribute_key] = self.get_column_label_index(fields,attribute_key.upper())
                else:
                    entry_matches_constraints = True
                    current_key_name = fields[field_index_map[key_column_name]]
                    current_dict = {}
                    for attribute_key in requested_attribute_keys:
                        mapped_attribute_key = attribute_key
                        if attribute_key in field_key_map and field_key_map[attribute_key] is not None:
                            mapped_attribute_key = field_key_map[attribute_key] 

                        if attribute_key in attrs and attrs[attribute_key] is not None:
                            #make sure the current value equals one of the target values
                            if isinstance(attrs[attribute_key],list):
                                found_list_match = False
                                if field_index_map[attribute_key] < len_fields:
                                    for target_value in attrs[attribute_key]:
                                        if target_value in fields[field_index_map[attribute_key]]:
                                            current_dict[mapped_attribute_key] = fields[field_index_map[attribute_key]]
                                            found_list_match = True 
                                    entry_matches_constraints = found_list_match 
                            #make sure the current value equals the target value
                            elif field_index_map[attribute_key] < len_fields and attrs[attribute_key] == fields[field_index_map[attribute_key]]:
                                current_dict[mapped_attribute_key] = fields[field_index_map[attribute_key]]
                                entry_matches_constraints = True 
                            #current value doesn't match constraints
                            else:
                                entry_matches_constraints = False 
                        elif field_index_map[attribute_key] < len_fields:
                            current_dict[mapped_attribute_key] = fields[field_index_map[attribute_key]]
                    if entry_matches_constraints:
                        info_dictionary[current_key_name] = current_dict 
        
        if info_dictionary:
            info_dictionary = self.update_diags_cpu_types(info_dictionary)
        
        return info_dictionary
    
    def get_node_info_dictionary(self,node_info_script=None,node_list=None,node_count=None,partition=None,use_probe=False):
        if "node_info_dict" in self.SYSTEM_STATE and self.SYSTEM_STATE["node_info_dict"]:
            return self.SYSTEM_STATE["node_info_dict"]
        
        if use_probe:
            node_info_dict = self.get_node_probe_dictionary(node_info_script,node_list,node_count,partition)
        else:
            node_info_dict = self.get_xtprocadmin_info_dictionary() 
            if node_list:
                pruned_dict = {}
                for nid in node_list:
                    if str(nid) in node_info_dict:
                        pruned_dict[str(nid)] = node_info_dict[str(nid)] 
                node_info_dict = pruned_dict 
        
        self.set_node_info_dictionary(node_info_dict)
        return node_info_dict
   
    def get_node_inventory_dictionary(self,invfile_path=None):
        node_inventory_dict = {}
        if not invfile_path:
            invfile_path = "/etc/opt/cray/sdb/attr.xthwinv.xml"
        
        self.set_invfile(invfile_path)
        root = self.hwinv_tree.getroot()

        #code to traverse hwinv_tree
        for child in root.findall('./node_list/node'):
            cpu_class = ''
            cpu_speed = ''
            cpu_cores = 0
            cpu_hyperthreads = 0
            cpu_stepping_str = ''
            cpu_brand_str = ''
            cpu_ppin = []
            cpuid = ''
            for proc in child.findall('./processor_list'):
                cpu_hyperthreads = int(proc.find('hyper_threads').text)
                cpu_cores = int(proc.find('cores').text)

            for proc in child.findall('./processor_list/processor/die'):
                if proc.find('step_str') is not None:
                    cpu_stepping_str = proc.find('step_str').text
                if proc.find('brand_string') is not None:
                    cpu_brand_str = proc.find('brand_string').text
                if 'cpuid' in proc.attrib and proc.attrib['cpuid'] is not None:
                    cpuid = proc.attrib['cpuid']

            for ppin in child.findall('./processor_list/processor/die/ppin'):
                cpu_ppin.append(ppin.text)

            for proc in child.findall('./processor_list/processor'):
                cpu_class = proc.attrib['class']
                cpu_speed = proc.attrib['speedGHz']

            ram_total = ''
            ram_speed = ''
            ram_partnums = []
            ram_serialnums = []
            for mem in child.findall('./memory'):
                ram_total = mem.attrib['size'] + mem.attrib['units']

            for meminfo in child.findall('./memory/dimm'):
                ram_vendor = meminfo.find('mfg').text
                ram_speed = meminfo.find('speed').text

            for dimm in child.findall('./memory/dimm/partnum'):
                ram_partnums.append(dimm.text)

            for dimm in child.findall('./memory/dimm/serialnum'):
                ram_serialnums.append(dimm.text)
            
            #populate a node_info instance 
            node_info = {} 
            node_info['cname'] = child.attrib['id'] 
            node_info['nid'] = child.attrib['nid'] 
            node_info['hostname'] = self.get_hostname_from_hostname_mask(child.attrib['nid']) 
            node_info['cpuid'] = cpuid 
            node_info['cpu_type'] = self.get_cpu_type_from_cpuid(cpuid) 
            node_info['tcrit'] = '000000000'
            node_info['cpu_class'] = cpu_class
            node_info['cpu_speed'] = cpu_speed
            node_info['cpu_cores'] = cpu_cores
            node_info['cpu_hyperthreads'] = cpu_hyperthreads
            node_info['cpu_stepping_str'] = cpu_stepping_str
            node_info['cpu_brand_str'] = cpu_brand_str
            node_info['cpu_ppin'] = cpu_ppin
            node_info['ram_partnums'] = ram_partnums 
            node_info['ram_serialnums'] = ram_serialnums 
            node_info['ram_speed'] = ram_speed 
            node_info['ram_total'] = ram_total 
            node_info['ram_vender'] = ram_vendor 

            #add instance to dictionary
            node_inventory_dict[node_info['nid']] = node_info

        return node_inventory_dict
    
    def get_node_probe_dictionary(self,node_probe_script=None,node_list=None,node_count=None,partition=None):
        raise RuntimeError(self.RUNTIME_ERROR_INHERITANCE + ": get_node_probe_dictionary")

    def get_node_list_code_names(self,code_names_dict=None,node_list=None):
        code_names_list = []
        if not node_list:
            node_list = self.expand_node_list(self.get_node_list())
        if not code_names_dict:
            #code_names_dict = self.get_node_code_names_dictionary(None,node_list)
            code_names_dict = self.get_node_code_names_dictionary(None)

        if code_names_dict:
            for key in code_names_dict.keys():
                intersection_list = self.get_node_list_intersection(code_names_dict[key],node_list)
                if intersection_list:
                    code_names_list.append(key)
        
        return code_names_list
    
    def get_node_list_cpu_cores_mem_types_dict(self,node_list=None,node_info_dict=None,num_cores_dict=None,mem_size_dict=None):
        node_list_cpu_cores_mem_types_dict = {} 
        
        if not node_list:
            node_list = self.expand_node_list(self.get_node_list())
        if not node_info_dict:
            node_info_dict = self.get_node_info_dictionary()
        if not mem_size_dict:
            mem_size_dict = self.get_mem_size_dictionary()
        if not num_cores_dict:
            num_cores_dict = self.get_num_cores_dictionary()

        for nid in node_list:
            nid = str(nid)
            key_name = "unknown"
            cpu_type = ""
            mem_size = ""
            num_cores = ""

            if nid in node_info_dict:
                cpu_type = node_info_dict[nid]['cpu_type']
                if cpu_type:
                    key_name = str(cpu_type)
            if nid in num_cores_dict:
                num_cores = num_cores_dict[nid]
                if num_cores:
                    key_name = key_name + "_" + str(num_cores)
            if nid in mem_size_dict:
                mem_size = mem_size_dict[nid]
                if mem_size:
                    key_name = key_name + "_" + str(mem_size)
            
            if key_name in node_list_cpu_cores_mem_types_dict:
                node_list_cpu_cores_mem_types_dict[key_name].append(nid)
            else:
                node_list_cpu_cores_mem_types_dict[key_name] = [nid]
        
        return node_list_cpu_cores_mem_types_dict 

    def get_node_list_intersection(self,list_a,list_b):
        return  list(set.intersection(*[set(list_a), set(list_b)]))

    def get_node_list(self,query_string=""):
        fl = os.popen('cnselect ' + query_string)
        node_list = fl.read().strip('\n')
        fl.close()
        return node_list
    
    def get_idle_node_list(self,node_count=None,node_list=None):
        idle_node_list = []
        if not node_count:
            node_count = float('inf')
         
        if not node_list:
            node_list = self.expand_node_list(self.get_node_list())
            if node_list: 
                node_list.reverse()
        
        if node_list: 
            for nid in node_list:
                if len(idle_node_list) < node_count:
                    if self.node_ready_for_job_submission(nid):
                        idle_node_list.append(nid)
                else:
                    break
        
        return idle_node_list


    def get_node_mem_size(self,nid):
        node_mem_size = None 
        command = "xtprocadmin -a availmem -n " + str(nid)
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:	
            for outline in proc.stdout:
                if "Error" in outline:
                    return node_mem_size
                else:
                    columns = outline.split()
                    if columns[0] == "NID":
                        continue
                    else:
                        node_mem_size = int(columns[4])
        return node_mem_size

    def get_num_available_nodes(self):
        raise RuntimeError(self.RUNTIME_ERROR_INHERITANCE + ": get_num_available_nodes")

    def get_num_core_sizes(self):
        fl = os.popen('cnselect -L numcores | wc -l')
        num_core_types = fl.read().strip('\n')
        fl.close()
        return num_core_types

    def get_num_cores_dictionary(self):
        num_cores_by_node = {} 
        command = "xtprocadmin -a CPUs"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:	
            for outline in proc.stdout:
                if "Error" in outline:
                    return None 
                else:
                    columns = outline.split()
                    if columns[0] == "NID":
                        continue
                    elif len(columns) > 4:
                        num_cores_by_node[str(columns[0])] = str(columns[4])
        return num_cores_by_node 
    
    def get_num_failures(self,log_file_name):
        fl = os.popen('grep -n FAIL ' + log_file_name + " | wc -l")
        num_failures = fl.read().strip('\n')
        fl.close()
        return num_failures

    def get_num_mem_sizes(self):
        fl = os.popen('cnselect -L availmem | wc -l')
        num_mem_sizes = fl.read().strip('\n')
        fl.close()
        return num_mem_sizes
   
    def get_num_nodes(self):
        fl = os.popen('cnselect -c')
        num_nodes = fl.read().strip('\n')
        fl.close()
        return num_nodes

    def get_nvidia_model_names(self,accelerator_configuration_dict=None):
        nvidia_names = ['Tesla_K20X', 'Tesla_K40s'] 
        if not accelerator_configuration_dict:
            accelerator_configuration_dict = self.get_accelerator_configuration()
    
        if accelerator_configuration_dict: 
            keys = accelerator_configuration_dict.keys() 
            for name in nvidia_names:
                if not (name in keys):
                    nvidia_names.remove(name)
        else:
            nvidia_names = []
        return nvidia_names

    def get_phi_model_names(self,processor_configuration_dict=None):
        phi_names = ['knl']
        if not processor_configuration_dict:
           
            processor_configuration_dict = self.get_processor_configuration()

        if processor_configuration_dict: 
            keys = processor_configuration_dict.keys()
            for name in phi_names:
                if not (name in keys):
                    phi_names.remove(name)
        else:
            phi_names = []
        return phi_names

    def get_power_and_thermal_data_from_smw(self,destination_hostname,first,last,windows,apid_list,smw_filename,local_filename,smw_utils_path=None,node_list=None,post_processing=None):
        """Runs xtvrm_pm_data.py on the SMW to pull power and temp data from pmdb 
        Args:
            destination_hostname: the host to contact
            smw_utils_path: path override to xtvrm_pm_data.py 
            first: username
            last: password
            apid_list: list of apids to get related power and thermal data for  
            smw_filename: remote file to write data to and copy data from
            local_filename: local file to copy data to
        Returns:
            None
        """
        print "Gathering power and thermal data for apids " + str(apid_list)
        if not smw_utils_path:
            smw_utils_path = "/opt/cray/aries/sysdiag/bin"
            
        if "node_info_dict" in self.SYSTEM_STATE and self.SYSTEM_STATE["node_info_dict"] and self.SYSTEM_STATE["node_info_dict"].values()[0]["tcrit"]:
            node_info_dict = self.SYSTEM_STATE['node_info_dict']
        else:
            node_info_dict = self.get_node_probe_dictionary(None,node_list)
            
        helper_command = smw_utils_path + "/xtvrm_pm_data.py"
        helper_command = helper_command + " -a " + ",".join(map(str,apid_list)) 
        helper_command = helper_command + " -o " + smw_filename 
        helper_command = helper_command + " -m " + self.get_tcrit_data(node_info_dict)
        helper_command = helper_command + " -k " + self.get_max_power_data(windows, node_info_dict)
        
        #Command needs -f (start command set to run in background), try 4 times to pull data from SMW 
        ssh_command = "ssh -f " + first + "@" + destination_hostname + " \"" + helper_command + "\""
        data = self.run_ssh_command(ssh_command,last,360)
        for i in range(1,4):
            time.sleep(5)
            try:
                self.transfer_results_from_smw(destination_hostname,local_filename,smw_filename,first,last)
                break
            except:
                if (i < 4):
                    print "failed to grab files from SMW. Attempt " + str(i+1) + " of 4"
                else:
                    print "failed to get power/temp files from SMW"
                    raise Exception
        
        if post_processing:
            for apid in apid_list:
                self.transfer_results_from_smw(destination_hostname,local_filename.replace(".json","") + "_" + str(apid) + "_thermal_time_series.csv",smw_filename.replace(".json","") + "_" + str(apid) + "_thermal_time_series.csv",first,last)
                self.transfer_results_from_smw(destination_hostname,local_filename.replace(".json","") + "_" + str(apid) + "_power_time_series.csv",smw_filename.replace(".json","") + "_" + str(apid) + "_power_time_series.csv",first,last)

    def get_processor_configuration(self,node_info_dict=None,exclude_service_nodes=True,exclude_down_nodes=True):
        processor_configuration = {} 
        if not node_info_dict:
            node_info_dict = self.get_node_info_dictionary()

        if node_info_dict:
            for nid in node_info_dict.keys():
                if exclude_service_nodes and "node_type" in node_info_dict[nid] and node_info_dict[nid]["node_type"] == "service":
                    continue
                if exclude_down_nodes and "status" in node_info_dict[nid] and node_info_dict[nid]["status"] == "down":
                    continue
                if "cpu_type" in node_info_dict[nid] and node_info_dict[nid]["cpu_type"]:
                    model_name = node_info_dict[nid]["cpu_type"]

                    if model_name in processor_configuration:
                        (node_count,node_list) = processor_configuration[model_name]
                        node_list.append(int(str(nid)))
                        node_list = sorted(node_list, key=int)
                        node_count += 1
                    else:
                        node_list = [int(str(nid))]
                        node_count = 1
                
                    processor_configuration[model_name] = (node_count,node_list)

        return processor_configuration
    
    def get_rank(self,num_nodes=None):
        rpn = 1
        if not num_nodes:
            num_nodes = self.get_num_nodes()
        MAXNODES_PER_CABINET = 192
        MAXNODES_PER_GROUP = MAXNODES_PER_CABINET * 2
        TWO_GROUPS = MAXNODES_PER_GROUP * 2
        if num_nodes >= TWO_GROUPS:
            rpn = 1
        elif num_nodes >= MAXNODES_PER_GROUP and num_nodes <= TWO_GROUPS:
            rpn = 2
        elif num_nodes < MAXNODES_PER_GROUP:
            rpn = 4
        return str(rpn)

    def get_smw_info(self,override_user=None):
        user = "crayadm"
        if override_user:
            user = override_user
        print "Please enter SMW info"
        passwd = getpass.getpass()
        return (user,passwd)

    def get_smw_name(self):
        uname_cmd = 'uname -n'

        fl = os.popen(uname_cmd)
        uname = fl.read().strip('\n')
        smw_name = ''
        if 'clogin' in uname:
            smw_name = uname.replace('clogin','cst')
        else:
            smw_name = uname + '-smw'
        return smw_name

    def get_standard_modules_list(self):
        standard_test_list = []
        util_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
        util_path_components = util_dir.split("/")
        util_path_components.remove("util")
        tests_dir = "/".join(util_path_components) + "/tests"
    
        for dirname, dirnames, filenames in os.walk(tests_dir):
            # print path to all filenames.
            for filename in filenames:
                if "_test.py" in filename and not "test.pyc" in filename:
                    module_name = os.path.splitext(filename)[0]
                    standard_test_list.append(module_name)    

        return standard_test_list 

    def get_tcrit_data(self,node_info_dict):
        tcrit_data = {}
        tcrit_string = ""
        if node_info_dict:
            for key in node_info_dict.keys():
                tcrit_value = node_info_dict[key]["tcrit"][:-3]
                nid = key 
                if tcrit_value in tcrit_data and tcrit_data[tcrit_value]:
                    tcrit_data[tcrit_value].append(int(nid))
                else:
                    tcrit_data[tcrit_value] = [int(nid)]
            semi = ""
            for key in tcrit_data:
                tcrit_data[key] = self.convert_node_list_to_sparse_string(tcrit_data[key])
                tcrit_string = tcrit_string + semi + str(key) + ":" + tcrit_data[key]
                semi = ";"

        return tcrit_string

    def get_total_num_cores_system(self):
        cores_dict = self.get_cores_system()
        return cores_dict['total_cores']
    
    def get_user_specified_node_list_from_node_code_names_dictionary(self,node_code_names_dictionary):
        user_specified_node_list = [] 
        for key in node_code_names_dictionary:
            user_specified_node_list.extend(node_code_names_dictionary[key])
        return user_specified_node_list

    def get_user_specified_node_list(self,cnames_dict=None,cnames_csv=None):
        node_list = []
        if cnames_csv:
            if not cnames_dict:
                cnames_dict = self.get_cnames_dictionary()
                if not cnames_dict:
                    print "%s get_user_specified_node_list unable to determine cnames_dictionary, unable to proceed" % (time.strftime("%Y%m%d%H%M%S"))
                    return None 
        
            cname_list = cnames_csv.split(",")
            for cname in cname_list:
                if cname in cnames_dict:
                    node_list = list(set(node_list + cnames_dict[cname]))
                else:
                    print "system_configuration.get_user_specified_node_list: current cname not in cnames_dict: " + cname 
                    
        node_list.sort()
        return node_list

    def get_wlm(self):
        wlm = None
        if not 'wlm' in self.SYSTEM_STATE:
            wlm = get_wlm()
            self.SYSTEM_STATE['wlm'] = wlm  
        else:
            wlm = self.SYSTEM_STATE['wlm']
        return wlm 

    def kill_user_jobs(self,user,apids=None):
        raise RuntimeError(self.RUNTIME_ERROR_INHERITANCE)

    def next_power_of_2(self,n):
        """
        Return next power of 2 greater than or equal to n
        """
        n -= 1 # greater than OR EQUAL TO n
        shift = 1
        while (n+1) & n: # n+1 is not a power of 2 yet
            n |= n >> shift
            shift <<= 1
        return n + 1

    def parse_script_template(self,arg_obj):
        
        script_template_path = arg_obj["script_template_path"]
        script_template_string = ""
        with open(script_template_path) as template_file_handle:
            script_template_string = template_file_handle.read() 

        template_context = arg_obj["template_context"]
         
        template = Template(script_template_string)
        script_template_string = template.render(template_context)

        return script_template_string
    
    def publish_script_template(self,arg_obj):
        path_to_published_script = None 
        if arg_obj:
            script_string = self.parse_script_template(arg_obj)
            script_work_path = arg_obj["script_work_path"]
            if script_string and script_work_path:
                with open(script_work_path, "w") as script_file:
                    script_file.write(script_string)
                path_to_published_script = script_work_path 
            os.chmod(path_to_published_script,0775)

        return path_to_published_script 
    
    def previous_power_of_2(self,n):
        return 2**(int(math.log(n, 2)))
        
    ## run an scp command
    # inputs:
    # scp_cmd: a fully formed scp command
    def run_scp_command(self,scp_cmd,last):
        if not scp_cmd:
            return 1
        else:
            try:
                print "transfering file: "
                print scp_cmd
                child = pexpect.spawn(scp_cmd, timeout=180)
                i = child.expect(['authenticity','assword:'], timeout=30)
                if i == 0:
                    child.sendline("yes")
                    child.expect(['assword:'], timeout=30)
                    child.sendline(last)
                    data = child.read()
                    print data
                else:
                    child.sendline(last)
                    data = child.read()
                    print data
                child.close()

            except KeyboardInterrupt as e:
                return 0
            except Exception as e:
                return 1
    
    ## run an arbitrary shell command
    # inputs:
    # shell_cmd: a fully formed command
    def run_shell_command(self,shell_cmd,logger=None,working_directory=None):
        if not shell_cmd:
            return 1	
        else:
            try:
                args = shlex.split(shell_cmd.encode('ascii'))
                proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=working_directory)
            
                if logger: 
                    if proc.stdout:	
                        for out_line in proc.stdout:
                            logger.info(out_line.strip("\n"))
            
                    if proc.stderr:	
                        for err_line in proc.stderr:
                            logger.error(err_line.strip("\n"))	
            
                returncode = proc.wait()
                return returncode
	
            except KeyboardInterrupt as e:
                if logger:
                    logger.info("Caught KeyboardInterrupt: " + str(e))
                return 0 
            except Exception as e:
                if logger:
                    logger.error("run_shell_command caught exception: " + str(e))
                return 1

    ## run an ssh/scp command
    # inputs:
    # ssh_cmd: a fully formed ssh command
    # last: password
    # cmd_timeout: timeout for remote command (in s)
    # returns:
    #   data: string output from ssh.  Returns None if aborted
    def run_ssh_command(self,ssh_cmd,last,cmd_timeout=180):
        if not ssh_cmd:
            print "missing SSH command"
            raise Exception
        else:
            try:
                print "running remote command: "
                print ssh_cmd
                child = pexpect.spawn(ssh_cmd, timeout=cmd_timeout)
                i = child.expect(['authenticity','assword:'], timeout=30)
                if i == 0:
                    child.sendline("yes")
                    child.expect(['assword:'], timeout=30)
                    child.sendline(last)
                    data = child.read()
                else:
                    child.sendline(last)
                    data = child.read()
                child.close()

            except KeyboardInterrupt as e:
                return None
            return data

    def sane_filename_request(self,filename):
        if "/tmp" in filename:
            return True
        else:
            return False

    def search_log(self,log_file_path,list_of_error_words,case_sensitive=0,error_match_exclusion_list=None,verify_logfile_is_not_empty=False):
        debug = 0 
        error_list = []
        max_tries = 10
        current_try = 0
        num_lines = 0
        if os.path.isfile(log_file_path) and list_of_error_words:
            if verify_logfile_is_not_empty:
                num_lines = self.file_len(log_file_path)
                while (num_lines <= 1) and current_try < max_tries:
                    num_lines = self.file_len(log_file_path)
                    current_try = current_try + 1
                    time.sleep(.5)
                    
            #print "examining " + log_file_path 

            with open(log_file_path) as f:
                for line in f:
                    if debug: print "examining " + log_file_path + ": " + line 
                    for error_word in list_of_error_words:
                        if not case_sensitive:
                            matches = re.findall(error_word,line,flags=re.IGNORECASE)
                        else:
                            matches = re.findall(error_word,line)
                        if matches:
                            if error_match_exclusion_list:
                                ignore = 0
                                for error_match_exclusion in error_match_exclusion_list:
                                    if error_match_exclusion in line:
                                        ignore = 1 
                                if not ignore:
                                    error_list.append(line)
                                    continue
                            else:
                                error_list.append(line)
                                continue
        return error_list
    
    def file_len(self,log_file_path):
        num_lines = 0
        if os.path.isfile(log_file_path):
            with open(log_file_path) as f:
                for l in enumerate(f):
                    num_lines = num_lines+1
        return num_lines

    def sort_logfile_list_by_node_type(self,logfile_list):
        sorted_logfile_dict = {}
        
        if logfile_list and len(logfile_list) > 0:
            for logfile in logfile_list:
                current_node_types = [] 
                if os.path.isfile(logfile):
                    #get the node_info from the first line of file
                    with open(logfile, 'r') as f:
                        first_line = f.readline()
                        if 'node_info:' in first_line:
                            jstring = first_line.replace('node_info:','')
                            current_node_info = json.loads(jstring.strip())
                            if current_node_info and current_node_info.keys():
                                for key in current_node_info.keys():
                                    current_node_types.append(key)
                
                if current_node_types:
                    for current_node_type in current_node_types:
                        if current_node_type in sorted_logfile_dict:
                            sorted_logfile_dict[current_node_type].append(logfile)
                        else:
                            sorted_logfile_dict[current_node_type] = [logfile]
                else:
                    if 'unknown' in sorted_logfile_dict:
                        sorted_logfile_dict['unknown'].append(logfile)
                    else:
                        sorted_logfile_dict['unknown'] = [logfile]

        return sorted_logfile_dict
    
    def source_intel_env_script(self,env_script_path): 
        if(not("MKLROOT" in os.environ)):
            compilervars_script_path = "/opt/intel/composerxe/bin/compilervars.sh" 
            if os.path.isfile(env_script_path) and os.path.isfile(compilervars_script_path): 
                args = shlex.split(env_script_path.encode('ascii'))
                proc=subprocess.Popen(args,stdout=subprocess.PIPE)
                if proc.stdout:
                    for line in proc.stdout:
                        if line:
                            (name,value) = line.strip("\n").split("=")
                            if name and value:
                                os.environ[name] = value

    def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def test_remote_file_exists(self,destination_hostname,smw_filename,first,last):
        """Test a SMW file exsists
        returns true or false
        Args:
            destination_hostname: SMW hostname
            first: username
            last: password
        Returns:
            status of if the file existed
        """
        ssh_test_command = "ssh " + first + "@" + destination_hostname + " test -f " + smw_filename + " && echo \"1\" || echo \"0\""
        result = self.run_ssh_command(ssh_test_command, last)
        return int(result)       
    
    def test_ssh_auth(self,destination_hostname,first,last):
        """Test an SMW SSH connection and credentials
        Throws general exception on connection fail
        Args:
            destination_hostname: SMW hostname
            first: username
            last: password
        Returns:
            none
        """
        print "Testing ssh connection..."
        ssh_test_command = "ssh " + first + "@" + destination_hostname + " echo TEST"
        data = self.run_ssh_command(ssh_test_command, last)
        if not "TEST" in data:
            raise RuntimeError( "Unable to open an SSH session to the SMW " + destination_hostname + \
                " .  Check the destination and login settings.")
        print "ssh connection successful"

    def transfer_results_from_smw(self,destination_hostname,local_filename,smw_filename,first,last):
        """Copies trim results file from the SMW
        Args:
            destination_hostname: the host to contact
            local_filename: local file to copy to
            smw_filename: remote file to copy from
            first: username
            last: password
        Returns:
            None
        """
        print "transfering results"
        #construct the scp command
        scp_command = "scp " + first + "@" + destination_hostname + ":" + smw_filename + " " + local_filename
        self.run_ssh_command(scp_command,last)
        if not os.path.exists(local_filename):
            print "unable to retrieve results file [" + smw_filename + "], exiting\n"
            raise Exception

    def transfer_trim_to_smw(self,destination_hostname,local_filename,smw_filename,first,last):
        """Copies trim deltas file to the SMW
        Args:
            destination_hostname: the host to contact
            local_filename: local file to send
            smw_filename: remote file to copy to
            first: username
            last: password
        Returns:
            None
        """
        print "transfering trim settings"
        if os.path.exists(local_filename):
            if self.sane_filename_request(smw_filename):
                #construct the scp command
                scp_command = "scp " + local_filename + " " + first + "@" + destination_hostname + ":" + smw_filename
                self.run_ssh_command(scp_command,last)
            else:
                print "unsane remote filename : " + str(smw_filename)
                raise Exception
        else:
            print "unable to find data file [" + path_to_concatenated_data_file + "], exiting\n"
            raise Exception

    def transfer_vrmscreen_results(self,transfer_results=False,input_file_list=None,destination_hostname=None,destination_filename=None,first=None,last=None):
        if transfer_results:
            print "transfering results"
            path_to_concatenated_data_file = ""
            if input_file_list:
                path_to_concatenated_data_file = self.concatenate_list_of_data_files(input_file_list)
        
            #concatenate each of the input_files
            if path_to_concatenated_data_file and os.path.exists(path_to_concatenated_data_file):
                print "path_to_concatenated_data_file: " + str(path_to_concatenated_data_file)
             
                #if not provided, prompt for the destination_folder
                if not destination_hostname:
                    destination_hostname = raw_input("\nEnter the destination hostname:\n")

                #if not provided, prompt for the destination_filename
                if not destination_filename:
                    destination_filename = raw_input("\nEnter the destination file name:\n")
           
                # do a sanity check on the destination_folder/destination_filename value
                if self.sane_filename_request(destination_filename):
                    #prompt for the login credentials on the destination_hostname
                    if not first or not last:
                        (first,last) = self.get_smw_info()
                
                    #construct the scp command
                    scp_command = "scp " + path_to_concatenated_data_file + " " + first + "@" + destination_hostname + ":" + destination_filename
                    self.run_scp_command(scp_command,last)
                else:
                    print "unsane destination_filename: " + str(destination_filename)
            else:
                print "unable to find data file [" + path_to_concatenated_data_file + "], exiting\n"
        else:
            print "not transfering results"

    def get_session_single_job_logfiles(self,job_logs_root,starting_timestamp,ending_timestamp=None):
        debug = 0 
        pruned_dirs = []
        session_logfiles = []
        general_timestamp_length = 20 
    
        if not starting_timestamp:
            return session_logfiles
    
        if len(starting_timestamp) < general_timestamp_length:
            num_missing_digits = general_timestamp_length - int(len(starting_timestamp))
            for x in range(0,num_missing_digits):
                starting_timestamp = starting_timestamp + "0"

        if not ending_timestamp:
            ending_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
        if debug: 
            print "sysconfig get_session_single_job_logfiles"
            print "job_logs_root: " + job_logs_root 
            print "starting_timestamp: " + starting_timestamp
            print "ending_timestamp: " + ending_timestamp

        if not os.path.exists(job_logs_root):
            return session_logfiles

        log_dirs = os.listdir(job_logs_root)
        if log_dirs:
            for log_dir in log_dirs:
                if log_dir <= ending_timestamp and log_dir >= starting_timestamp: 
                    pruned_dirs.append(log_dir)
        if pruned_dirs:
            for cur_dir in pruned_dirs:
                log_files = os.listdir(job_logs_root + "/" + cur_dir)
                if log_files:
                    for cur_log_file in log_files:
                        session_logfiles.append(job_logs_root + "/" + cur_dir + "/" + cur_log_file)            
        return session_logfiles 

    def get_session_component_test_toplevel_logfiles(self,job_logs_root,component_test_name,starting_timestamp,ending_timestamp=None):
        debug = 0 
        session_logfiles = []
        general_timestamp_length = 20 
    
        if not starting_timestamp:
            return session_logfiles
    
        if len(starting_timestamp) < general_timestamp_length:
            num_missing_digits = general_timestamp_length - int(len(starting_timestamp))
            for x in range(0,num_missing_digits):
                starting_timestamp = starting_timestamp + "0"

        if not ending_timestamp:
            ending_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
        if debug: 
            print "sysconfig get_session_component_test_logfiles"
            print "job_logs_root: " + job_logs_root 
            print "starting_timestamp: " + starting_timestamp
            print "ending_timestamp: " + ending_timestamp

        if not os.path.exists(job_logs_root):
            if debug: print "job_logs_root doesn't exist: " + job_logs_root 
            return session_logfiles
    
        top_level_candidates = []
        top_level_files = os.listdir(job_logs_root)
        if top_level_files:
            for top_level_file in top_level_files:
                if os.path.isfile(job_logs_root + "/" + top_level_file) and component_test_name in top_level_file and ".log" in top_level_file and not "check" in top_level_file:
                    top_level_candidates.append(top_level_file)
    
        for candidate_filename in top_level_candidates:
            filename_components = candidate_filename.split("_")
            if len(filename_components) > 1:
                if "error" in filename_components[-1]:
                    candidate_timestamp = filename_components[-2]
                else:
                    candidate_timestamp = filename_components[-1].replace(".log","")
                if candidate_timestamp and candidate_timestamp <= ending_timestamp and candidate_timestamp >= starting_timestamp: 
                    session_logfiles.append(job_logs_root + "/" + candidate_filename)            
    
        return session_logfiles 

    def get_session_application_managed_logfiles(self,job_logs_root,application_logfile_name,starting_timestamp,ending_timestamp=None):
        debug = 0 
        pruned_dirs = []
        session_logfiles = []
        general_timestamp_length = 20 
    
        if not starting_timestamp:
            return session_logfiles
    
        if len(starting_timestamp) < general_timestamp_length:
            num_missing_digits = general_timestamp_length - int(len(starting_timestamp))
            for x in range(0,num_missing_digits):
                starting_timestamp = starting_timestamp + "0"

        if not ending_timestamp:
            ending_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
        if debug: 
            print "sysconfig get_session_application_managed_logfiles"
            print "job_logs_root: " + job_logs_root 
            print "starting_timestamp: " + starting_timestamp
            print "ending_timestamp: " + ending_timestamp

        if not os.path.exists(job_logs_root):
            return session_logfiles

        log_dirs = os.listdir(job_logs_root)
        if log_dirs:
            for log_dir in log_dirs:
                if log_dir <= ending_timestamp and log_dir >= starting_timestamp: 
                    pruned_dirs.append(log_dir)
    
        if pruned_dirs:
            for cur_dir in pruned_dirs:
                log_dirs = os.listdir(job_logs_root + "/" + cur_dir)
                if log_dirs:
                    for cur_log_dir in log_dirs:
                        cur_log_file = job_logs_root + "/" + cur_dir + "/" + cur_log_dir + "/" + application_logfile_name
                        session_logfiles.append(cur_log_file)            
        return session_logfiles 

    def get_cname_from_nid_using_cnames_dictionary(self,nid):
        cname = str(nid) 
        nid = int(nid)
        cnames_dictionary = self.get_cnames_dictionary()
        if cnames_dictionary:
            for key in cnames_dictionary.keys():
                if "n" in key and nid in cnames_dictionary[key]: 
                    return key

        return cname

    def get_cname_and_timestamp_from_logfile_name(self,logfile_name,nodeinfo_in_logfile_name,timestamp_path_index=None,timestamp_component_index=None,node_path_index=None,node_component_index=None):
    
        out_tuple = None
        node_list_string = "" 
        timestamp_string = "" 
        cnames = ""
        timestamp = ""
    
        #convert inputs to integers 
        if timestamp_path_index is not None:
            timestamp_path_index = int(timestamp_path_index)
        if timestamp_component_index is not None:
            timestamp_component_index = int(timestamp_component_index)
        if node_path_index is not None:
            node_path_index = int(node_path_index)
        if node_component_index is not None:
            node_component_index = int(node_component_index)
   
        path_components = logfile_name.split("/")

        #determine cnames
        if nodeinfo_in_logfile_name:
            if node_path_index:
                node_component = path_components[node_path_index]
            else:    
                node_component = path_components[-1]
    
            node_component_parts = node_component.split("_") 
            if node_component_index is not None:
                if node_component_index >= 0:
                    comma = ""
                    for x in range(node_component_index,len(node_component_parts)):
                        node_list_string = node_list_string + comma + node_component_parts[x]
                        comma = ","
                else:
                    node_list_string = node_component_parts[node_component_index]
            else:
                node_list_string = node_component_parts[-1]
    
            if "." in node_list_string:
                #remove the file extension
                node_list_components = node_list_string.split(".")
                node_list_string = node_list_components[0]
    
            if not "c" in node_list_string:
                nid_list = self.expand_node_list(node_list_string)
                comma = ""
                for nid in nid_list:
                    cnames = cnames + comma + self.get_cname_from_nid_using_cnames_dictionary(nid)
                    comma = ","
            else:
                cnames = node_list_string
    
        #determine timestamp 
        if timestamp_path_index:
            timestamp_component = path_components[timestamp_path_index]
        else:    
            timestamp_component = path_components[-1]
    
        timestamp_component_parts = timestamp_component.split("_") 
        if timestamp_component_index: 
            timestamp_string = timestamp_component_parts[timestamp_component_index]
        else:
            timestamp_string = timestamp_component_parts[-1]
  
        timestamp = timestamp_string.replace(".log","")

        out_tuple = (timestamp,cnames)
    
        return out_tuple
    
    def update_diags_cpu_types(self,info_dictionary):
        for key in info_dictionary:
            current_entry = info_dictionary[key]
            if 'cpu_type' in current_entry:
                cpu_type = self.get_diags_cpu_type(current_entry['cpu_type'])
                arch_type = self.get_diags_arch_type(current_entry['cpu_type'])
                current_entry['cpu_type'] = cpu_type
                current_entry['arch'] = arch_type
                info_dictionary[key] = current_entry 
        return info_dictionary
    
    def get_diags_cpu_type(self,cpu_type):
        diags_cpu_type = "unknown"
        cpu_types_dict = self. get_diags_cpu_types_dict()
        if cpu_type in cpu_types_dict:
            diags_cpu_type = cpu_types_dict[cpu_type]
        
        return diags_cpu_type
    
    def get_diags_arch_type(self,cpu_type):
        diags_arch_type = "unknown"
        arch_types_dict = self. get_diags_arch_types_dict()
        if cpu_type in arch_types_dict:
            diags_arch_type = arch_types_dict[cpu_type]
        
        return diags_arch_type
   
    def set_diags_cpu_types_dict(self,cpu_types_dict=None):
        if not cpu_types_dict:
            cpu_types_dict = {}
            cpu_types_dict['SB'] = "snb"
            cpu_types_dict['IV'] = "ivb"
            cpu_types_dict['HW'] = "hsw"
            cpu_types_dict['BW'] = "bdw"
            cpu_types_dict['KL'] = "knl"
            cpu_types_dict['SK'] = "skl"
            cpu_types_dict['CL'] = "skl"
            cpu_types_dict['DC'] = "tx2"
            cpu_types_dict['UM'] = "tx2"
            cpu_types_dict['TX2'] = "tx2"
            cpu_types_dict['snb'] = "snb"
            cpu_types_dict['ivb'] = "ivb"
            cpu_types_dict['hsw'] = "hsw"
            cpu_types_dict['bdw'] = "bdw"
            cpu_types_dict['knl'] = "knl"
            cpu_types_dict['skl'] = "skl"
            cpu_types_dict['tx2'] = "tx2"
        self.SYSTEM_STATE['cpu_types_dict'] = cpu_types_dict
    
    def set_diags_arch_types_dict(self,arch_types_dict=None):
        if not arch_types_dict:
            arch_types_dict = {}
            arch_types_dict['SB'] = "x86_64"
            arch_types_dict['IV'] = "x86_64"
            arch_types_dict['HW'] = "x86_64"
            arch_types_dict['BW'] = "x86_64"
            arch_types_dict['KL'] = "x86_64"
            arch_types_dict['SK'] = "x86_64"
            arch_types_dict['CL'] = "x86_64"
            arch_types_dict['snb'] = "x86_64"
            arch_types_dict['ivb'] = "x86_64"
            arch_types_dict['hsw'] = "x86_64"
            arch_types_dict['bdw'] = "x86_64"
            arch_types_dict['knl'] = "x86_64"
            arch_types_dict['skl'] = "x86_64"
            arch_types_dict['DC'] = "aarch64"
            arch_types_dict['UM'] = "aarch64"
            arch_types_dict['TX2'] = "aarch64"
            arch_types_dict['tx2'] = "aarch64"
        self.SYSTEM_STATE['arch_types_dict'] = arch_types_dict
    
    def get_diags_cpu_types_dict(self):
        cpu_types_dict = {}
        if 'cpu_types_dict' in self.SYSTEM_STATE and self.SYSTEM_STATE['cpu_types_dict'] is not None:
            cpu_types_dict = self.SYSTEM_STATE['cpu_types_dict']
        else:
            self.set_diags_cpu_types_dict()
            cpu_types_dict = self.SYSTEM_STATE['cpu_types_dict']

        return cpu_types_dict 
    
    def get_diags_arch_types_dict(self):
        arch_types_dict = {}
        if 'arch_types_dict' in self.SYSTEM_STATE and self.SYSTEM_STATE['arch_types_dict'] is not None:
            arch_types_dict = self.SYSTEM_STATE['arch_types_dict']
        else:
            self.set_diags_arch_types_dict()
            arch_types_dict = self.SYSTEM_STATE['arch_types_dict']

        return arch_types_dict 


    def get_cpu_type_from_cpuid(self,cpuid=None):
        #TODO: put this in an ini once the conversion to json based ini files is made
        cpu_type = "UNKNOWN" 
        cpu_types_dict = {}
        cpu_types_dict[0x206d0] = "snb"
        cpu_types_dict[0x306e0] = "ivb"
        cpu_types_dict[0x306f0] = "hsw"
        cpu_types_dict[0x406f0] = "bdw"
        cpu_types_dict[0x50670] = "knl"
        cpu_types_dict[0x50650] = "skl"
        cpu_types_dict[0x516] = "tx2"

        if cpuid:
            cpuid = int(cpuid,16) 
            if (cpuid & 0xF0FF0) in cpu_types_dict and cpu_types_dict[(cpuid & 0xF0FF0)]:
                cpu_type = cpu_types_dict[(cpuid & 0xF0FF0)]
            elif (cpuid & 0x00FFF) in cpu_types_dict and cpu_types_dict[(cpuid & 0x00FFF)]:
                cpu_type = cpu_types_dict[(cpuid & 0xF0FF0)]
        
        return cpu_type 

class AlpsConfig(BaseConfig):
    
    def __init__(self):
        super(AlpsConfig,self).__init__()

    def get_age_user_jobs(self,user,apids,partition=None):
        #print "AlpsConfig.get_age_user_jobs()"
        apid_list = []
        command = "apstat -a"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:	
            for out_line in proc.stdout:
                fields = out_line.split()
                if len(fields) == 8:
                    (apid,resid,user_name,pes,nodes,age,state,command) = fields
                    if user_name == user and apid in apids:
                        age = string.rstrip(age,"m")
                        fields = age.split("h")
                        apid_list.append((apid,int(fields[0]),int(fields[1]))) 
        return apid_list
    
    def get_apids_by_name(self,username,testnames,partition=None):
        #print "AlpsConfig.get_apids_by_name()"
        apid_list = []
        header_list = []
        command = "apstat -a"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:	
            for out_line in proc.stdout:
                fields = out_line.split()
                if len(fields) >= 6:
                    if not header_list:
                        header_list = [field.strip().lower() for field in fields]
                    else:
                        apstat_user = fields[self.get_column_label_index(header_list,"user")]
                        apstat_command = fields[self.get_column_label_index(header_list,"command")]
                        apid = fields[self.get_column_label_index(header_list,"apid")]
                        for testname in testnames:
                            if username == apstat_user and apstat_command in testname: 
                                apid_list.append(apid) 
    
        return apid_list    
    
    def get_num_available_nodes(self):
        #print "AlpsConfig.get_num_available_nodes()"
        fl = os.popen("apstat -v | grep XT | awk '{print $3}'")
        num_nodes = fl.read().strip('\n')
        fl.close()
        return num_nodes

    def get_partition_available_node_list(self,partition=None,reservation=None):
        return self.expand_node_list(self.get_node_list())
    
    def kill_user_jobs(self,user,apids=None):
        #print "AlpsConfig.kill_user_jobs"
        return_status_list = []
        kill_list = []
        command = "apstat -a"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:	
            for out_line in proc.stdout:
                fields = out_line.split()
                if len(fields) > 5:
                    #(apid,resid,user_name,pes,nodes,age,state,command) = fields
                    apid = fields[0]
                    user_name = fields[2]
                    if apids and user_name == user and apid in apids: 
                        kill_list.append(("apkill -9 " + apid,apid))
    
        for cmd,apid in kill_list:
            proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return_code = proc.wait()
            return_status_list.append((apid,return_code))
    
        return return_status_list
    
    def get_node_probe_dictionary(self,node_probe_script=None,node_list=None,node_count=None,partition=None):
    
        node_probe_dict = {}
        command = ""

        if not node_probe_script:
            node_probe_script = self.FULL_PATH_TO_UTIL_DIR + "/get_node_info.sh"
    
        if node_list:
            command = "aprun -n " + str(len(node_list)) + " -N 1 -L " + self.convert_node_list_to_sparse_string(node_list) + " " + node_probe_script
        elif node_count:
            command = "aprun -n " + str(node_count) + " -N 1 " + node_probe_script
        else:
            node_list = self.expand_node_list(self.get_node_list())
            command = "aprun -n " + str(len(node_list)) + " -N 1 -L " + self.convert_node_list_to_sparse_string(node_list) + " " + node_probe_script
        if command:
            print command
            proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if proc.stdout:	
                for outline in proc.stdout:
                    if "Error" in outline:
                        return None 
                    elif not outline.startswith("Application"):
                        try:
                            node_info = json.loads(outline)
                            if node_info and "nid" in node_info:
                                nid = node_info["nid"]
                                node_probe_dict[nid] = node_info
                        except ValueError:
                            print("Could not convert data into node_info: " + outline)
        return node_probe_dict
    
    def node_list_ready_for_job_submission(self,nid_list,timeout_in_seconds=None):
        status = 1
        checkable_nid_list = []
        if nid_list:
            #check the first and last nodes on the list
            checkable_nid_list.append(nid_list[0])
            if len(nid_list) > 1:
                checkable_nid_list.append(nid_list[-1])
            checkable_nid_list.sort()
            for nid in checkable_nid_list:
                if not self.node_ready_for_job_submission(nid,timeout_in_seconds):
                    status = 0
                    break
        return status
    
    def node_ready_for_job_submission(self,nid,timeout_in_seconds=None):
        status = 0
        apid = ""
        
        if nid:
            command = "apmgr ping -g"
            if timeout_in_seconds:
                command = command + " -w " + str(timeout_in_seconds)
            command = command + " " + str(nid)
            proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if proc.stdout:
                for outline in proc.stdout:
                    apid = outline
            status = proc.wait()
        
        if apid:
            return 0 
        else:
            return 1 



class SlurmConfig(BaseConfig):
    
    def __init__(self):
        super(SlurmConfig,self).__init__()

    def get_age_user_jobs(self,user,apids=None,partition=None):
        #print "SlurmConfig.get_age_user_jobs()"
        age_tuples_list = []
        command = "squeue -u " + user
        if partition:
            command = command + " -p " + partition 
        command = command + " -o \"%i %u %j %t %M\"" 
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:	
            for i,out_line in enumerate(proc.stdout):
                fields = out_line.split()
                if i == 0: 
                    jobid_index = self.get_column_label_index(fields,"JOBID")
                    username_index = self.get_column_label_index(fields,"USER")
                    testname_index = self.get_column_label_index(fields,"NAME")
                    job_state_index = self.get_column_label_index(fields,"ST")
                    time_used_index = self.get_column_label_index(fields,"TIME")
                else:
                    if testname_index and username_index:
                        JOBID = fields[jobid_index]
                        USER_NAME = fields[username_index]
                        NAME = fields[testname_index]
                        STATE = fields[job_state_index]
                        TIME = fields[time_used_index]
                        if USER_NAME == user and JOBID in apids:
                            days = 0
                            hours = 0
                            mins = 0
                            secs = 0
                            time_components = TIME.split(":")
                            if time_components and len(time_components) > 0:
                                secs = time_components.pop() 
                                mins = time_components.pop()
                                if len(time_components) > 0:
                                    hours = time_components.pop() 
                                if len(time_components) > 0:
                                    days = time_components.pop() 
                            age_tuples_list.append((JOBID,int(hours),int(mins))) 
        return age_tuples_list

    def get_apids_by_name(self,username,testnames,partition=None):
        #print "SlurmConfig.get_apids_by_name()"
        apid_list = []
        testname_index = None 
        username_index = None 
        jobid_index = None 
        command = "squeue -u " + username
        if partition:
            command = command + " -p " + partition 
        command = command + " -o \"%i %u %j %t %M\"" 
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:	
            for i,out_line in enumerate(proc.stdout):
                fields = out_line.split()
                if i == 0: 
                    jobid_index = self.get_column_label_index(fields,"JOBID")
                    username_index = self.get_column_label_index(fields,"USER")
                    testname_index = self.get_column_label_index(fields,"NAME")
                    job_state_index = self.get_column_label_index(fields,"ST")
                    time_used_index = self.get_column_label_index(fields,"TIME")
                    #print "get_apids_by_name: testname_index: " + str(testname_index)
                    #print "get_apids_by_name: username_index: " + str(username_index)
                    #print "get_apids_by_name: jobid_index: " + str(jobid_index)
                else:
                    if testname_index and username_index:
                        for testname in testnames:
                            JOBID = fields[jobid_index]
                            USER_NAME = fields[username_index]
                            NAME = fields[testname_index]
                            STATE = fields[job_state_index]
                            #print "get_apids_by_name: testname: " + str(testname) + ", username: " + username
                            #print "get_apids_by_name: NAME: " + str(NAME) + ", USER_NAME: " + USER_NAME 
                            if USER_NAME == username and (NAME in testname) and ("R" in STATE):
                                apid_list.append(JOBID)
                    else:
                        print "SLURM get_apids_by_name: can't determine username and/or testname"

        return apid_list    
    
    def get_cnames_dictionary(self,partition=None,reservation=None):
        #get the set of available nids from sinfo
        if partition: 
            partition_down_nodes_list = self.get_partition_down_node_list(partition) 
        else:
            partition_down_nodes_list = [] 

        cnames = {}
        cnames["s0"] = []
        cnames["module_cnames"] = []
        command = "xtprocadmin"
        proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if proc.stdout:	
            for outline in proc.stdout:
                columns = outline.split()
                if len(columns)==6 and columns[3] == "compute":
                    cur_nid = int(columns[0])
                    if not cur_nid in partition_down_nodes_list:
                        cur_cname = columns[2]
                        cabinet_chassis = cur_cname.strip("c").split("c")
                        cabinet = cabinet_chassis[0]
                        chassis = cabinet_chassis[1]
                        cabinet_row = cabinet.split("-")
                        cabinet = cabinet_row[0]
                        row = cabinet_row[1]
                        chassis_module = chassis.split("s")
                        chassis = chassis_module[0]
                        module = chassis_module[1]
                        module_node=module.split("n")
                        module = module_node[0]
                        node = module_node[1]
                    
                        row_key = "cX-" + row 
                        if row_key in cnames:
                            cnames[row_key].append(cur_nid)
                        else:
                            cnames[row_key] = [cur_nid]
                 
                        cabinet_key = "c" + cabinet + "-" + row 
                        if cabinet_key in cnames:
                            cnames[cabinet_key].append(cur_nid)
                        else:
                            cnames[cabinet_key] = [cur_nid]
                 
                        chassis_key = cabinet_key + "c"  + chassis 
                        if chassis_key in cnames:
                            cnames[chassis_key].append(cur_nid)
                        else:
                            cnames[chassis_key] = [cur_nid]
                 
                        module_key = chassis_key + "s" + module 
                        if module_key in cnames:
                            cnames[module_key].append(cur_nid)
                        else:
                            cnames[module_key] = [cur_nid]
                        
                        if not module_key in cnames["module_cnames"]:
                            cnames["module_cnames"].append(module_key)
                 
                        node_key = module_key + "n" + node 
                        if node_key in cnames:
                            cnames[node_key].append(cur_nid)
                        else:
                            cnames[node_key] = [cur_nid]
                        cnames["s0"].append(cur_nid)              
            
        self.SYSTEM_STATE['cnames_dictionary'] = cnames 
        return cnames
    
    def get_node_probe_dictionary(self,node_probe_script=None,node_list=None,node_count=None,partition=None):
    
        node_probe_dict = {}
        
        if not node_probe_script:
            node_probe_script = self.FULL_PATH_TO_UTIL_DIR + "/get_node_info"
        
        command = ""
        if node_list:
            hostname_list = self.get_hostname_list_from_node_list(node_list)
            hostname_list_string = self.convert_hostname_list_to_sparse_string(hostname_list) 
            command = "srun --quiet"
            if partition:
                command = command + " -p " + partition
            command = command + " -n " + str(len(node_list)) + " --ntasks-per-node=1 --bcast=/tmp/" + os.path.basename(node_probe_script) + " --nodelist=" + hostname_list_string + " " + node_probe_script
        elif node_count:
            command = "srun --quiet" 
            if partition:
                command = command + " -p " + partition
            command = command + " -n " + str(node_count) + " --ntasks-per-node=1 " + node_probe_script
        else:
            node_list = self.expand_node_list(self.get_node_list())
            hostname_list = self.get_hostname_list_from_node_list(node_list)
            hostname_list_string = self.convert_hostname_list_to_sparse_string(hostname_list) 
            command = "srun --quiet"
            if partition:
                command = command + " -p " + partition
            command = command + " -n " + str(len(node_list)) + " --ntasks-per-node=1 --nodelist=" + hostname_list_string + " " + node_probe_script
        
        if command:
            print command
            proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if proc.stdout:	
                for outline in proc.stdout:
                    if "Error" in outline:
                        return None 
                    elif not outline.startswith("Application"):
                        try:
                            node_info = json.loads(outline)
                            if node_info and "nid" in node_info:
                                nid = node_info["nid"]
                                node_probe_dict[nid] = node_info
                        except ValueError:
                            print("Could not convert data into node_info: " + outline)
 
        return node_probe_dict

    def get_num_available_nodes(self):
        #print "SlurmConfig.get_num_available_nodes()"
        num_available_nodes = 0
        sinfo = self.get_sinfo("\"%F\"")
        if sinfo:
            aiot = sinfo[0]['NODES(A/I/O/T)'][0]
            num_available_nodes = aiot.split("/")[1]
        return num_available_nodes
    
    def get_partition_available_node_list(self,partition=None,reservation=None):
        partition_nodes_list = []
        down_nodes_list = []
        available_nodes_list = []
        format_string = "%N" 
        #format_string = None
        all_partition = partition 
        sinfo_list = self.get_sinfo(format_string,all_partition,None,reservation)
        if sinfo_list:
            node_list_dict = sinfo_list.pop()
            if 'NODELIST' in node_list_dict:
                value_list = node_list_dict['NODELIST']
                if value_list:
                    available_nodes_string = value_list.pop()
                    if available_nodes_string:
                        partition_nodes_list = self.expand_sparse_node_list_string(available_nodes_string) 
        
        down_nodes_list = self.get_partition_down_node_list(partition,reservation)
        
        available_nodes_list = [x for x in partition_nodes_list if x not in down_nodes_list]
        return available_nodes_list


    def get_partition_down_node_list(self,partition=None,reservation=None):
        down_nodes_list = []
        format_string = "%N" 
        partition = partition + " --states=DOWN,DRAIN "
        sinfo_list = self.get_sinfo(format_string,partition,None,reservation)
        if sinfo_list:
            #print "get_partition_down_node_list: sinfo_list: " + str(sinfo_list)
            node_list_dict = sinfo_list.pop()
            #print "get_partition_down_node_list: node_list_dict: " + str(node_list_dict)
            
            if 'NODELIST' in node_list_dict:
                value_list = node_list_dict['NODELIST']
                #print "get_partition_down_node_list: value_list: " + str(value_list)
                if value_list:
                    down_nodes_string = value_list.pop()
                    if down_nodes_string:
                        #print "get_partition_down_node_list: down_nodes_string: " + str(down_nodes_string)
                        down_nodes_list = self.expand_sparse_node_list_string(down_nodes_string) 
                        #print "get_partition_down_node_list: down_nodes_list: " + str(down_nodes_list)

        return down_nodes_list
    
    def expand_sparse_node_list_string(self,sparse_node_list_string):
        node_list = []
        #print "expand_sparse_node_list_string: " + str(sparse_node_list_string)
         
        #remove ending ]
        if "]" in sparse_node_list_string:
            sparse_string = sparse_node_list_string.replace("]","")
            #remove everthing before [
            sparse_string_components = sparse_string.split("[")
            if sparse_string_components and len(sparse_string_components)>1:
                node_list = self.expand_node_list(sparse_string_components[1])
        else:
            node_list = self.expand_node_list(sparse_node_list_string.replace("nid",""))

        return node_list
     
    def get_sinfo(self,format_string=None,partition=None,additional_options_string=None,reservation=None):
        sinfo = []
        header_fields = []
        format_parameters = ""
        partition_parameters = ""
        reservation_parameters = ""
        additional_parameters = ""
        
        #print "get_sinfo: format_string " + str(format_string) 
        if format_string:
            format_parameters = " -o \"" + format_string + "\""
        #print "get_sinfo: format_parameters" + format_parameters 
        
        if reservation:
            reservation_parameters = " -T " + reservation 
        elif partition:
            partition_parameters = " -p " + partition 
        
        if additional_options_string:
            additional_parameters = str(additional_options_string)
        
        command = "sinfo" + reservation_parameters + partition_parameters + format_parameters + additional_parameters
        #print "get_sinfo: command " + command 
        proc=subprocess.Popen(shlex.split(command),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.stdout:
            counter = 0
            for out_line in proc.stdout:
                delimiter = None 
                if "|" in out_line:
                    delimiter = "|"
                if counter == 0:
                    header_fields = out_line.strip('\n').split(delimiter)
                else:
                    partition_dict = {}
                    for i,field_value in enumerate(out_line.strip('\n').split(delimiter)):
                        field_name = header_fields[i].strip()
                        if not field_name in partition_dict:
                            partition_dict[field_name] = []
                        partition_dict[field_name].append(field_value.strip())
                    sinfo.append(partition_dict)
                counter = counter + 1
        return sinfo 
    
    def get_sconfig_option(self,option_name):
        if not option_name:
            return None
        
        sconfig_dictionary = self.get_sconfig_dictionary() 
        #keys = sconfig_dictionary.keys()
        #print "sconfig keys: " + str(keys)

        if option_name in sconfig_dictionary and sconfig_dictionary[option_name]:
            return sconfig_dictionary[option_name]
        else:
            return None 

    def get_sconfig_dictionary(self):
        if 'sconfig_dictionary' in self.SYSTEM_STATE and self.SYSTEM_STATE['sconfig_dictionary']:
            return self.SYSTEM_STATE['sconfig_dictionary']
        else:
            sconfig = {}
            command = "scontrol show config"
            proc=subprocess.Popen(shlex.split(command.encode('ascii')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if proc.stdout:	
                for outline in proc.stdout:
                    columns = outline.split()
                    if len(columns) >= 2 and columns[1] == "=":
                        cur_opt_name = columns[0]

                        if len(columns) == 2:
                            cur_opt_val = None
                        elif len(columns) > 3:
                            cur_opt_val = columns[2]
                            for i in range(3,len(columns)):
                                cur_opt_val += " " + columns[i]
                        else:
                            try:
                                cur_opt_val = int(columns[2])
                            except ValueError:
                                cur_opt_val = columns[2]
                        
                        sconfig[cur_opt_name] = cur_opt_val
                                   
            self.SYSTEM_STATE['sconfig_dictionary'] = sconfig 
            return sconfig
    
    def kill_user_jobs(self,user,apids=None):
        #print "SlurmConfig.kill_user_jobs"
        return_status_list = []
        kill_list = []
        
        if user and not apids:
            kill_list.append("scancel -u " + user)
        elif apids:
            for apid in apids:
                kill_list.append("scancel " + str(apid))
        
        if kill_list:
            for cmd in kill_list:
                proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                return_code = proc.wait()
                return_status_list.append((apid,return_code))
    
        return return_status_list
    
    def node_list_ready_for_job_submission(self,nid_list,timeout_in_seconds=None):
        status = 0 
        if nid_list:
            hostname_list = self.get_hostname_list_from_node_list(nid_list)
            sparse_nid_list_string = " -n " + self.convert_hostname_list_to_sparse_string(hostname_list)
            status_list = self.get_sinfo("%T",None,sparse_nid_list_string)
            if status_list:
                for i,status_dict in enumerate(status_list):
                    if "STATE" in status_dict and status_dict["STATE"]:
                        if len(status_dict["STATE"]) > 0:
                            if (status_dict["STATE"][0] == "idle" or status_dict["STATE"][0] == "reserved"):
                                status = 1
                            else:
                                status = 0
                    else:
                        status = 0
        return status
    
    def node_ready_for_job_submission(self,nid,timeout_in_seconds=None):
        status = 0
        if nid:
            hostname_list = self.get_hostname_list_from_node_list([int(nid)])
            sparse_nid_list_string = " -n " + self.convert_hostname_list_to_sparse_string(hostname_list)
            status_list = self.get_sinfo("%T",None,sparse_nid_list_string)
            if status_list:
                for i,status_dict in enumerate(status_list):
                    if "STATE" in status_dict and status_dict["STATE"]:
                        if len(status_dict["STATE"]) > 0:
                            if status_dict["STATE"][0] == "idle":
                                status = 1
                            else:
                                status = 0
                    else:
                        status = 0
        return status

#-----------------

if __name__ == '__main__':
    sc = BaseConfig.factory()
    node_list = sc.expand_node_list(sc.get_node_list())
    hostname_list = sc.get_hostname_list_from_node_list(node_list)
    sparse_slurm_string = sc.convert_hostname_list_to_sparse_string(hostname_list)
    print sparse_slurm_string 

    """     
    print get_wlm()
    #print "instantiating AlpsConfig" 
    #print "instantiating BaseConfig" 
    sc = BaseConfig.factory() 
    
    WLM = sc.get_wlm()
    print 'WLM: %s\n' % (str(WLM))
    
    hostname = sc.get_hostname_from_nid(41)

    STANDARD_MODULES_LIST = sc.get_standard_modules_list()
    print 'STANDARD_MODULES_LIST: %s\n' % (str(STANDARD_MODULES_LIST))
   
    NODE_LIST = sc.get_node_list()
    print 'NODE_LIST: %s\n' % (NODE_LIST) 
    
    NUM_NODES = sc.get_num_nodes()
    print 'NUM_NODES: %s\n' % (NUM_NODES) 
    
    NUM_CORE_SIZES = sc.get_num_core_sizes()
    print 'NUM_CORE_SIZES: %s\n' % (NUM_CORE_SIZES)
    
    LIST_CORE_SIZES = sc.get_list_core_sizes()
    print 'LIST_CORE_SIZES: %s\n' % (str(LIST_CORE_SIZES))
    
    NUM_AVAILABLE_NODES = sc.get_num_available_nodes()
    print 'NUM_AVAILABLE_NODES: %s\n' % (str(NUM_AVAILABLE_NODES))
 
    username = None 
    testname = None 
    
    APID_LIST = sc.get_apids_by_name(username,testname)
    print 'APID_LIST: %s\n' % (str(APID_LIST))
  
    AGE_LIST = sc.get_age_user_jobs(username,APID_LIST)
    print 'AGE_LIST: %s\n' % (str(AGE_LIST))

    NODE_INFO_DICTIONARY = sc.get_node_info_dictionary()
    print 'NODE_INFO_DICTIONARY: %s\n' % (str(NODE_INFO_DICTIONARY))
    
    NODE_CODE_NAMES = sc.get_node_code_names_dictionary()
    print 'NODE_CODE_NAMES: %s\n' % (str(NODE_CODE_NAMES))
    if "snb" in NODE_CODE_NAMES:
        print 'NUM SANDYBRIDGE: %s\n' % (len(NODE_CODE_NAMES['snb']))
    if "ivb" in NODE_CODE_NAMES:
        print 'NUM IVYBRIDGE: %s\n' % (len(NODE_CODE_NAMES['ivb']))
    if "hsw" in NODE_CODE_NAMES:
        print 'NUM HASWELL: %s\n' % (len(NODE_CODE_NAMES['hsw']))
    
    NODE_LIST_CODE_NAMES  = sc.get_node_list_code_names()
    print 'NODE_LIST_CODE_NAMES: %s\n' % (str(NODE_LIST_CODE_NAMES))
    """ 
# vim: set expandtab tabstop=4 shiftwidth=4:

