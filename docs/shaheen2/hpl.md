---
title: HPL and Trimming
---

## LINPACK

High Performance LINPACK ( HPL ) is a high performance implementation of the
LINear Algebra PACKage ( LINPACK ) benchmarks to measure the computing power of
a system's floating-point. Theoretically, the floating-point of a system can be
calculated as follows:

```math
GFLOPS = CPU frequency ( GHz ) x number of cores x number of instruction per cycle x number of sockets x number of nodes
```

For instance, the Intel Haswell CPU compute node of Shahenn II delivers a
theoretical peak performance of: `1.18 TFLOPS`, whereas the sustained LINPACK
performance of a compute node of Shaheen II is between:
`935-955 GFLOPS ( ~80% of the peak performance )`.

Before running HPL, email incident-reply@hpc.kaust.edu.sa to create a KSL RT
ticket requesting for reservation on the nodes to be benchmarked. In the email,
you can either include a list of the node id ( `nid` ), e.g., `nid0[5100-5103,5820-5823]`,
or a list of the component name ( `cname` ), e.g., blade id `c6-2c1s11,c0-3c0s15`.

```sh
# convert a node id ( nid ) into the component name ( cname )
# node id to blade name
$ nid2str nid05200
    c7-2c0s4n0
    │ │ │ │ │
    │ │ │ │ └───node {0..3}
    │ │ │ └───slot {0..15}
    │ │ └───chassis {0..2}
    │ └───row {0..3}
    └───cabinet {0..9}

# useful script to handle multiple nids
$ NIDS=`scontrol show hostnames nid0[5100-5103,5820-5823]`; for nid in $NIDS; do nid2str $nid | sed 's/.\{2\}$//' ; done | sort -u
    c0-3c0s15
    c6-2c1s11

# get all nids in a blade
$ nid2blade nid05200
    nid0[5200-5203]

# convert a node string to a nid
$ str2nid c7-2c0s4n0
    nid05200
```

Shaheen II HPL binary and a sample SLURM script can be downloaded from:
https://github.com/farhanma/hpe/tree/opt/shaheen2/hpl. Use `git` to clone the
HPL binary branch in your `/scratch` home directory.

```sh
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/hpl
$ ls

    lininput_xeon64  linpack_slurm.sh  xlinpack_xeon64
    │                │                 │
    │                │                 │
    │                │                 │
    │                │                 └───HPL binary
    │                └───SLURM job script
    └───HPL input data file

$ cat linpack_slurm.sh

#!/bin/bash

#SBATCH -N 1
#SBATCH -t 0:50:00
#SBATCH -J linpack
#SBATCH --output=linpack-%A_%a_%N.out
#SBATCH --err=linpack-%A_%a_%N.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --sockets-per-node=2
#SBATCH --cores-per-socket=16
#SBATCH --threads-per-core=1
#SBATCH --hint=nomultithread
#SBATCH --account=<HPE_Shaheen_account_name>
#SBATCH --reservation=<SLURM_reservation_name_created_by_KSL>

export OMP_NUM_THREADS=32
export KMP_AFFINITY=nowarnings,scatter,1,0,granularity=fine

echo "NODE ID:" ${SLURM_JOB_NODELIST}
echo

./xlinpack_xeon64 lininput_xeon64
```

Make sure before attempting to run HPL that the SLURM state of the nodes is not in the
`DRAIN` state. If so, update the KSL RT ticket requesting the nodes to be resumed
into production. Also, do not run HPL if the SLURM state of the nodes is in the `ALLOCATED`
state, Having said that, the right SLURM state and flags, which indicate that the
list of the nodes are ready to launch the HPL SLURM job, is `IDLE+RESERVED`.

```sh
# query reservation
$ scontrol show res <reservation_id>
$ sinfo -T

# query nodes slurm state
$ scontrol show node nid0[5100-5103,5820-5823] | egrep "NodeName|State" | \
  awk '{print $1}' | paste -s -d' \n'

# check if one of the nodes are allocated for a specific job
$ squeue -w nid0[5100-5103,5820-5823]

# to loop over a list of multiple nodes that need to be benchmarked and submit
# HPL for every node
$ for i in {1852..1855} {3324..3327} {6448..6451} {6512..6515} {6740..6743}; do sbatch -w nid0$i linpack_slurm.sh; done

# to check the status of the SLURM jobs
$ squeue -u <shaheen_username>

# helpful command to grep the performance results
$ cat *nid* | egrep -A 1 -i 'node|Maximal|pass' | grep -e Node -e Maximal -e 55000

# another useful set of commands that grep the GFLOPS on every compute node
$ for i in `ls linpack-*nid*.out`; do grep "NODE ID" $i | awk '{print $3}' | tr '\n' ' '; grep -A 3 "Performance Summary" $i | tail -n 1 | awk '{print $4}' | tr '\n' ' '; echo; done
```

## Workload Test Suite ( WTS )

If LINPACK performance on a node does not match the minimum expected performance
( `~935 GFLOPS` ), then it needs to be trimmed.

As stated [above](#linpack), before start trimming, email incident-reply@hpc.kaust.edu.sa
to create a KSL RT ticket requesting for reservation on the nodes to be trimmed.
If there is an in place reservation for HPL, you can use it for trimming.

The performance of the nodes must be benchmarked via [HPL](#linpack) before and
after the trimming, for the following reasons:

  - Pre-trimming: to confirm the reported low HPL performance
  - Post-trimming: to confirm the successfulness of the trimming procedure

Report the post-trimming HPL results in email to KSL updating the RT ticket.

The trimming python script can be run from Shaheen's `gateway` nodes. The script
is installed in `/opt/cray/diag/workload/xtvrmscreen`. However, it's recommended
to download the scripts from: https://github.com/farhanma/hpe/tree/opt/shaheen2/trimming

```sh
$ ssh gateway1
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/trimming

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

# for example, /var/opt/cray/log/p0-current
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
