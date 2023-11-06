#!/usr/bin/env python
###############################################################################
# Copyright 2014-2015 Cray Inc. All Rights Reserved.
#
# xtvrm_screen_test.py - a wrapper script used in conjunction with xtvrm_screen_test.ini
#                       to execute the standard Cray xtcpudgemm diagnostic
#
# author: Pete Halseth
#
# The purpose of xtvrm_screen_test.py is to provide the means to include
# the standard Cray xtcpudgemm diagnostic as a component test in a list
# of tests grouped together in xtsystest.ini
#
# Usage:
# -------
# 1. To run as a standalone test: ./xtvrm_screen_test.py <options>
#    To see the available options, type: ./xtvrm_screen_test.py -h
#
# 2. To use within a script, just include the "import xtvrm_screen_test" statement at
# the top of the script
#
################################################################################
##@package tests.xtvrm_screen_test
# a tool to execute the Cray xtcpudgemm diagnostic
import os,shutil,time,subprocess,shlex,csv,re,json,tempfile,math

from base_test_component import BaseTestComponent

try:                                                                                                                            
    from workload.util import system_configuration
except:
    sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/../..")
    from workload.util import system_configuration
sysconfig = system_configuration.BaseConfig.factory()

class XTVrmScreen(BaseTestComponent):

    def __init__(self):

        # set self.FULL_PATH_TO_SCRIPT_DIR
        self.FULL_PATH_TO_SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

        # set self.COMPONENT_NAME
        if not hasattr(self,'COMPONENT_NAME'):
            self.COMPONENT_NAME = self.__class__.__name__

        # set self.MODULE_NAME
        if not hasattr(self,'MODULE_NAME'):
            (file_root,file_name) = os.path.split(os.path.realpath(__file__))
            (self.MODULE_NAME,ext) = os.path.splitext(file_name)

        self.read_phase2_windows(self.FULL_PATH_TO_SCRIPT_DIR + '/xtvrm_screen_windows.json')

        # initialize parent
        BaseTestComponent.__init__(self)

    def get_supported_nid_list(self,supported_processor_types):
        supported_nid_list = []
        if not supported_processor_types:
            supported_processor_types = ['hsw','bdw','skl']
        for processor_type in supported_processor_types:
            if processor_type in self.node_code_names_dict:
                type_list = self.node_code_names_dict[processor_type]
                if type_list:
                    supported_nid_list = supported_nid_list + type_list
        return supported_nid_list

    def get_aprun_parameters(self,number_of_test_copies=1):
        parameters = []
        
        aprun_parameter_template = self.get_aprun_parameter_template()
        if not aprun_parameter_template:
            aprun_parameter_template = "-n WIDTH -N NPPN -L NODE_LIST -m MEM_SIZE --cc=none"
       
        parameters = self.get_job_launcher_parameter_list(aprun_parameter_template)		
        return parameters 
    
    def get_srun_parameters(self,number_of_test_copies=1):
        parameters = []
        
        srun_parameter_template = self.get_srun_parameter_template()
        if not srun_parameter_template:
            #srun_parameter_template = "--exclusive -n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST --cpu_bind=none --time=90 --mem-per-cpu=MAX"
            #srun_parameter_template = "--exclusive -n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST --cpu_bind=none --time=90"
            #srun_parameter_template = "--exclusive -n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST --cpu_bind=none --mem-per-cpu=0 --time=90"
            srun_parameter_template = "--exclusive -n WIDTH --ntasks-per-node=NPPN --nodelist=NODE_LIST --cpu_bind=none --mem-per-cpu=0 --time=360"
        
        parameters = self.get_job_launcher_parameter_list(srun_parameter_template)		
        return parameters 
    
    def get_job_launcher_parameter_list(self,parameter_template_string):
        parameters_list = []
        supported_nid_list = []

        supported_processor_types = self.get_component_option("supported_processor_types")
        if supported_processor_types:
            supported_processor_types = supported_processor_types.split(",")
        
        supported_nid_list = self.get_supported_nid_list(supported_processor_types)

        if supported_nid_list:
                supported_node_count = len(supported_nid_list)

                if 'user_specified_node_list' in self and self.user_specified_node_list:
                    intersection_list = sysconfig.get_node_list_intersection(supported_nid_list,self.user_specified_node_list)
                    if intersection_list:
                        self.node_list = intersection_list
                    else:
                        return parameters_list
                else:
                    self.node_list = supported_nid_list

                nids_by_core_size = self.get_list_of_nids_by_core_size(self.node_list)

                if nids_by_core_size:
                    for core_size_tuple in nids_by_core_size:
                        (core_size_string,nid_list) = core_size_tuple
                        
                        nids_by_mem_size = self.get_list_of_nids_by_mem_size(nid_list)
                        if nids_by_mem_size:
                            for mem_size_tuple in nids_by_mem_size:
                                (mem_size_string, nid_list) = mem_size_tuple
                                node_count = len(nid_list)
                                core_size_node_list_string = sysconfig.convert_node_list_to_sparse_string(nid_list)
                                if self.sysconfig.get_wlm() == self.sysconfig.SLURM:
                                    cur_host_list_string = self.sysconfig.convert_hostname_list_to_sparse_string(self.sysconfig.convert_node_list_to_hostname_list(nid_list))
                                else:
                                    cur_host_list_string = core_size_node_list_string

                                parameter_string = parameter_template_string.replace("NPPN",self.get_NPPN())
                                parameter_string = parameter_string.replace("WIDTH",str(node_count))
                                parameter_string = parameter_string.replace("NODE_LIST",cur_host_list_string)
                                
                                #Only needed with Alps to help support susspend/resume systems
                                if self.sysconfig.get_wlm() == self.sysconfig.ALPS:
                                    parameter_string = parameter_string.replace("MEM_SIZE",str(int(mem_size_string)/1024))
                                    
                                parameters_list.append((core_size_string,parameter_string,len(nid_list),core_size_node_list_string))
                                    
        
        return parameters_list

    def get_test_script_parameters(self,number_of_test_copies=1,node_list_string=None,num_PEs=None,job_label=None):

        smallest_size = float("inf")
        node_list = []
        if not node_list_string:
            return None
        else:
            node_list = sysconfig.expand_node_list(node_list_string)

        if not node_list:
            return None
        if 'mem_size_dict' in self:
            mem_size_dict = self.mem_size_dict
        else:
            mem_size_dict = sysconfig.get_mem_size_dictionary()

        if len(node_list) > 1:
            for nid in node_list:
                if float(mem_size_dict[str(nid)]) < smallest_size:
                    smallest_size = int(mem_size_dict[str(nid)])
        else:
            smallest_size = int(mem_size_dict[str(node_list[0])])

        # insure the nodes we want to screen responded in the last
        # xtvrmtrim report

        last_report_filename = self.get_component_option('xtvrmtrim_last_report')

        # if the above is null, then we don't have a report to test
        if last_report_filename:
            with open(last_report_filename, 'r') as last_report_file:
                last_report_csv = csv.reader(last_report_file)
                last_report_nodes = set()
                for (node, socket, trim_percent, iscale_pre, iscale_trim, limit) in last_report_csv:
                    if node in self.cnames_dictionary:
                        last_report_nodes |= set(self.cnames_dictionary[node]);

            missing_nodes = set(node_list).difference(last_report_nodes)

            if missing_nodes:
                missed_node_cnames = set()
                for missed_cname, missed_nid in self.cnames_dictionary.iteritems():
                    cname_regex = re.compile(r"c[0-9]+-[0-9]+c[0-9]s[0-9]+n[0-3]")
                    if missed_nid[0] in missing_nodes and cname_regex.match(missed_cname):
                        missed_node_cnames.add(missed_cname)
                print "Nodes missed or failed during previous SMW trim operation (xtvrmtrim):"
                print '\n'.join(sorted(missed_node_cnames))
                print "Check the component state on the SMW before restarting screen"
                raise RuntimeError('SMW trim operation failed on one or more nodes');

        test_script_parameter_template = self.get_test_script_parameter_template()
        if not test_script_parameter_template:
            test_script_parameter_template = ""

        node_memory_gb = smallest_size/1024
        ncores = int(job_label)/2
        test_script_parameters = test_script_parameter_template + " -nthreads " + str(ncores) + " -mem " + str(node_memory_gb)
        return test_script_parameters

    def calculate_cc_parameter(self,core_size_string,range=0):
        true_core_size = int(self.calculate_core_size(core_size_string))
        if int(range) == 0:
            last_core = true_core_size - 1
            return "0-" + str(last_core)
        else:
            last_core = (true_core_size * 2) - 1
            return str(true_core_size) + "-" + str(last_core)

    def calculate_core_size(self,core_size_string):
        return str(int(core_size_string)/4)

    def get_result_column_headers(self,input_file_name):
        """extract column headers from results file

        Args:

        Returns:
            tuple of column headers

        """
        column_headers = []
        with open(input_file_name,'r') as input_file:
            search_result = re.search(r' Cname.*,.*,.*,.*$', input_file.read(),re.MULTILINE)
            if search_result:
                csv_line = search_result.group(0)
                column_headers = csv_line.split(',')

                column_headers = [column.replace('Socket ',' ') for column in column_headers]

                # normalize fields to uppercase alpha only
                return [re.sub(r'(\(.*\))|([\/ ])', r'', column_header).upper() for column_header in column_headers]
            else:
                return column_headers

    def read_test_results(self,input_file_name,column_headers,exclusion_list=None,inclusion_list=None):
        """read test result log file into a list

        Args:
            input_file_name: file to read results from
            column_headers: list of column header strings in the
                same order as the fields in the log file output
            exclusion_list: list of strings indicating a line to ignore
            inclusion_list: list of regex strings to filter result lines by

        Returns: list of dicts containing the results keyed by
                column_header
        """
        inclusion_regex_list = []
        results = []
        if os.path.isfile(input_file_name):
            with open (input_file_name, "r") as input_file:
                line_list=input_file.readlines()

            if line_list:
                #compile each string in inclusion_list into a regular expression
                if inclusion_list:
                    for include_str in inclusion_list:
                        inclusion_regex_list.append(re.compile(include_str))

                xtsystest_strip_regex = re.compile(r"INFO - ")
                cname_regex = re.compile(r"c[0-9]+-[0-9]+c[0-9]s[0-9]+n[0-3]")
                nid_regex = re.compile(r"nid[0-9]*")

                strip_nuls_regex = re.compile(r'\x00')

                for line in line_list:
                    skip_line = False

                    line = strip_nuls_regex.sub('',line)

                    if exclusion_list:
                        for exclude_str in exclusion_list:
                            if exclude_str in line:
                                skip_line = True
                                continue

                    if inclusion_regex_list:
                        for inclusion_regex in inclusion_regex_list:
                            if not inclusion_regex.search(line):
                                skip_line = True
                                continue
                    record_dict = {}
                    if not skip_line:
                        #strip out unnecessary xtsystest stuff and split by commas
                        fields = xtsystest_strip_regex.split(line,maxsplit=1)[-1].split(",")

                        # there must be as many records as column headers
                        if len(column_headers) == len(fields):
                            field_index = 0
                            for field in fields:
                                if field:
                                    record_dict[column_headers[field_index]] = field.strip()
                                    field_index += 1
                            results.append(record_dict)
        if len(results) == 0:
            raise RuntimeError("No valid results found from test jobs")
        return results

    def run(self):
        #CAEXC-1375 - removing the symlinked binaries before the run if post-
        #    processing was enabled
        if (self.get_component_option('post_processing_mode')):
            for test_command in self.validated_test_commands:
                if 'test_work_path' in test_command:
                    work_dir = os.path.dirname(test_command['test_work_path'])
                    if os.path.isdir(work_dir) and os.path.isfile(test_command['test_work_path']):
                        os.remove(test_command['test_work_path'])
        
        BaseTestComponent.run(self)

    def compute_phase2_averages(self, results):
        """Create a dict of BIN averages keyed by CPU brand
        strings.
        Args:
            results: List of result dicts, must have "BIN" and "CPUBRAND"
                    keys
        Returns:
            dict of BIN averages keyed by filtered CPU brand
                (see cpubrand_filter())
        """
        if results:
            avgs = {}
            counts = {}
            for result in results:
                brand = sysconfig.cpubrand_filter(result["CPUBRAND"])
                if brand in counts:
                    counts[brand] += 1.0
                else:
                    counts[brand] = 1.0
                if brand in avgs:
                    avgs[brand] += float(result["BIN"])
                else:
                    avgs[brand] = float(result["BIN"])
            for brand in avgs:
                avgs[brand] = avgs[brand] / counts[brand]
            return avgs
        else:
            raise RuntimeError("No results found, can't compute averages")

    def read_phase2_windows(self, filename):
        sku_windows_serialized = open(filename,'r').read()
        self.windows = json.loads(sku_windows_serialized)
        if not self.windows:
            raise RuntimeError("Error loading trim window config file " + filename)
        window_keys = [ "bottom", "top", "margin_bottom", "margin_top",\
                        "mhz_factor", "clamp_low", "clamp_high", "node_pwr_max_limit" ]
        # validate file
        for sku in self.windows:
            if not self.windows[sku]:
                raise RuntimeError('Window config file missing SKU "' + sku + '"')
            for socket in self.windows[sku]:
                if not self.windows[sku][socket]:
                    raise RuntimeError('Window config file missing socket "' + socket + '" for SKU "' + sku + '"')
                for field in window_keys:
                    if not field in self.windows[sku][socket]:
                        raise RuntimeError('Window config file missing field "' + field + '" for socket "' + socket + '" and SKU "' + sku + '"')

    def compute_phase2_trim(self, result, ignoremissing=False):
        """Generate trim percentages for a result set
        Args:
            result: dict of result parameters.  Trim% is stored
                in the "TRIMPERCENT" key in this dict as a float
                where 100.0% = 100.0.
            ignoremissing: fill TRIMPERCENT with "0.0" if no SKU
                is found instead of raising an exception.
        Results:
            none
        """
        try:
            brand = sysconfig.cpubrand_filter(result["CPUBRAND"])
            window = self.windows[brand][result["SOCKET"]]
        except KeyError as e:
            if ignoremissing:
                result["TRIMPERCENT"] = "0.0"
                return 
            if not e.args:
                e.args = ('',)
            e.args = e.args + ("Could not find SKU / socket entry in trim window file") 
            raise

        if result:
            eff_bin = float(result["BIN"])
            if eff_bin < window["bottom"]:
                trim_percent = (eff_bin - window["bottom"] - window["margin_bottom"]) / window["mhz_factor"] 
            elif eff_bin > window["top"]:
                trim_percent = (eff_bin - window["top"] + window["margin_top"]) / window["mhz_factor"]
            else:
                trim_percent = 0.0
            if(trim_percent < window["clamp_low"]):
                trim_percent = window["clamp_low"]
            if(trim_percent > window["clamp_high"]):
                trim_percent = window["clamp_high"]
            result["TRIMPERCENT"]=str(trim_percent)
        else:
            raise RuntimeError("No results found, can't compute trim")
    
    def get_node_list_sorted_by_processor_type(self,input_file_name):
        
        nodes_by_processor_type = {}
        header_row = None 
        num_fields = None 
        
        cname_idx = None
        cores_cpu_idx = None
        clock_speed_idx = None
        bin_idx = None
         
        if input_file_name: 
            #read in the csv
            input_file_handle = open(input_file_name, 'rb')
            if input_file_handle:
                incsv = csv.reader(input_file_handle)
                if incsv:
                    for i,row in enumerate(incsv):
                        if row[0] == "CNAME":
                            header_row = row 
                            num_fields = len(header_row)
                            
                            cname_idx = self.get_column_label_index(header_row,"CNAME") 
                            cores_cpu_idx = self.get_column_label_index(header_row,"Cores/CPU") 
                            clock_speed_idx = self.get_column_label_index(header_row,"Clock Speed(MHz)") 
                            bin_idx = self.get_column_label_index(header_row,"Bin") 
                        
                        elif len(row)==num_fields:
                            # put the row into a local dictionary data structure keyed by cores/cpu
                            processor_type_entry = (row[cname_idx],row[clock_speed_idx],row[bin_idx])
                            print "adding processor_type_entry: " + str(processor_type_entry)
                            if row[cores_cpu_idx] in nodes_by_processor_type:
                                nodes_by_processor_type[row[cores_cpu_idx]].append(processor_type_entry)
                            else: 
                                nodes_by_processor_type[row[cores_cpu_idx]] = [processor_type_entry] 
                        """ 
                        else:
                            #warning_string = "inconsistent input data, please review: " + str(row) + "\n"
                            warning_string += "len(row): " + str(len(row)) + ", num_fields: " + str(num_fields) + "\n" + "please review state of input file: " + input_file_name 
                            if self.logger: 
                                self.logger.warning(warning_string)
                            else: 
                                print warning_string
                        """ 
                return nodes_by_processor_type
            else:
                if self.logger: 
                    self.logger.error("unable to get file handle, please review state of input file: " + input_file_name)
                return None
        else:
            return None
    
    def generate_power_csv(self,input_file_name,output_file_name,exclusion_list=None,inclusion_list=None,sort_column_label=None,socket_number=0):
        #print "generate_csv: input_file_name: " + input_file_name 
        final_dict = {}
        massaged_rows = [] #the abbreviated list of log file lines
        inclusion_regex_list = []
        xtsystest_strip_regex = re.compile(r"INFO - ")
        
        #header_list = self.get_result_column_headers(self.log_file_name)
        header_list = self.get_result_column_headers(input_file_name)
        if os.path.isfile(input_file_name):
            with open (input_file_name, "r") as input_file:
                line_list=input_file.readlines()
           
            if line_list:
                #compile each string in inclusion_list into a regular expression 
                if inclusion_list:
                    for include_str in inclusion_list:
                        inclusion_regex_list.append(re.compile(include_str))
                        
                #create a csv writer
                csv_writer = csv.writer(open(output_file_name,'wb'),delimiter=',')

                for line in line_list:
                    skip_line = False
                    if exclusion_list: 
                        for exclude_str in exclusion_list:
                            if exclude_str in line:
                                skip_line = True
                                continue
                    
                    if inclusion_regex_list:
                        for inclusion_regex in inclusion_regex_list:
                            if not inclusion_regex.search(line):
                                skip_line = True
                                continue
                    
                    if not skip_line:
                        #strip out unnecessary xtsystest stuff and split by commas
                        fields = xtsystest_strip_regex.split(line,maxsplit=1)[-1].split(",")
                        
                        if len(fields) == len(header_list):
                            massaged_rows.append(fields) 
                        else:
                            print("length of fields list is different the length of headers list")

                #do sorting on desired column 
                if massaged_rows:
                    sort_column_id = None
                    if sort_column_label:
                        sort_column_id = self.get_column_label_index(header_list,sort_column_label)
                    else:
                        sort_column_id = len(header_list) - 1
                    
                    for massaged_row in massaged_rows:
                        if len(massaged_row) >= (sort_column_id + 1):
                            raw_sort_column_value = str(massaged_row[sort_column_id])
                            sort_column_value = raw_sort_column_value.strip() 
                            if sort_column_value:
                                final_dict_keys = final_dict.keys()
                                if sort_column_value in final_dict_keys:
                                    final_dict[sort_column_value].append([x.strip() for x in massaged_row])
                                else:
                                    final_dict[sort_column_value] = [[x.strip() for x in massaged_row]]

                    final_keys = final_dict.keys()
                    if final_keys:
                        final_keys.sort(key=float,reverse=1)
                        csv_writer.writerow(header_list)
                        list_of_rows = []
                        socket_index = self.get_column_label_index(header_list,"SOCKET")
                        for i,key in enumerate(final_keys):
                            list_of_rows = final_dict[key]
                            if list_of_rows:
                                for j,row in enumerate(list_of_rows):
                                    if int(row[socket_index]) == int(socket_number):
                                        csv_writer.writerow(row)
    
    def generate_csv(self,input_file_name,output_file_name,exclusion_list=None,inclusion_list=None,sort_column_label=None):
        #print "generate_csv: input_file_name: " + input_file_name 
        final_dict = {}
        final_iteration = 0 
        massaged_rows = [] #the abbreviated list of log file lines
        inclusion_regex_list = []
        header_list = [] 
        if os.path.isfile(input_file_name):
            with open (input_file_name, "r") as input_file:
                line_list=input_file.readlines()
           
            if line_list:
                #compile each string in inclusion_list into a regular expression 
                if inclusion_list:
                    for include_str in inclusion_list:
                        inclusion_regex_list.append(re.compile(include_str))
                        
                #create a csv writer
                csv_writer = csv.writer(open(output_file_name,'wb'),delimiter=',')

                for line in line_list:
                    skip_line = False
                    if exclusion_list: 
                        for exclude_str in exclusion_list:
                            if exclude_str in line:
                                skip_line = True
                                continue
                    
                    if inclusion_regex_list:
                        for inclusion_regex in inclusion_regex_list:
                            if not inclusion_regex.search(line):
                                skip_line = True
                                continue
                    
                    if not skip_line:
                        fields = line.split(",")
                        
                        #only keep lines with > 7 fields
                        if len(fields) >= 7:
                            #throw away first 2 fields
                            interesting_fields = fields[2:]
                            
                            #determine if this is the header row 
                            if self.get_column_label_index(interesting_fields,"Iteration") > 0:
                                if not header_list:
                                    header_list = [x.strip() for x in interesting_fields] 
                                    header_list[0] = "CNAME"
                                    header_list[1] = "NID"
                            else: 
                                massaged_rows.append(interesting_fields) 
                
                #do sorting on desired column 
                if massaged_rows:
                    sort_column_id = None
                    if sort_column_label:
                        sort_column_id = self.get_column_label_index(header_list,sort_column_label)
                    else:
                        sort_column_id = len(header_list) - 1
                    
                    for massaged_row in massaged_rows:
                        if len(massaged_row) >= (sort_column_id + 1):
                            raw_sort_column_value = str(massaged_row[sort_column_id])
                            sort_column_value = raw_sort_column_value.strip() 
                            if sort_column_value:
                                final_dict_keys = final_dict.keys()
                                if sort_column_value in final_dict_keys:
                                    final_dict[sort_column_value].append([x.strip() for x in massaged_row])
                                else:
                                    final_dict[sort_column_value] = [[x.strip() for x in massaged_row]]

                    csv_writer.writerow(header_list)
                    list_of_rows = []
                    final_keys = final_dict.keys()
                    if final_keys:
                        iteration_label_index = self.get_column_label_index(header_list,"Iteration")
                        final_keys.sort(reverse=1)
                        for i,key in enumerate(final_keys):
                            list_of_rows = final_dict[key]
                            if list_of_rows:
                                for j,row in enumerate(list_of_rows):
                                    current_iteration = row[iteration_label_index].strip("'")
                                    if int(current_iteration) == final_iteration: #only use data from the final iteration
                                        csv_writer.writerow(row)
    
    def get_column_label_index(self,header_list,label):
        idx = None;
        if header_list and label:
            for i,column_header in enumerate(header_list):
                if str(label) in str(column_header):
                    idx = i 
        return idx
    
    def generate_slow_node_list_csv(self,input_file_name,output_file_name,socket_number,calculated_bin_average_output_file_name=None,percentage=None,bin_average=None,processor_type=None,bin_average_offset=None,hard_trim=None):
       
        final_cname_socket_list = []
        return_cname_socket_list = []
        bin_average_output_data = {}    
        if percentage:
            percentage_value = float(percentage)
        else:
            percentage_value = 0.036
       
        print "generate_slow_node_list_csv: percentage_value set to: " + str(percentage_value)

        #get nodes by processor type
        nodes_by_processor_type = self.get_node_list_sorted_by_processor_type(input_file_name)
        print "nodes_by_processor_type: " + str(nodes_by_processor_type)
        if nodes_by_processor_type:
            for type in nodes_by_processor_type.keys():
                #calculate the average bin rate for this processor type
                current_list = nodes_by_processor_type[type]

                if bin_average: 
                    type_average = int(bin_average) 
                else: 
                    type_sum = 0
                    for (cname,peak,bin) in current_list:
                        type_sum = type_sum + float(bin)
                    type_average = type_sum/float(len(current_list))

                percentage_inverse = 1 - percentage_value
                
                if bin_average_offset:
                    bin_average_offset = 0 - int(bin_average_offset)
                    if self.logger: 
                        self.logger.info("factoring in user-supplied bin_average_offset: [" + str(bin_average_offset) + "]")
                else:
                    bin_average_offset = 0 
                
                calculated_type_cutoff_equation_string = " (( " + str(0-percentage_value) + " * " + str(peak) + " ) + ( " + str(percentage_inverse) + " * " + str(type_average) + " )) + " + str(bin_average_offset)
                if self.logger: 
                    self.logger.info("calculated type cutoff equation: " + calculated_type_cutoff_equation_string)

                #this is the main value 
                calculated_type_cutoff = ( ((0-percentage_value) * float(peak)) + (percentage_inverse * type_average ) ) + bin_average_offset 
                calculated_type_cutoff_string = "type is : " + str(type) + ", calculated_type_cutoff: " + str(calculated_type_cutoff)
                if self.logger: 
                    self.logger.info(calculated_type_cutoff_string)
                
                if hard_trim:
                    type_cutoff = 0 - int(hard_trim)
                    type_cutoff_string = "type is : " + str(type) + ", hard_trim type_cutoff: " + str(type_cutoff)
                    if self.logger: 
                        self.logger.info(type_cutoff_string)
                else:
                    type_cutoff = calculated_type_cutoff 
                
                #need to store type_cutoff somewheres for future reference
                type_data = {}
                type_data["type_cutoff_value"] = type_cutoff
                type_data["calculated_type_cutoff_equation"] = calculated_type_cutoff_equation_string
                type_data["calculated_type_cutoff_value"] = calculated_type_cutoff
                bin_average_output_data[type] = type_data 
            	
		        #compare and push slow nodes onto final_cname_socket_list 
                for i,(cname,peak,bin) in enumerate(current_list):
                    current_bin = float(bin)
                    if current_bin <= type_cutoff:
                        cname_sock_tuple = (cname,socket_number,type)
                        comparison_info = "current_bin: " + str(current_bin) + " <= " + str(type_cutoff) +  " adding tuple to list: " + str(cname_sock_tuple)
                        if self.logger: 
                            self.logger.info(comparison_info)
                        else:
                            print comparison_info
                        final_cname_socket_list.append(cname_sock_tuple)
                    else:
                        comparison_info = "current_bin: " + str(current_bin) + " is greater than cutoff: " + str(type_cutoff)
                        if self.logger:
                            self.logger.info(comparison_info)
                        else:
                            print comparison_info
    
            if calculated_bin_average_output_file_name:
                bin_average_file_handle = open(calculated_bin_average_output_file_name,'wb')
                if bin_average_file_handle:
                    bin_average_file_handle.write(sysconfig.dump_data(bin_average_output_data))
 
            csv_writer2 = None 
	    if output_file_name: 
                csv_writer2 = csv.writer(open(output_file_name,'wb'),delimiter=',')
            if final_cname_socket_list: 
                #create a csv writer
                for (cname,socket_number,type) in final_cname_socket_list:
                    if csv_writer2:
                        csv_writer2.writerow((cname,socket_number))
                    if processor_type and type == processor_type:
                        return_cname_socket_list.append((cname,socket_number))
            else:
                if self.logger:
                    self.logger.info("no slow nodes found")
                if csv_writer2: 
                    csv_writer2.writerow("no slow nodes found")
            
            if processor_type:
                return return_cname_socket_list
            else:
                return False
        else:
            return False 
    
    def calculate_socket_average_cutoff(self,input_file_names):
        if input_file_names:
            cutoff_average_raw_data = [] 
            type_related_data = {} 
            average_cutoffs_by_type = {} 

            #read in each set of values 
            for input_file_name in input_file_names:
                json_data = open(input_file_name)
                if json_data:
                    data = json.load(json_data)
                    if data:
                        cutoff_average_raw_data.append(data)
                    json_data.close()
            
            if cutoff_average_raw_data:
                for socket_data in cutoff_average_raw_data:
                    keys = socket_data.keys()
                    for key in keys:
                        type_dict = socket_data[key]
                        if type_dict:
                            if key in type_related_data:
                                type_related_data[key].append(type_dict["calculated_type_cutoff_value"])
                            else:
                                type_related_data[key] = [type_dict["calculated_type_cutoff_value"]]
            
            if type_related_data:
                keys = type_related_data.keys()
                for key in keys:
                    cutoff_list = type_related_data[key]
                    if cutoff_list and len(cutoff_list) == 2:
                        #average the two values, push average onto list 
                        #print "found two values for type: " + key + ", values : " + str(type_related_data[key])
                        average_cutoff = (cutoff_list[0] + cutoff_list[1])/2
                        if key in average_cutoffs_by_type:
                            print "oops, found duplicate key for type: " + key
                        else:
                            print "setting average_cutoff for key " + str(key) + " to " + str(average_cutoff)
                            average_cutoffs_by_type[key] = average_cutoff
                    else:
                        print "incorrect number of values for type: " + key + ", values : " + str(type_related_data[key]) 

            return average_cutoffs_by_type

        else:
            return -1
    
    def generate_slow_nodes_using_socket_average(self,cutoff_input_filename_list,results_output_filename_list,slow_nodes_output_filename):
        all_slow_nodes_list = []
        if cutoff_input_filename_list and results_output_filename_list:
            average_cutoffs_by_type = self.calculate_socket_average_cutoff(cutoff_input_filename_list)
            if average_cutoffs_by_type:
                keys = average_cutoffs_by_type.keys()
                for i in range(0,2):
                    results_output_filename = results_output_filename_list[i] 
                    #get nodes by processor type
                    if results_output_filename:
                        nodes_by_processor_type = self.get_node_list_sorted_by_processor_type(results_output_filename)
                        if nodes_by_processor_type:
                            for key in keys:
                                type_cutoff = average_cutoffs_by_type[key] 
                                if type_cutoff:
                                    current_list = nodes_by_processor_type[key]
                                    if current_list:
                                        for node_entry in current_list:
                                            if float(node_entry[len(node_entry)-1]) <= float(type_cutoff):
                                                log_entry = "slow node (using averaged cutoff): " + str(node_entry[0]).replace("-","_") + ": " + str(node_entry[len(node_entry)-1]) + " <= " + str(type_cutoff)
                                                if self.logger:
                                                    self.logger.info(log_entry)
                                                else:
                                                    print log_entry
                                                all_slow_nodes_list.append((node_entry[0],i))
                                            else:
                                                log_entry = str(node_entry[0]).replace("-","_") + ": " + str(node_entry[len(node_entry)-1]) + " >= " + str(type_cutoff)
                                                if self.logger:
                                                    self.logger.info(log_entry)
                                                else:
                                                    print log_entry
                if all_slow_nodes_list:
                    #create a csv writer
                    csv_writer = csv.writer(open(slow_nodes_output_filename,'wb'),delimiter=',')
                    if csv_writer: 
                        #write the list to
                        for slow_node in all_slow_nodes_list:
                            csv_writer.writerow(slow_node)
            else:
                print "call to calculate_socket_average_cutoff didn't return any data"

    def generate_xtvrmtrim_csv(self,results,output_file_name):
        """Write a CSV file based on the contents of the results list
        Args:
            results: list of result dicts
            output_file_name: file name to write CSV to
        Results:
            none
        """
        #create a csv writer
        csv_writer = csv.writer(open(output_file_name,'wb'),delimiter=',')
        for result in results:
            csv_writer.writerow((result["CNAME"], result["SOCKET"], result["TRIMPERCENT"]))

    def screen_process_results(self,trim_nodes):
        """Parse the screen results, optionally apply trim, and generate results
        Args:
            trim_nodes: True if nodes are to be trimmed after the screen, False if not
        Results:
            0 if successful, nonzero if not
        """
        status = 0

        #clean up after test and finish out logs
        self.post_run_tasks()
        #self.report()

        #generate results csv output
        margin_component = ""
        if self.margin:
            margin_component = self.margin + "_"

        results_output_filename = self.generated_results_csv_output_filename.replace("timestamp",margin_component + self.session_timestamp)
        results_object_filename = self.work_root + "/" + self.get_component_option("results_object").replace("timestamp",margin_component + self.session_timestamp)
        power_object_filename = self.work_root + "/" + self.get_component_option("power_object").replace("timestamp",margin_component + self.session_timestamp)
        smw_power_object_filename = "/tmp/" + self.get_component_option("power_object").replace("timestamp",margin_component + self.session_timestamp)

        column_headers = self.get_result_column_headers(self.log_file_name)

        results = self.read_test_results(self.log_file_name, column_headers,["Passed","passed","Failed","failure","Iterat"],[r'c[*0-9]+\-[*0-9]+c[*0-2]s[0-1]?[0-9]'])

        effective_clock_avgs = self.compute_phase2_averages(\
                [result for result in results if int(result["SOCKET"]) == 0])
        print "---averages:"
        print effective_clock_avgs

        for result in results:
            self.compute_phase2_trim(result, ignoremissing=not trim_nodes)

        self.generate_xtvrmtrim_csv(results, results_output_filename)
        if trim_nodes:
            smw_trim_filename = "/tmp/" + os.path.basename(results_output_filename)
            smw_report_filename = smw_trim_filename + ".rpt"
            local_report_filename = results_output_filename + ".rpt"

            sysconfig.transfer_trim_to_smw(self.get_component_option("destination"), results_output_filename, smw_trim_filename, self.get_component_option("first"), self.get_component_option("last"))
            sysconfig.execute_xtvrmscreen_smwhelper(self.get_component_option("destination"),self.get_component_option("smw_utils_path"),self.get_component_option("first"),self.get_component_option("last"),self.blades,smw_report_filename,trim_csv=smw_trim_filename,timestamp=self.session_timestamp,timeout=int(self.get_component_option("ssh_timeout"),0),workroot=self.work_root,post_processing=self.get_component_option('post_processing_mode'))
            sysconfig.execute_trim_apply(self.get_component_option("destination"),self.get_component_option("first"),self.get_component_option("last"), self.blades,timeout=int(self.get_component_option("ssh_timeout"),0))
            sysconfig.transfer_results_from_smw(self.get_component_option("destination"), local_report_filename, smw_report_filename, self.get_component_option("first"), self.get_component_option("last"))

            # no run-to-run state to pass this report to the next iteration,
            # so use a common symlink to refer to the last report
            os.remove(self.get_component_option('xtvrmtrim_last_report'))
            os.symlink(local_report_filename, self.get_component_option('xtvrmtrim_last_report'))

            # read trim results and attach to results
            with open(local_report_filename, 'r') as trim_report_file:
                trim_report_csv = csv.reader(trim_report_file)
                trim_report_dict = {}
                for (node, socket, trim_percent, iscale_pre, iscale_trim, limit) in trim_report_csv:
                    trim_report_dict[(node,socket)] = (iscale_pre, iscale_trim, limit)
                for result in results:
                    if (result["CNAME"],result["SOCKET"]) in trim_report_dict:
                        (result["ISCALE_PRE"], result["ISCALE_TRIM"], result["TRIM_LIMIT"]) = trim_report_dict[(result["CNAME"], result["SOCKET"])]

        # pull power and thermal data from the SMW
        # stringify the elements to be consistent with the other data
        try:
            sysconfig.get_power_and_thermal_data_from_smw(self.get_component_option('destination'),self.get_component_option('first'),self.get_component_option('last'),self.windows,self.apids,smw_power_object_filename,power_object_filename,self.get_component_option("smw_utils_path"),self.node_list,self.get_component_option('post_processing_mode'))
            with open(power_object_filename,'r') as power_object_file:
                power_results = json.loads(power_object_file.read())
                print power_results
                for result in results:
                    if result["CNAME"] in power_results:
                        if result["SOCKET"] in power_results[result["CNAME"]]:
                            for key in power_results[result["CNAME"]][result["SOCKET"]]:
                                result[key] = str(power_results[result["CNAME"]][result["SOCKET"]][key])
                    print result
        except Exception as e:
            print "couldn't get power and thermal data from smw"
            print "reason: %s" % e

        results_object_file = open(results_object_filename,"wb")
        json.dump((column_headers,results,self.windows,effective_clock_avgs), results_object_file)
        results_object_file.close()
        
        if (self.get_component_option('post_processing_mode')):
            self.convert_results_to_csv(results_object_filename,json.dumps((column_headers,results,self.windows,effective_clock_avgs)))

        status = self.get_main_return_status()
        return status
    
    def convert_results_to_csv(self,results_object_filename,json_data):
        csv_file_name = results_object_filename.replace(".json","") + ".csv"
        csv_data = open(csv_file_name, 'w')

        #with open(user_options['in_file_name']) as json_data:
        json_parsed = json.loads(json_data)
        data = json_parsed[1]
        csvwriter = csv.writer(csv_data)

        #write header
        header = json_parsed[0]
        header.append("SOCKET_TEMP_MAX")
        header.append("NODE_POWER_MAX")
        header.append("TRIMPERCENT")
        csvwriter.writerow(header)

        #parse the records for each node
        for record in data:
            result_list=[]
            for val in json_parsed[0]:
                if val in record and record[val] != None:
                    result_list.append(record[val])
                else:
                    result_list.append(" ")

            csvwriter.writerow(result_list)
        csvwriter.writerow([])

        #parse the window setting info
        count=0
        for window in json_parsed[2]:
            for socket in json_parsed[2][window]:
                if count == 0:
                    header = []
                    header.append("Processor ID")
                    header.append("socket")
                    header.extend(json_parsed[2][window][socket].keys())
                    csvwriter.writerow(header)
                    count += 1
                values = []
                values.append(window)
                values.append(socket)
                values.extend(json_parsed[2][window][socket].values())
                csvwriter.writerow(values)
        csvwriter.writerow([])

        #parse the processor stats
        for window in json_parsed[3]:
            values = []
            values.append(window)
            values.append(json_parsed[3][window])
            csvwriter.writerow(values)

        csv_data.close() 
    
    def convert_power_and_thermal_data_to_csv(self,json_data,csv_file_name):
        if json_data: 
            #create a csv writer
            csv_writer = csv.writer(open(csv_file_name,'wb'),delimiter=',')
            for key in json_data.keys():

                node_data = json_data[key]
                cname = key
                node_0_power_max = None 
                socket_0_temp_max = None 
                node_1_power_max = None 
                socket_1_temp_max = None 
                    
                if "0" in node_data and node_data["0"]:
                    if "NODE_POWER_MAX" in node_data["0"] and node_data["0"]["NODE_POWER_MAX"]:
                        node_0_power_max = int(json_data[key]["0"]["NODE_POWER_MAX"])
                        
                    if "SOCKET_TEMP_MAX" in node_data["0"] and node_data["0"]["SOCKET_TEMP_MAX"]:
                        socket_0_temp_max = float(json_data[key]["0"]["SOCKET_TEMP_MAX"])
                    
                if "1" in node_data and node_data["1"]:
                    if "NODE_POWER_MAX" in node_data["1"] and node_data["1"]["NODE_POWER_MAX"]:
                        node_1_power_max = int(json_data[key]["1"]["NODE_POWER_MAX"])
                        
                    if "SOCKET_TEMP_MAX" in node_data["1"] and node_data["1"]["SOCKET_TEMP_MAX"]:
                        socket_1_temp_max = float(json_data[key]["1"]["SOCKET_TEMP_MAX"])
                    
                csv_writer.writerow([cname,node_0_power_max,socket_0_temp_max,node_1_power_max,socket_1_temp_max])
                        
    
         
    def get_power_and_thermal_outliers(self,json_data_file,node_power_max,socket_temp_max):
        outliers = {} 
        if os.path.exists(json_data_file):
            node_power_max = int(node_power_max)
            socket_temp_max = float(socket_temp_max)
            with open(json_data_file) as json_data:
                d = json.load(json_data)
                for key in d.keys():
                    
                    outlier_0_power = False
                    outlier_0_temp = False
                    outlier_1_power = False
                    outlier_1_temp = False

                    node_data = d[key]
                    if "0" in node_data and node_data["0"]:
                        if "NODE_POWER_MAX" in node_data["0"] and node_data["0"]["NODE_POWER_MAX"]:
                            node_0_power_max = int(d[key]["0"]["NODE_POWER_MAX"])
                            outlier_0_power = (node_0_power_max >= node_power_max)
                        
                        if "SOCKET_TEMP_MAX" in node_data["0"] and node_data["0"]["SOCKET_TEMP_MAX"]:
                            socket_0_temp_max = float(d[key]["0"]["SOCKET_TEMP_MAX"])
                            outlier_0_temp = (socket_0_temp_max >= socket_temp_max)
                    
                    if "1" in node_data and node_data["1"]:
                        if "NODE_POWER_MAX" in node_data["1"] and node_data["1"]["NODE_POWER_MAX"]:
                            node_1_power_max = int(d[key]["1"]["NODE_POWER_MAX"])
                            outlier_1_power = (node_1_power_max >= node_power_max)
                        
                        if "SOCKET_TEMP_MAX" in node_data["1"] and node_data["1"]["SOCKET_TEMP_MAX"]:
                            socket_1_temp_max = float(d[key]["1"]["SOCKET_TEMP_MAX"])
                            outlier_1_temp = (socket_1_temp_max >= socket_temp_max)
                    
                    if outlier_0_power or outlier_0_temp or outlier_1_power or outlier_1_temp:
                        outliers[key] = node_data
                
                self.convert_power_and_thermal_data_to_csv(outliers,json_data_file.replace(".json","_outliers.csv"))        
                self.convert_power_and_thermal_data_to_csv(d,json_data_file.replace(".json",".csv"))        
                    
        return outliers


