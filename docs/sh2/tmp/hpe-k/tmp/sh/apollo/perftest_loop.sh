#!/bin/bash

# sudo nvidia-smi -pm 1
# sudo /etc/init.d/nv_peer_mem start
# lsof -ti:1080

cpu_bind_cmd="taskset -c 0"
perftest_exe="/home/hpeadmin/bin/ib_write_bw"
perftest_opt="-p 1080 -b -a -F -d mlx5_0 --report_gbits -i 1 --use_cuda=3"

while true
do
    date
    $cpu_bind_cmd $perftest_exe $perftest_opt 2>&1 & \
    ssh 10.109.16.92 \
    $cpu_bind_cmd $perftest_exe $perftest_opt 10.109.16.91
done | tee perftest_b_d00_cuda33.log.`date +"%Y%m%d-%H%M%S"`
