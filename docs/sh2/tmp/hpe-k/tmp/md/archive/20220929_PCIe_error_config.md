### KAUST work
### Uncorrectable PCI Express Error Detected

--------------------------------------------------------------------------------
### Mellanox logs

```sh
reboot

sysinfo-snapshot.py

while true; do date; /home/admin/bin/ib_write_bw -p 1080 -a -b -F -d mlx5_0 --report_gbits -i 1 --use_cuda=2 2>&1 & ssh gpu202-16-r /home/admin/bin/ib_write_bw -p 1080 -a -b -F -d mlx5_0 --report_gbits -i 1 --use_cuda=2 gpu202-16-l; done | tee listen_write_bw-while.log.`date +"%Y%m%d"`

sysinfo-snapshot.py

while true; do date; /home/admin/bin/ib_write_bw -p 1080 -a -b -F -d mlx5_0 --report_gbits -i 1 2>&1 & ssh gpu202-16-r /home/admin/bin/ib_write_bw -p 1080 -a -b -F -d mlx5_0 --report_gbits -i 1 gpu202-16-l; done | tee listen_write_bw-while.log.`date +"%Y%m%d"`

sysinfo-snapshot.py

while true; do date; /home/admin/bin/ib_write_bw -p 1080 -a -F -d mlx5_0 --report_gbits -i 1 2>&1 & ssh gpu202-16-r /home/admin/bin/ib_write_bw -p 1080 -a -F -d mlx5_0 --report_gbits -i 1 gpu202-16-l; done | tee listen_write_bw-while.log.`date +"%Y%m%d"`

sysinfo-snapshot.py
```

--------------------------------------------------------------------------------

```sh
dnf update && dnf upgrade

dnf install gcc tcsh tk tcl gcc-gfortran rpm-build kernel-rpm-macros patch python3-devel libtool createrepo perl lsof wget pciutils-devel

dnf update && dnf upgrade

dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
yum config-manager --add-repo http://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
dnf install --enablerepo=epel dkms
dnf install "kernel-devel-uname-r == $(uname -r)"
dnf install kernel-devel

dnf update && dnf upgrade

dnf install cuda

sudo reboot

dnf update && dnf upgrade

[MLNX_OFED v5.7-1.0.2.0](https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/)

./mlnxofedinstall --force --with-nfsrdma --enable-gds --add-kernel-support

dracut -f
/etc/init.d/openibd restart

firewall-cmd --state
systemctl stop firewalld
systemctl disable firewalld
systemctl mask --now firewalld

nvidia-smi -pm 1

subscription-manager remove --all
subscription-manager unregister
subscription-manager clean
dnf clean all
rm -rf /var/cache/yum/*
subscription-manager register
subscription-manager attach --auto
subscription-manager list 

```

--------------------------------------------------------------------------------

- Operating System
  - Red Hat Enterprise Linux (RHEL) v8.6: rhel-8.6-x86_64-boot.iso (minimal)
  - Kernel version 4.18.0-372.26.1.el8_6.x86_64
  - Server time etc/UTC
  - Username: _admin_ and _root_
  - Password: HPE!nvent

--------------------------------------------------------------------------------

- RHEL 8.6
  - NVIDIA driver v520.61.05 and CUDA v11.8
  - `dnf update`
    - `dnf install gcc`
    - `dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm`
    - `yum config-manager --add-repo http://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo`
    - `dnf install kernel-devel`
    - `dnf install cuda`
    - `sudo reboot`
    - `dnf install createrepo`
    - `dnf install patch kernel-rpm-macros gdb-headless elfutils-libelf-devel make lsof libtool python36-devel python36 rpm-build`
    - `dnf install tcsh tk tcl gcc-gfortran`
    - `./mlnxofedinstall --force --with-nfs-rdma --enable-gds --add-kernel-support`
    - `dracut -f`
    - `/etc/init.d/openibd restart`
    - `sudo reboot`
    - `ofed_info -s`

--------------------------------------------------------------------------------

- New firmware version: 20.34.1002