def main(test_options=None):
    status = 0
    test = XTVrmScreen()
    if test is not None:
        if not test_options:
            test.process_commandline_options()
        if test.initialize(test_options):
            print "test failed: unable to initialize"
        else:
            validation_errors = test.validate_setup()
            if not validation_errors:
                return_value = test.run()
                if return_value:
                    test.logger.error("main: run method returned non-zero")
                test.post_run_tasks()
                #test.report()
                status = test.get_main_return_status()
            else:
                test.logger.error("main: test failed due to validation errors")
                test.logger.error(validation_errors)
    return status

def test_compute_phase_2_trim(test_options=None):
    #def compute_phase2_trim(self, result, window, mhz_per_percent_trim, clamp_low, clamp_high):
    test = XTVrmScreen()
    # test bin corners
    window = { "top": -390, "bottom": -430, "margin_bottom": 15, "margin_top": 0 }
    result = { "BIN": "-800" }
    test.compute_phase2_trim(result, window, 12.0, -12.0, 8.0)
    if not result["TRIMPERCENT"] == "-12.0":
        print "Low bin clip test fail"
        return False
    result = { "BIN": "-200" }
    test.compute_phase2_trim(result, window, 12.0, -12.0, 8.0)
    if not result["TRIMPERCENT"] == "8.0":
        print "High bin clip test fail"
        return False
    result = { "BIN": "-431" }
    test.compute_phase2_trim(result, window, 12.0, -12.0, 8.0)
    if not float(result["TRIMPERCENT"]) < 0.0:
        print "Low bin edge test fail"
        return False
    result = { "BIN": "-389" }
    test.compute_phase2_trim(result, window, 12.0, -12.0, 8.0)
    if not float(result["TRIMPERCENT"]) > 0.0:
        print "High bin edge test fail"
        return False
    result = { "BIN": "-400" }
    test.compute_phase2_trim(result, window, 12.0, -12.0, 8.0)
    if not float(result["TRIMPERCENT"]) == 0.0:
        print "Inside bin test fail"
        return False
    return True


