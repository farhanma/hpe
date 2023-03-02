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
#SBATCH --account=v1003
#SBATCH --reservation=rt29677

export OMP_NUM_THREADS=32
export KMP_AFFINITY=nowarnings,scatter,1,0,granularity=fine

./xlinpack_xeon64 lininput_xeon64
