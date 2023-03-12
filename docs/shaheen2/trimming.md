---
title: Trimming
---

If LINPACK performance on a node does not match the minimum expected performance
( `~935 GFLOPS` ), then it needs to be trimmed by executing Cray Workload Test
Suite ( WTS )

Before start trimming, [create a KSL RT ticket requesting for reservation on the nodes to be trimmed](rt-ticket.md).

The performance of the nodes needs to be benchmarked via [HPL](#hpl.md) before
and after the trimming, for the following reasons:

  - Pre-trimming: to confirm the reported low HPL performance
  - Post-trimming: to confirm the successfulness of the trimming procedure

Report the post-trimming HPL results in email to KSL updating the RT ticket.

The trimming python script can be run from Shaheen's `gateway` nodes. The script
is installed in `/opt/cray/diag/workload/xtvrmscreen`. However, as a best practice,
it's recommended to download the most recent scripts from: https://github.com/farhanma/hpe/tree/opt/shaheen2/trimming

```sh
$ ssh gateway1
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/trimming/workload

# export SLURM environment variables to make them accessible by xtvrmscreen
$ export SLURM_RESERVATION=rt46392 # reservation in place
$ export SLURM_ACCOUNT=v1003       # HPE account on Shaheen II
$ export SLURM_PARTITION=all
$ export OMP_STACKSIZE=128M

# modify shell resource limits
#   -s unlimited    set the maximum stack size no limit
$ ulimit -s unlimited

# trimming procedures take long time, and thus it's recommended to attach it with
# a shell screen
# screen manager ( interactive shell )
#   -L               turn on output logging
#   -S <sockname>    session name ( <pid>.sockname )
#   -ls              list all of the screen sessions
#   -x               attach to a not detached screen
$ screen -L -S <sockname>
# to exit screen without termination: ctrl+A ctrl+D
$ screen -ls
# to reattach to the existing trimming screen
$ screen -x <pid>.sockname
# or you can your trimming id
$ VAR=`screen -ls | grep trimming | awk '{print $1}'` && screen -x $VAR

# run xtvrmscreen iterations
$ ./xtvrmscreen -s smw2 -c <blade_id0>,<blade_id1>,...,<blade_idn>
```

If trimming procedures fail, then you may check the hardware logs, for a possible
hardware failure, e.g., high DIMM error count, CPU issue, ... etc.

```sh
$ ssh smw2
$ logs

# /var/opt/cray/log/p0-current
$ xthwerrlog -M -i -f hwerrlog.p0-20230301t162823 -C c3-3c1s12

Node         Count     Chan  Type           DIMM   BIT(s)  Detail
-----------------------------------------------------------------------------
c3-3c1s12n0  642       0     CORRECTABLE    J4002          Read Error
c3-3c1s12n0  40671590  0     CORRECTABLE    J4002  DQ19    Memory Scrub Error
c3-3c1s12n0  2570      0     CORRECTABLE    J4002  DQ19    Read Error

Node          Socket  Count    Bank                  Type
---------------------------------------------------------------
c3-3c1s12n0   1       642      8   (HA 1)            CORRECTABLE
c3-3c1s12n0   1       19101384 13  (iMC 4)           CORRECTABLE
```
