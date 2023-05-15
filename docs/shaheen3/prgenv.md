---
title: PrgEnv-intel
---

```sh title="Example of PrgEnv-intel deployment" hl_lines="9 19 30"
# Intel CPE SquashFS `cpe-intel-sles15sp4.x86_64-22.10.squashf` is added in
# `~/hpe/config/software/22.11_recipe/cpe-22.10-sles15-sp4/squashfs`
$ cd ~/hpe/config/software/22.11_recipe/cpe-22.10-sles15-sp4/
$ ./install.sh intel

# check the image directory to confirm the installation
$ ls /opt/clmgr/image/images_rw_nfs/pe/PE/22.10/*intel*

/opt/clmgr/image/images_rw_nfs/pe/PE/22.10/cpe-intel-sles15sp4.x86_64-22.10.squashfs

# on the compute nodes, we forced a redeploy of the PE manually ( this will be
# auto picked up on the boot/deployment )
$ cd /opt/clmgr/image/scripts/post-install
$ pdsh -w x3110c0s[17-18]b0n0,x8000c0s[0-7]b0n[0-3] /etc/opt/sgi/conf.d/77-deploy-pe

# confirm the redeployment
$ pdsh -w x3110c0s[17-18]b0n0,x8000c0s[0-7]b0n[0-3] df -h | grep intel

...

# note this step needs to be done on a node that mounts LUSTRE, e.g.,
# x3110c0s17b0n0
# create Intel and AMD symbolic links from LUSTRE to /opt on the compute nodes (
# this will need to go into the image too )
$ pdsh -w x3110c0s[17-18]b0n0,x8000c0s[0-7]b0n[0-3] ln -s /lustre/intel /opt/intel
$ pdsh -w x3110c0s[17-18]b0n0,x8000c0s[0-7]b0n[0-3] ln -s /lustre/AMD /opt/AMD
# confirm the output
$ pdsh -w x3110c0s[17-18]b0n0,x8000c0s[0-7]b0n[0-3] ls -l /opt/ | grep intel

...

# update the image
## KAUST image
$ cd /opt/clmgr/image/scripts/post-instal
$ chroot /opt/clmgr/image/images/kaust-compute-cos-cpe-boysenberry/
$ ln -s /lustre/intel /opt/intel
$ ln -s /lustre/AMD /opt/AMD
## SLURM image
$ chroot /opt/clmgr/image/images/kaust_slurm_cos_boysenberry_non_mountain/
$ ln -s /lustre/intel /opt/intel
$ ln -s /lustre/AMD /opt/AMD

# query SLURM image
$ cm node show -n x3110c0s[17-18]b0n0 -I
```

```sh title="Example of adding a new modulefile"
# on the login node, i.e., x3110c0s18b0n0
$ cd /etc/cray-pe.d && grep -ri /sw cray-pe*

$ vi cray-pe-configuration.csh

set mpaths = "/sw/tds108genoa/modulefiles /sw/ex108genoa/modulefiles"

$ vi cray-pe-configuration.sh

mpaths="/sw/tds108genoa/modulefiles /sw/ex108genoa/modulefiles"

# copying files from login node to compute image override section
# on the HPCM admin node
$ scp x3110c0s18b0n0:/etc/cray-pe.d/cray-pe-config* /opt/clmgr/image/overrides/kaust-compute-cos-cpe-boysenberry/etc/cray-pe.d/
# deploy the changes to all compute nodes
$ pdcp -w x8000c0s0b0n[0-3] /opt/clmgr/image/overrides/kaust-compute-cos-cpe-boysenberry/etc/cray-pe.d/cray* /etc/cray-pe.d/
```

```sh title="Example for adding aocc-compiler module file"
# on the compute node
$ rpm2cpio aocc-compiler-3.2.0.sles15-1.x86_64.rpm | cpio -idmv
$ module use /opt/cray/pe/modulefiles
$ cd /opt/AMD && craypkg-gen -m /opt/AMD/aocc-compiler-3.2.0 -o /opt/cray/
$ module switch PrgEnv-cray PrgEnv-aocc
$ cc --version

...

# Then we need to copy the newly created module file to all nodes and images
# on the HPCM admin node
$ cd /opt/clmgr/image/overrides/kaust-compute-cos-cpe-boysenberry/etc/cray-pe.d
$ scp -r x3110c0s18b0n0:/opt/cray/modulefiles/aocc/ /tmp/
$ pdcp -r -w x3110c0s17b0n0,x8000c0s0b0n[0-3] /tmp/aocc/ /opt/cray/modulefiles
$ mkdir -p opt/cray/modulefiles/
$ cp -r /tmp/aocc opt/cray/modulefiles/
$ cd /opt/clmgr/image/images/kaust_slurm_cos_boysenberry_non_mountain/
$ mkdir -p opt/cray/modulefiles/
$ cp -r /tmp/aocc opt/cray/modulefiles/
```
