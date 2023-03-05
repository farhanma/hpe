---
title: HPL
---

## LINPACK

High Performance LINPACK ( HPL ) is a high performance implementation of the
LINear Algebra PACKage ( LINPACK ) benchmarks to measure the computing power of
a system's floating-point. Theoretically, the floating-point of a system can be
calculated as follows:

```math
GFLOPS = CPU frequency ( GHz ) x number of cores x number of instruction per cycle x number of sockets x number of nodes
```

For instance, the Intel Haswell CPU that's used in Shahenn II delivers a theoretical
peak performance of: `1.18 TFLOPS`, whereas the sustained LINPACK
performance of a compute node of Shaheen II is between:
`935-955 GFLOPS ( ~80% of the peak performance )`.

Before running HPL, [request for reservation in slurm](reservation.md) on the nodes
to be benchmarked.

Shaheen II HPL binary and a sample SLURM script can be downloaded from:
https://github.com/farhanma/hpe/tree/opt/shaheen2/hpl

## Useful commands

```sh
# downloading HPL binary and running it using SLURM
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/hpl
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
#SBATCH --account=v1003
#SBATCH --reservation=rt46392

export OMP_NUM_THREADS=32
export KMP_AFFINITY=nowarnings,scatter,1,0,granularity=fine

echo "NODE ID:" ${SLURM_JOB_NODELIST}
echo

./xlinpack_xeon64 lininput_xeon64

$ cat run.sh

for i in {1852..1855} {3324..3327} {6448..6451} {6512..6515} {6740..6743}
do
    sbatch -w nid0$i linpack_slurm.sh
done

# to run the above bash script
$ ./run.sh

# to check the status of the SLURM jobs
$ squeue -u <shaheen_username>

# helpful command to grep the performance results
$ cat *nid* | egrep -A 1 -i 'node|Maximal|pass' | grep -e Node -e Maximal -e 55000

# a sample script to extracts the GFLOPS results from multiple output files
$ cat grep_linpack_gflops.sh

#!/bin/bash

for i in `ls linpack-*nid*.out`
do
    grep "NODE ID" $i | awk '{print $3}' | tr '\n' ' '
    grep -A 3 "Performance Summary" $i | tail -n 1 | awk '{print $4}' | tr '\n' ' '
    echo
done

```