--------------------------------------------------------------------------------

- Start collecting the below logs for both nodes, then save all the logs for
  each node in a separate folder:

  1. Console logs for both nodes (which already been created while the test was
     running)
  2. AHS logs (download them from the iLO)
  3. IML logs (download them from the iLO)
  4. "lspci -vvv >> lspci-vvv" (from the CLI)
  5. "nvidia-bug-report.sh" (from the CLI) (The created file will be saved in
     the current directory)
  6. "nvidia-smi -a >> nvidia-smi-a" (from the CLI)
  7. "nvidia-smi topo -m >> nvidia-smi-topo" (from the CLI)
  8. "sosreport" (from the CLI) (This command will prompt you to press ENTER or
     CTRL-C please hit ENTER and enter the case ID which is "5364273397") (The
     generated file will be saved at: /var/tmp)
    - `yum install sos`
  9. "[sysinfo-snapshot.py](https://github.com/Mellanox/linux-sysinfo-snapshot)"
    (from the CLI) (the output will be saved in /tmp)

--------------------------------------------------------------------------------

### CentOS-7-x86_64-Everything-2009.iso

- VBIOS: 92.00.36.00.01 (`nvidia-smi -q | grep BIOS`)
- CUDA: 11.4 (`/usr/local/cuda-11.4/bin/nvcc --version`)
- NV Driver: 470.57.02 (`nvidia-smi`)
- MLNX_OFED: MLNX_OFED_LINUX-5.6-2.0.9.0 (`ofed_info -s`)
- NV_PEER: nvidia-peer-memory-1.1
- Pert Test: 4.5-0.14
- Mellanox IB card firmware: 20.33.1048 (`mlxfwmanager --online -u`)

--------------------------------------------------------------------------------

- NOTE: CUDA might be installed before NVIDIA driver -- I don't know yet;
-       however, if not, then repeat the process of NVIDIA driver installation

1. Using ILO to install _CentOS-7-x86_64-Everything-2009.iso_
2. `yum update`
3. `yum install gcc`
4. `yum install epel-release`
5. `yum install --enablerepo=epel dkms`
6. `yum install "kernel-devel-uname-r == $(uname -r)"`
7. Disable the `nouveau` driver, the inbox driver
  1. `touch /etc/modprobe.d/blacklist.conf`
  2. `echo "blacklist nouveau" >> /etc/modprobe.d/blacklist.conf`
  3. `cat /etc/default/grub`
      ```bash
      GRUB_TIMEOUT=5
      GRUB_DISTRIBUTOR="$(sed 's, release .*$,,g' /etc/system-release)"
      GRUB_DEFAULT=saved
      GRUB_DISABLE_SUBMENU=true
      GRUB_TERMINAL_OUTPUT="console"
      GRUB_CMDLINE_LINUX="crashkernel=auto rd.lvm.lv=centos/root rd.lvm.lv=centos/swap rhgb quiet rd.driver.blacklist=nouveau nouveau.modeset=0"
      GRUB_DISABLE_RECOVERY="true"
      ```
  4. `lsmod | grep nouveau`