def test_get_test_script_parameters():
    test = XTVrmScreen()
    node_list_string = "128-131" 
    job_label = "56"
    num_PEs = "1"
    print test.get_test_script_parameters(1,node_list_string,num_PEs,job_label)

def test_generate_csv(test_options=None):
    print "executing test_generate_csv"
    #print "test_options: " + str(test_options)
    if test_options:
        test = XTVrmScreen()
        test.generate_power_csv(test_options["input_file_name"],test_options["output_file_name"],test_options["pattern_exclusion_list"],test_options["pattern_inclusion_list"],test_options["sort_column_label"],test_options["socket_number"])
        
def test_generate_slow_nodes_csv(test_options=None):
    print "executing test_generate_slow_nodes_csv"
    #print "test_options: " + str(test_options)
    if test_options:
        test = XTVrmScreen()
        test.generate_slow_node_list_csv(test_options["generated_results_csv_output_filename"],test_options["generated_slow_nodes_csv_file_name"],test_options["socket_number"],test_options["bin_average_output_file_name"],test_options["cutoff_percentage"],test_options["system_bin_average"])
               
def test_calculate_socket_average_cutoff(test_options=None):
    print "executing test_calculate_socket_average_cutoff"
    #print "test_options: " + str(test_options)
    if test_options:
        test = XTVrmScreen()
        test.calculate_socket_average_cutoff(test_options)

