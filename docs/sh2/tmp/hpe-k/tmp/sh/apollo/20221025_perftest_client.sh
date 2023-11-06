#!/bin/bash

# client
while true
do
  lsof -ti:1080 | xargs kill -9
  /home/admin/bin/ib_write_bw -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 \
                              --use_cuda=3 10.109.16.91
done | tee listen_write_bw-while.client.log.`date +"%Y%m%d"`
