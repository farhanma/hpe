---
title: AMD uProf
---

- http://192.48.187.132:9965/system/wiki
- http://192.48.187.132:9965/system/wiki/Config/AMDuProf-Install
- https://www.amd.com/en/developer/uprof.html

```sh title="installation of the AMD uProf ( MICRO-prof )" hl_lines="10-14"
# login to the HPCM admin node ( orbit33 )
$ cd /opt/clmgr/image/scripts/post-install
$ cm node zypper -n x8000c0s0b0n[0-3] --repos COS-2.4.89-sles15sp4-x86_64,SLE-15-SP4-Full-x86_64 install amduprof libcap1 libcap2 libcap-devel libcap-progs

# enable user access to the low level devices the following must bet set via a
# post-install script
$ cd /opt/clmgr/image/scripts/post-install
$ cat 98all.amduprof

echo 0 > /proc/sys/kernel/nmi_watchdog
modprobe msr
chmod chmod og+rw /dev/cpu/*/msr
setcap cap_sys_rawio=ep /opt/AMD*/bin/AMDuProfPcm
```
