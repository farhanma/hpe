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
performance of single compute node of Shaheen II is between:
`935-955 GFLOPS ( ~80% of the peak performance )`.

Before running HPL, [request for reservation in slurm](slurm_res.md) on the nodes
to be benchmarked.

Shaheen II HPL binary and a sample SLURM script can be downloaded from:
https://github.com/farhanma/hpe-docs/tree/opt/hpl

## Useful commands

```sh
# downloading HPL binary and running it using SLURM
$ cd /scratch/<username>
$ git clone --branch opt https://github.com/farhanma/hpe_sysadmin_guide.git
$ cd hpe_sysadmin_guide/shaheen2/hpl
$ cat linpack_slurm.sh

#!/bin/bash

#SBATCH -N 1
#SBATCH -t 0:50:00
#SBATCH --output=linpack-%A_%a_%N.out
#SBATCH --err=linpack-%A_%a_%N.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --sockets-per-node=2
#SBATCH --cores-per-socket=16
#SBATCH --threads-per-core=1
#SBATCH --hint=nomultithread
#SBATCH --account=<account_name>         # e.g., v1003
#SBATCH --reservation=<reservation_name> # e.g., rt29677

export OMP_NUM_THREADS=32
export KMP_AFFINITY=nowarnings,scatter,1,0,granularity=fine

./xlinpack_xeon64 lininput_xeon64

$ cat run.sh

for i in {5100..5103} {5820..5823}
do
    sbatch -w nid0$i linpack_slurm.sh
done

# to run the above bash script
$ ./run.sh

# to check the status of the SLURM jobs
$ squeue -u <shaheen_username>

# helpful command to grep the performance results
$ cat *nid* | egrep -A 1 -i 'node|Maximal|pass' | grep -e Node -e Maximal -e 55000
```
