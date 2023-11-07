---
title: AOCC
---

```sh title="installing AOCC 3.2.0 on the TDS"
# Parent link
#    https://www.amd.com/en/developer/aocc/aocc-archives.html
# Download link
#    https://www.amd.com/en/developer/aocc/aocc-compiler/eula.html?filename=aocc-compiler-3.2.0.sles15-1.x86_64.rpm

# on the ldap ( x3110c0s17b0n0 ) or login( x3110c0s18b0n0 ) node
$ ssh x3110c0s18b0n0
$ cd /opt/AMD

# extracting the aocc rpm Locally into the shared lustre filesystem /opt/AMD
$ rpm2cpio aocc-compiler-3.2.0.sles15-1.x86_64.rpm | cpio -idmv

# generate modulefiles
$ module use /opt/cray/pe/modulefiles
$ craypkg-gen -m /opt/AMD/aocc-compiler-3.2.0 -o /opt/cray/

# copy the modulefiles to the rest of the compute nodes
$ pdcp -r -w x3110c0s17b0n0,x8000c0s0b0n[0-3] /opt/cray/modulefiles/aocc/ /opt/cray/modulefiles

# update the image located in the HPCM admin node ( orbit33 )
$ ssh orbit33
$ cd /opt/clmgr/image/overrides/kaust-compute-cos-cpe-boysenberry/opt/cray/modulefiles/
$ scp -r x3110c0s18b0n0:/opt/cray/modulefiles/aocc/ .
```

```sh title="installing AOCC 4.0.0 on the TDS"
# Parent link
#    https://www.amd.com/en/developer/aocc.html
# Download link
#    https://www.amd.com/en/developer/aocc/aocc-compiler/eula.html?filename=aocc-compiler-4.0.0.tar

# on the ldap ( x3110c0s17b0n0 ) or login( x3110c0s18b0n0 ) node
$ ssh x3110c0s18b0n0
$ cd /opt/AMD

# extracting the aocc rpm Locally into the shared lustre filesystem /opt/AMD
$ tar xvf aocc-compiler-4.0.0.tar
$ cd aocc-compiler-4.0.0
$ ./install.sh

# generate modulefiles
$ module use /opt/cray/pe/modulefiles
$ craypkg-gen -m /opt/AMD/aocc-compiler-4.0.0 -o /opt/cray/

# copy the modulefiles to the rest of the compute nodes
$ pdcp -r -w x3110c0s17b0n0,x8000c0s0b0n[0-3] /opt/cray/modulefiles/aocc/ /opt/cray/modulefiles

# update the image located in the HPCM admin node ( orbit33 )
$ ssh orbit33
$ cd /opt/clmgr/image/overrides/kaust-compute-cpe23.02-ss2.0.1-cos.2.4/opt/cray/modulefiles/
$ scp -r x3110c0s18b0n0:/opt/cray/modulefiles/aocc/ .
```
