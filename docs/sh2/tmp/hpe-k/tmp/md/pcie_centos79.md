- ens15f0
  - gpu202-16-l MAC address 68:05:ca:e1:d4:4e
  - gpu202-16-r MAC address 68:05:ca:e1:c1:38

--------------------------------------------------------------------------------

- `sudo yum update && sudo yum upgrade`
- `sudo yum install libusbx tcl gcc-gfortran fuse-libs tcsh tk yum-utils createrepo kernel-devel-3.10.0-1160.76.1.el7.x86_64 python-devel pciutils redhat-rpm-config rpm-build lsof patch libtool`
- `sudo yum update && sudo yum upgrade`
- `sudo reboot`
- `sudo yum-config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel7/x86_64/cuda-rhel7.repo`
- `sudo yum clean all`
- `sudo yum install epel-release`
- `sudo yum install ocl-icd`
- `sudo yum -y install nvidia-driver-latest-dkms`
- `sudo yum -y install cuda`
- `sudo reboot`
- `sudo yum update && sudo yum upgrade'
- [MLNX_OFED v5.7-1.0.2.0](https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/)
- `mount -o ro,loop MLNX_OFED_LINUX-5.7-1.0.2.0-rhel7.9-x86_64.iso /mnt`
- `./mlnxofedinstall --force --with-nfsrdma --enable-gds --add-kernel-support`
- `dracut -f`
- `/etc/init.d/openibd restart`
- `sudo yum clean all`
- `sudo yum update && sudo yum upgrade`

```bash
ibstat -p

vi /etc/rc.d/rc.local

# right
opensm -B -g 0x88e9a4ffff1a6e08 -p 0 -f /var/log/opensm-ib0.log
opensm -B -g 0x88e9a4ffff1a6eb0 -p 1 -f /var/log/opensm-ib1.log

# left

opensm -B -g 0x88e9a4ffff1a6ea8 -p 0 -f /var/log/opensm-ib0.log
opensm -B -g 0x88e9a4ffff4ab90c -p 1 -f /var/log/opensm-ib1.log
```

- `sudo systemctl start opensm.service`
- `sudo reboot`
- `firewall-cmd --state`
- `systemctl stop firewalld`
- `systemctl disable firewalld`
- `systemctl mask --now firewalld`
- `yum install git pciutils-devel`

### Testing plan 2022.11.02

1. Power Cycle the servers left (10.109.16.91) and right (10.109.16.92)
2. Take sysinfo snapshot and AHS logs, which will be the basline

```bash
lspci -vvv >> lspci-vvv

sudo nvidia-bug-report.sh

nvidia-smi -a >> nvidia-smi-a

nvidia-smi topo -m >> nvidia-smi-topo-m

sudo sosreport # hit ENTER and enter the case ID: 5364273397

sudo chmod 755 sosreport* 

sudo python /root/linux-sysinfo-snapshot/sysinfo-snapshot.py
```

4. Run the perftest with right (10.109.16.92) as client and left (10.109.16.91) as server and with `--use_cuda`

```bash
sudo nvidia-smi -pm 1

lsof -ti:1080 | xargs kill -9

while true; do date; /home/hpeadmin/bin/ib_write_bw -p 1080 -b -a -F -d mlx5_0 --report_gbits -i 1 --use_cuda=3 2>&1 & ssh 10.109.16.92 /home/hpeadmin/bin/ib_write_bw -p 1080 -b -a -F -d mlx5_0 --report_gbits -i 1 --use_cuda=3 10.109.16.91; done | tee perftest_b_d00_cuda33.log.`date +"%Y%m%d-%H%M%S"`
```

4. Take sysinfo snapshot, AHS logs, and terminal logs
6. Run the perftest with right as (10.109.16.92) client and left as server (10.109.16.91) and without `--use_cuda`
7. Take sysinfo snapshot, AHS logs, and terminal logs

```bash
nvidia-smi topo -m

sudo mlxlink -d 43:00.0 --port_type PCIE -c -e
sudo mlxlink -d c8:00.0 --port_type PCIE -c -e

commands_txt_output/mlxlink_mstlink.txt

dl down : [link down counter]

RX errors: indicate number of transitions to recovery due to Framing errors and CRC (dlp and tlp) errors.
TX errors: indicate number of transitions to recovery due to EIEOS and TS errors.
CRC Error dllp: indicate CRC error in Data Link Layer Packets
CRC Error tlp: indicate CRC error in Transaction Layer Packet

mlxlink -d mlx5_0 -m # will show the cable information 

mlxlink -d mlx5_0 -m | grep "Serial Number"

iblinkinfo 

```

--------------------------------------------------------------------------------

### 20221108-115000 --- action items

1. ILO: default is Optimal Cooling
    - Power & Thermal > Fans > Fan Settings > Thermal Configuration > Maximum Cooling
2. Terminal: cap HDR cable bandwidth -- mimic EDR

```bash

# HDR to EDR

sudo mlxlink -d mlx5_0 -p 1 --speeds EDR
sudo mlxlink -d mlx5_0 -p 1 --port_state TG

# EDR to HDR

sudo mlxlink -d mlx5_0 -p 1 --speeds HDR
sudo mlxlink -d mlx5_0 -p 1 --port_state TG
```

3. BIOS: cap CPU cores to 16 -- default is 64 cores
    - Power & Thermal > Fans > Fan Settings > Thermal Configuration > Maximum Cooling
4. EDR to switch
5. EDR to switch on different nodes to test the customer software setup
