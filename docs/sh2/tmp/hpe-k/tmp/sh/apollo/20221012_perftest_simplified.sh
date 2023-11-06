#!/bin/bash

cmd="ib_write_bw -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 --use_cuda=2"
  # -a Run sizes from 2 till 2^23
  # -b Measure bidirectional bandwidth
  # -F Do not show a warning even if cpufreq_ondemand module is loaded, and
  #    cpu-freq is not on max
  # -d Use IB device mlx5_1
  # --report_gbits Report Max/Average BW of test in Gbit/sec
  # -i Use port 1 of IB device
  # --use_cuda=2 Use CUDA specific device for GPUDirect RDMA testing

while true
do
  lsof -ti:1080 | xargs kill -9
  date
  eval $cmd 2>&1 & ssh gpu202-16-r eval $cmd gpu202-16-l
done | tee listen_write_bw-while.log.`date +"%Y%m%d"`
