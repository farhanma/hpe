---
title: HPL
---

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

Before running HPL, [create a KSL RT ticket requesting for reservation on the nodes to be benchmarked](rt-ticket.md).
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