def test_generate_slow_nodes_using_socket_average(test_options=None):
    print "executing test_generate_slow_nodes_using_socket_average"
    #print "test_options: " + str(test_options)
    if test_options:
        test = XTVrmScreen()
        test.generate_slow_nodes_using_socket_average(test_options["cutoff_input_filenames_list"],test_options["results_input_filenames_list"],test_options["slow_nodes_output_filename"])

if __name__ == "__main__":
    #    main()

    log_dir = "/home/users/phalseth"
    timestamp = "20150522155700"
    socket_number = "0"
    
    #test results csv generator 
    test_options = {}
    test_options["input_file_name"] = log_dir + "/workload_test_suite/xtvrm_socket" + socket_number + "_test/xtvrm_socket" + socket_number + "_test_" + timestamp + ".log"
    test_options["output_file_name"] = log_dir + "/workload_test_suite/xtvrm_socket" + socket_number + "_test/xtvrm_socket" + socket_number + "_results_debug_" + timestamp + ".csv"
    test_options["pattern_exclusion_list"] = ["Passed","passed","Failed","failure"]
    test_options["pattern_inclusion_list"] = [r'c[0-9]-[0-9]c[0-9]s[0-9]']
    test_options["sort_column_label"] = "Bin" 
    #test_generate_csv(test_options)
    
    #test watts csv generator 
    test2_options = {}
    test2_options["input_file_name"] = log_dir + "/workload_test_suite/xtvrm_socket" + socket_number + "_test/xtvrm_socket" + socket_number + "_test_" + timestamp + ".log"
    test2_options["output_file_name"] = log_dir + "/workload_test_suite/xtvrm_socket" + socket_number + "_test/xtvrm_socket" + socket_number + "_watts_debug_" + timestamp + ".csv"
    test2_options["pattern_exclusion_list"] = ["Passed","passed","Failed","failure"]
    test2_options["pattern_inclusion_list"] = [r'c[0-9]-[0-9]c[0-9]s[0-9]']
    test2_options["sort_column_index"] = 5 
    #test_generate_csv(test2_options)

    #test slow nodes csv generator 
    slow_nodes_options = {}
    slow_nodes_options["generated_results_csv_output_filename"] = test_options["output_file_name"]
    slow_nodes_options["generated_slow_nodes_csv_file_name"] = log_dir + "/workload_test_suite/xtvrm_socket" + socket_number + "_test/xtvrm_socket" + socket_number + "_slow_nodes_debug_" + timestamp + ".csv"
    slow_nodes_options["socket_number"] = socket_number
    slow_nodes_options["bin_average_output_file_name"] = log_dir + "/workload_test_suite/xtvrm_socket" + socket_number + "_test/xtvrm_socket" + socket_number + "_bin_average_debug_" + timestamp + ".json"
    slow_nodes_options["cutoff_percentage"] = None 
    slow_nodes_options["system_bin_average"] = None 
    test_generate_slow_nodes_csv(slow_nodes_options)
   
    
    socket0_bin_average_output_file_name = log_dir + "/workload_test_suite/xtvrm_socket0_test/xtvrm_socket0_system_bin_average_" + timestamp + ".json"
    socket1_bin_average_output_file_name = log_dir + "/workload_test_suite/xtvrm_socket1_test/xtvrm_socket1_system_bin_average_" + timestamp + ".json"
    #test_calculate_socket_average_cutoff([socket0_bin_average_output_file_name,socket1_bin_average_output_file_name])
    
    socket0_results_output_file_name = log_dir + "/workload_test_suite/xtvrm_socket0_test/xtvrm_socket0_results_" + timestamp + ".csv"
    socket1_results_output_file_name = log_dir + "/workload_test_suite/xtvrm_socket1_test/xtvrm_socket1_results_" + timestamp + ".csv"
    average_test_options = {}
    average_test_options["cutoff_input_filenames_list"] = [socket0_bin_average_output_file_name,socket1_bin_average_output_file_name]
    average_test_options["results_input_filenames_list"] = [socket0_results_output_file_name,socket1_results_output_file_name]
    average_test_options["slow_nodes_output_filename"] = log_dir + "/workload_test_suite/xtvrm_screen_slow_nodes_using_socket_average_cutoff_" + timestamp + ".csv"  
    #test_generate_slow_nodes_using_socket_average(average_test_options)

# vim: set expandtab tabstop=4 shiftwidth=4:
