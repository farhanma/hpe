#!/bin/bash

# server
while true
do
  lsof -ti:1080 | xargs kill -9
  date
  /home/admin/bin/ib_write_bw -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 \
                              --use_cuda=3
done | tee listen_write_bw-while.server.log.`date +"%Y%m%d"`
