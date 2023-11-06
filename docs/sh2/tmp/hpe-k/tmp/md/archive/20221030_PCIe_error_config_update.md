- Operating system ISO: rhel-8.6-x86_64-dvd.iso
- `uname -a`: 4.18.0-372.32.1.el8_6.x86_64

- `dnf update && dnf upgrade`
- `dnf install gcc tcsh tk tcl gcc-gfortran rpm-build kernel-rpm-macros patch python3-devel libtool createrepo perl lsof wget pciutils-devel`
- `dnf install openmpi`
- `dnf update && dnf upgrade`
- `dnf install mpitests-openmpi.x86_64`
- `dnf update && dnf upgrade`
- `dnf provides */mpicc`

```bash
export PATH=/usr/lib64/openmpi/bin/:$PATH
export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib:$LD_LIBRARY_PATH:
```

- `dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm`
- `yum config-manager --add-repo http://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo`
- `dnf install --enablerepo=epel dkms`
- `dnf install "kernel-devel-uname-r == $(uname -r)"`
- `dnf install kernel-devel`
- `dnf update && dnf upgrade`
- `dnf install cuda`
- `dnf update && dnf upgrade`
- `dnf install opensm`
- `dnf install infiniband-diags`
- [MLNX_OFED v5.7-1.0.2.0](https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/)
- `dnf install kernel-devel-4.18.0-372.26.1.el8_6.x86_64`
- `./mlnxofedinstall --force --with-nfsrdma --enable-gds --add-kernel-support`

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

- [subnet manager back-to-back](https://docs.netapp.com/us-en/e-series/config-linux/nvme-ib-configure-subnet-manager-task.html)
