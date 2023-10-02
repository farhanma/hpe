#!/bin/bash

while true
do
  date
  ib_write_bw \
    -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 --use_cuda=2 2>&1 & \
  ssh gpu202-16-r \
  ib_write_bw \
    -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 --use_cuda=2 gpu202-16-l
done | tee listen_write_bw-while.log.`date +"%Y%m%d"`