8. `yum makecache`
9. `yum -y install pkgconfig`
10. `yum -y install libglvnd-devel`
11. [Nvidia driver v470.57.02](https://www.nvidia.com/Download/driverResults.aspx/178356/en-us/)
12. Query VBIOS: `nvidia-smi -q | grep BIOS` [^1]
  - `> 92.00.36.00.01` 
13. `yum install wget`
14. [CUDA v11.4](https://developer.nvidia.com/cuda-11-4-1-download-archive?target_os=Linux&target_arch=x86_64&Distribution=CentOS&target_version=7&target_type=rpm_local)
15. [MLNX_OFED v5.6-2.0.9.0](https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/)
16. `yum install createrepo`
17. `yum install kernel-devel-3.10.0-1160.76.1.el7.x86_64 python-devel pciutils redhat-rpm-config rpm-build lsof patch libtool`
18. `yum install tcl gcc-gfortran fuse-libs tcsh tk`
19. `depmod -a`
20. `./mlnxofedinstall --force --with-nfs-rdma --enable-gds --add-kernel-support`
21. `dracut -f`
22. `/etc/init.d/openibd restart`
23. [Mellanox IB card firmware v20.33.1048](https://support.hpe.com/connect/s/softwaredetails?softwareId=MTX_752385de6032475384977be454&language=en_US&tab=Installation+Instructions)
24. `ofed_info -s`
25. `mlxfwmanager --online -u`
26. `yum install pciutils-devel`
27. [nvidia-peer-memory-1.1](network.nvidia.com/products/GPUDirect-RDMA)
28. [perftest v4.5-0.14](github.com/linux-rdma/perftest/releases)
29. Disable AMD VT and ACS (Access Control Service)
  1. ILO
  2. Reboot
  3. F9
  4. System Utilities > System Configuration > BIOS/Platform Configuration (RBSU) > Virtualization Options > Access Control Service
  4. System Utilities > System Configuration > BIOS/Platform Configuration (RBSU) > Virtualization Options > AMD I/O Virtualization Technology

--------------------------------------------------------------------------------

[^1]: To avoid slowness: `nvidia-persistenced --user <username>`

--------------------------------------------------------------------------------

### CentOS-7-x86_64-Everything-2009.iso

- GPU: NVIDIA A100-SXM4-80GB
- VBIOS: 92.00.36.00.01
- OS: Cent OS 7.9
- CUDA: 11.4 and 11.5
- NV Driver: 470.57.02 and 495.29.05
- MLNX_OFED: MLNX_OFED_LINUX-5.1-2.5.8.0 (OFED-5.1-2.5.8) and MOFED:5.6-2.0.9.0
- NV_PEER: nvidia-peer-memory-1.1
- IB-RDMA Perf Test: Under /root folder
- Pert Test: 4.5-0.14
- Mellanox IB card firmware: 20.32.1010 and 20.33.1048
- MOFED:5.6-2.0.9.0
- ACS: Disabled
- AMD VT: Disabled
- NPS: 4
- System Rom: A48 v2.56 (02/10/2022)
- ILO5:2.70 May 16 2022

--------------------------------------------------------------------------------

- Nodes used:
  - gpu202-16-l (Server)
  - gpu202-16-r (Client)
- On "gpu202-16-l" (Server):
```bash
while true; do date; ib_write_bw -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 --use_cuda=2 2>&1 & ssh gpu202-16-r ib_write_bw -p 1080 -a -b -F -d mlx5_1 --report_gbits -i 1 --use_cuda=2 gpu202-16-l; done | tee listen_write_bw-while.log.`date +"%Y%m%d"`
```

```bash
while true; do date; ib_write_bw -p 1080 -b -F -d mlx5_1 --report_gbits  -i 1 --use_cuda=2 -s 65536 -D 30  2>&1 & ssh gpu202-16-r ib_write_bw -p 1080 -b -F -d mlx5_1 --report_gbits -i 1 --use_cuda=2 -s 65536 -D 30 gpu202-16-l; done | tee listen_write_bw-while.log.20220928
```

```bash
firewall-cmd --state
systemctl stop firewalld
systemctl disable firewalld
systemctl mask --now firewalld
```

`nvidia-smi -pm 1`

--------------------------------------------------------------------------------

### If test fails then capture below logs immediately after failure

- AHS
- console logs
- sysinfo using below latest sysinfo-snapshot

https://github.com/Mellanox/linux-sysinfo-snapshot/releases

--------------------------------------------------------------------------------

- Network configuration: `nmtui` set `ONBOOT=yes`
- https://www.nvidia.com/Download/driverResults.aspx/178356/en-us/
- https://www.nvidia.com/Download/driverResults.aspx/190713/en-us/
- https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html#centos7
- https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/
- https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/HGX/a100-80gb-hgx-a100-datasheet-us-nvidia-1485640-r6-web.pdf
- https://docs.oracle.com/cd/E19932-01/820-3523-10/ea_chpt5_firmware.html

