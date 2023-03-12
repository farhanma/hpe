#!/bin/sh
# Copyright 2017 Cray Inc. All Rights Reserved.
#
# xtnls_test.sh - This script supports running multiple NLS diagnostics with one
# aprun/srun command. It uses jinja syntax for the cpu list, time duration, & log
# level CLAs. It also uses jinja syntax for the processor type and to determine
# if this node has a gpu or not.
#
# author: Dean Balts

/opt/cray/diag/bin/xtbte_ata --cpus {{network_cpu_list}} --time {{network_time_duration}} -l {{network_log_level}} &
#get process id
bteata=$!

/opt/cray/diag/bin/{{processor_type}}/xtcpuburn --cpus {{processor_cpu_list}} --time {{processor_time_duration}} -l {{processor_log_level}} &
#get process id
cpuburn=$!

/opt/cray/diag/bin/{{processor_type}}/xtmemtester -a 50 --cpus {{memory_cpu_list}} --time {{memory_time_duration}} -l {{memory_log_level}} -M 0x1ffff &
#get process id
memtest=$!

{% if has_gpu == True %}
sleep 10
/opt/cray/diag/bin/nvidia/xkbandwidth -t range -s 64  -e 1024 -g 64 -n 0x00000001 -i 1000 --cpu {{gpu_cpu_list}} --time {{gpu_time_duration}} -v {{gpu_log_level}} -o 100
{% endif %}

if [[ -n $(ps --no-headers -p $bteata,$cpuburn,$memtest) ]]
 then
 while [[ -n $(ps --no-headers -p $bteata,$cpuburn,$memtest) ]]
 do
 sleep 10
 done
fi
