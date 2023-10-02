```sh
while true; do date; /home/farhanma/perftest-23.04.0/ib_write_bw -p 1080 -b -a -F -d mlx5_0 --report_gbits -i 1 --use_cuda=3 2>&1 & ssh gpu202-16-r /home/farhanma/perftest-23.04.0/ib_write_bw -p 1080 -b -a -F -d mlx5_0 --report_gbits -i 1 --use_cuda=3 gpu202-16-l; done | tee perftest_b_d00_cuda33.log.`date +"%Y%m%d-%H%M%S"`

yum install pciutils-devel

wget https://github.com/linux-rdma/perftest/releases/download/23.04.0-0.23/perftest-23.04.0-0.23.g63e250f.tar.gz

./autogen.sh && ./configure CUDA_H_PATH=/sw/csgv/cuda/11.5.2/el7.9_binary/include/cuda.h && make -j
```

`url -k -u admin:1dr@gon1 -s https://gpu202-16-l-mgmt/redfish/v1/Systems/1/LogServices/IML/Entries | jq | grep PCIe`

https://hewlettpackard.github.io/ilo-rest-api-docs/ilo5/#ilo-5-top-and-skip-query-options

https://hewlettpackard.github.io/ilo-rest-api-docs/ilo5/#deleting-volumes
