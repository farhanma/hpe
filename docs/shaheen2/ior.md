---
title: IOR
---

## Interleaved Or Random ( IOR )

It is a parallel IO benchmark that evaluates the performance of parallel file
systems using various interfaces and access patterns. IOR uses MPI for process
synchronization. IOR processes run in parallel across several nodes in a cluster
to saturate file system IO.

## Cray Sonexion 2000

### `/lustre/scratch`

* Lustre Parallel file system
* 5988 disks ( 4 TB per disk )
* Storage capacity: ~17.2 PB
* I/O Throughput: ~500 GB/s
* 72 Scalable Storage Units ( SSU )
* 144 Object Storage Servers ( OSS )
* Connected to Shaheen via 72 Lustre NETwork ( LNET ) router service nodes
* IOR benchmarks amount of data moved in a fixed time ( 60 seconds ) using 1152 nodes
* https://github.com/farhanma/hpe/tree/opt/shaheen2/ior/sonexion

### Useful commands

```sh
# download IOR binary and running it using SLURM
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/ior/sonexion
$ cat ior-sonexion_slurm.sh

#!/bin/bash

#SBATCH -N 1152
#SBATCH -t 0:20:00
#SBATCH -J ior-sonexion-write
#SBATCH -p workq
#SBATCH --account=v1003
#SBATCH --reservation=maintenance1

# ##############################################################################
# write to all OSTs for 1 minute ( 60 seconds ), or time requested
# usage: sbatch ior-sonexion_slurm.sh [<number_of_seconds> <ior_dir_path>]
# ##############################################################################

IOR_FILEPATH=${2:-/scratch/farhanma/hpe/shaheen2/ior/sonexion}
OUT_FILEPATH=${IOR_FILEPATH}/output.`date +"%Y%m%d-%H%M%S"`

rm -rf ${OUT_FILEPATH} && mkdir -p ${OUT_FILEPATH}

# amount of data moved in 60 seconds
IOR_SECONDS=${1:-60}
# 16 files/object storage target (OST)
FILES_PER_OST=${FILES_PER_OST:-16}
# -t 1m
TRANSFER_SIZE=${TRANSFER_SIZE:-1m}
# 2 MPIR ranks per node
RANKS_PER_NODE=${RANKS_PER_NODE:-2}
# file system to test
LUSTRE=${LUSTRE:-${IOR_FILEPATH}}
# SLURM job ID or shell's process ID
JOBID=`basename ${SLURM_JOB_ID:-$$} .sdb`
# total number of active OSTs
NOST=`lfs df -h ${LUSTRE:-.} | grep OST: | wc -l`

if (( $NOST == 0 ))
then
  echo "ERROR: must be run on a Lustre file system"
  exit
fi

# total number of ranks and files
RANKS=$(( ${FILES_PER_OST}*${NOST} ))
# base name for output files
BASE=${OUT_FILEPATH}/fixed_time_${NOST}OSTs_${FILES_PER_OST}files_${TRANSFER_SIZE}_${RANKS_PER_NODE}ppn_${JOBID}
# directory of test files
TESTDIR=${OUT_FILEPATH}/testdir.${JOBID}

rm -rf ${TESTDIR} && mkdir -p ${TESTDIR}

lfs setstripe --stripe-size 1m -c 1 ${TESTDIR}

# standard options: POSIX file per process
OPTIONS="-k -vv -C -E -F -e -g -D $IOR_SECONDS -b 300g -t ${TRANSFER_SIZE} -w"

{
  date
  echo "Running: $IOR"; echo "   with: ${OPTIONS}"
  echo "OSTs: $NOST  Ranks: $RANKS  RANKS_PER_NODE: $RANKS_PER_NODE  Nodes: $(($RANKS/$RANKS_PER_NODE))"
  if [ -e /etc/opt/cray/release/cle-release ]
  then
    echo -n CLE version: `paste /etc/opt/cray/release/cle-release | sed -e 's/DEFAULT=//'`
    echo ", " `head -1 /proc/fs/lustre/version`
  fi
  echo ""
} | tee -a ${BASE}.IOR

echo "Expected write rate is greater than 500000 MB/sec"
echo "Measured write rate for $IOR_SECONDS seconds is ..."

# run IOR for a fixed time ( 60 seconds ) using SLURM
srun --ntasks=${RANKS} \
     --ntasks-per-node=${RANKS_PER_NODE} \
     --hint=nomultithread \
     ${IOR_FILEPATH}/bin/ior \
        ${OPTIONS} -o ${TESTDIR}/IOR_file < /dev/null >> ${BASE}.IOR

# summary of IOR output
echo " "
grep ^Max ${BASE}.IOR || echo " ERROR: IOR did not complete"
echo " "

# to submit IOR job to SLURM
$ sbatch ior-sonexion_slurm.sh [<number_of_seconds> <ior_dir_path>]
```

## Cray ClusterStor E1000

### `/lustre2/project`

### Useful commands
