---
title: IOR
---

## Interleaved Or Random (IOR)

It is a parallel IO benchmark that evaluates the performance of parallel file
systems using various interfaces and access patterns. IOR uses MPI for process
synchronization. IOR processes run in parallel across several nodes in a cluster
to saturate file system IO.

## Cray Sonexion 2000

### `/lustre/scratch`

- Lustre Parallel file system
- 12 cabinets interconnected by FDR InfiniBand
    - 6 Scalable Storage Units ( SSU )/cabinet -> so, in total is 72
        - 5988 SAS disk drives ( 4 TB per disk drive ); 82 disks per SSU
- Storage capacity: ~17.2 PB
- Fine Grained Routing
- I/O Throughput: ~500 GB/s
- 144 Object Storage Servers ( OSS )
- Connected to Shaheen via 73 Lustre NETwork ( LNET ) router service nodes
- IOR benchmarks amount of data moved in a fixed time ( 60 seconds ) using 1152 nodes
- [IOR binary and a sample SLURM script](https://github.com/farhanma/hpe/tree/opt/shaheen2/ior/sonexion)

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
#   lfs df    report Lustre filesystem disk usage
#     -h      print output in a human readable format
#   grep OST:
#   wc -l     print the newline counts
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

# lfs setstripe - set striping pattern of a file or directory default
#   --stripe-size    number of bytes to store on each OST before moving to the next OST
#   -c               number  of  OSTs  to  stripe  a file over
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

# grep summary of IOR output
#   ^             regular expression special character marks the start of a line
#   $             regular expression special character marks the end   of a line
#   grep ^Max     grep any line starting with Max
echo " "
grep ^Max ${BASE}.IOR || echo " ERROR: IOR did not complete"
echo " "

# to submit IOR job to SLURM
$ sbatch ior-sonexion_slurm.sh [<number_of_seconds> <ior_dir_path>]
```

## Cray ClusterStor E1000

### `/lustre2/project`

* Lustre Parallel file system
* 3392 disks ( 16 TB each disk )
* Storage capacity: ~37 PB
* I/O Throughput: ~120 GB/s
* [IOR binary and a sample SLURM script](https://github.com/farhanma/hpe/tree/opt/shaheen2/ior/e1000)
* Running IOR on `/project` benchmarks the performance of the Cray ClusterStor E1000
* Before running IOR on `/project`, make sure a reservation already in place on 128
  nodes, mounts `/lustre2/project` ( read and write ).
* Example of a common reservation issue: `ERROR: open64("", , ) failed, (aiori-POSIX.c:440)`
  * Solution: remove the current reservation and create a new one with different set of nodes

### Useful commands

```sh
# download IOR binary and running it using SLURM
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/ior/e1000
$ cat ior-e1000_slurm.sh

#!/bin/bash

LAUNCHER_NAME="ior-launcher-rw.sh"

if [ ! -x $LAUNCHER_NAME ]
then
   echo "LAUNCHER_NAME=$LAUNCHER_NAME doesn't exist"
   exit 1
fi

SLURM_PART='workq'
SLURM_ACCOUNT='v1003'

# IOR on /project must be ran on a specific reservation that mount /lustre2/project
# as read/write on the reserved nodes
SLURM_RESERVATION='rwproject2'

if [ ! -z "$SLURM_RESERVATION" ]
then
  SLURM_RES_ARG="--reservation=$SLURM_RESERVATION"
else
  unset SLURM_RES_ARG
fi

if [ ! -z "$SLURM_ACCOUNT" ]
then
  SLURM_ACC_ARG="--account=$SLURM_ACCOUNT"
else
  unset SLURM_ACC_ARG
fi

NODES=128
PPN=32
NP=$(( $NODES * $PPN ))

RESULTS_DIR=./RESULTS

if [ ! -d $RESULTS_DIR ]
then
  mkdir $RESULTS_DIR
fi

OUT_FPATH=./output.`date +"%Y%m%d-%H%M%S"`

rm -rf ${OUT_FPATH} && mkdir -p ${OUT_FPATH}

OUTFILE=${OUT_FPATH}/out-ior-${NODES}-nodes-${NODES}x${PPN}-$NP-procs-job-%J.ior

sbatch \
  --comment="$TEST_NAME" --cpu-freq=Performance --hint=compute_bound \
  -d singleton --exclusive -J "ior_pj" -m block  --nodes=$NODES \
  --ntasks-per-node=$PPN -p $SLURM_PART $SLURM_RES_ARG --wait-all-nodes=1 \
  --time=01:00:01 $SLURM_ACC_ARG -o $OUTFILE ./$LAUNCHER_NAME

$ cat ior-launcher-rw.sh

#!/bin/bash

echo "#######################################################"
echo $0 launched on `hostname` at `date`
echo "#######################################################"
echo

set | grep ^SLURM

echo "------------------------------"
echo
echo " slurm job $SLURM_JOBID at `date`"
echo "$0 launched on `hostname` $*"
echo
echo "------------------------------"

IOR_BIN=./bin/ior
if [ ! -x $IOR_BIN ]
then
  echo "ERROR: IOR_BIN=$IOR_BIN not found"
  exit 1
fi

IOR_OUT_DIR=/lustre2/project/v1003/farhanma/ior-project/ior_rw_dir

if [ ! -d $IOR_OUT_DIR ]
then
  mkdir $IOR_OUT_DIR
fi

# pointless, if mkdir failed:
if [ ! -d $IOR_OUT_DIR ]
then
  echo "ERROR: IOR_OUT_DIR=$IOR_OUT_DIR does not exist"
  exit 1
fi

pushd $IOR_OUT_DIR && rm -f $IOR_OUT_DIR/iorfile.bin*
popd

lfs setstripe -c 1 -i -1 -S 1M $IOR_OUT_DIR
lfs getstripe $IOR_OUT_DIR

#------------------------------------
# pre-create the files in a balanced way:
#------------------------------------

fs_name=`lfs getname $IOR_OUT_DIR | cut -d- -f1`
ost_count=`lfs osts $IOR_OUT_DIR| grep UUID | grep ACTIVE | wc -l`

file_count=$SLURM_NTASKS
for x in `seq 0 $(( $file_count - 1 ))`
do
  index=$(( $x % $ost_count ))
  rm -f $IOR_OUT_DIR/iorfile.bin.${x}
  ior_rank_index=`printf "%08d" $x`
  lfs setstripe -c 1 -i $index -S 1M $IOR_OUT_DIR/iorfile.bin.${ior_rank_index}
done
#------------------------------------
# end-precreate
#------------------------------------

STW_STATUS_FILE=$IOR_OUT_DIR/STW_status.file.txt
rm -f $STW_STATUS_FILE

SECONDS=0
echo "==============================================================="
echo "STARTING: Job $SLURM_JOBID on `hostname` - `date` - `date +%s` "
echo "==============================================================="

set -x

srun $IOR_BIN -v -w -k -E -k -F -C -a POSIX -D 360 --posix.odirect -i 1 -b 16g \
              -t 64m -g -k -e -o $IOR_OUT_DIR/iorfile.bin

srun $IOR_BIN -v -r -k -E -k -F -C -a POSIX -D 90 --posix.odirect -i 1 -b 2g \
              -t 64m -g -k -e -o $IOR_OUT_DIR/iorfile.bin

set +x

echo "==============================================================="
echo "FINISHED: Job $SLURM_JOBID - runtime: $SECONDS sec"
echo "==============================================================="

pushd $IOR_OUT_DIR && rm -f $IOR_OUT_DIR/iorfile.bin*

# to submit IOR job to SLURM
$ ./ior-e1000_slurm.sh
```

### MetaData Test ( MDTest )

It is an MPI-based application for evaluating the metadata performance of a file
system and has been designed to test parallel file systems. MDTest specifically
tests the peak metadata rates of storage systems under different directory
structures. MDTest processes run in parallel across several nodes in a cluster
to saturate file system IO. MDTest creates directory trees of arbitrary depth
and can be directed to create a mixture of workloads.

MDTest binary and a sample SLURM script can be downloaded from:
https://github.com/farhanma/hpe-docs/tree/opt/mdtest

### Useful commands

```sh
# download IOR binary and running it using SLURM
$ cd /scratch/<username>
$ git clone --single-branch --branch opt https://github.com/farhanma/hpe.git
$ cd /scratch/farhanma/hpe/shaheen2/mdtest/e1000
$ cat mdtest-e1000_slurm.sh

#!/bin/bash

#!/bin/bash

SLURM_PART="slurm"

TEST_NAME="mdt"

LAUNCHER_NAME="mdtest-launcher.sh"

if [ ! -x $LAUNCHER_NAME ]
then
   if [ -e $LAUNCHER_NAME ]
   then
     echo "LAUNCHER_NAME=$LAUNCHER_NAME exists, but is NOT executable"
     exit 1
   else
     echo "LAUNCHER_NAME=$LAUNCHER_NAME does not exist"
     exit 1
   fi
fi

SLURM_PART='workq'
SLURM_ACCOUNT='v1003'

# MDTest on /project must be ran on a specific reservation that mount /lustre2/project
# as read/write on the reserved nodes
SLURM_RESERVATION='rwproject2'

if [ ! -z "$SLURM_RESERVATION" ]
then
  SLURM_RES_ARG="--reservation=$SLURM_RESERVATION"
else
  unset SLURM_RES_ARG
fi

if [ ! -z "$SLURM_ACCOUNT" ]
then
  SLURM_ACC_ARG="--account=$SLURM_ACCOUNT"
else
  unset SLURM_ACC_ARG
fi

NODES=64 #128
PPN=32
NP=$(( $NODES * $PPN ))

OUT_FPATH=./output.`date +"%Y%m%d-%H%M%S"`

rm -rf ${OUT_FPATH} && mkdir -p ${OUT_FPATH}

OUTFILE=${OUT_FPATH}/out-mdtest-${NODES}-nodes-${NODES}x${PPN}-$NP-procs-job-%J.ior

sbatch --comment="$TEST_NAME" \
-d singleton --exclusive -J "$TEST_NAME" -m block \
--nodes=$NODES --ntasks-per-node=$PPN  -p $SLURM_PART $SLURM_RES_ARG \
--wait-all-nodes=1 --time=00:45:01 $SLURM_ACC_ARG --cpu-freq=Performance --hint=compute_bound \
-o $OUTFILE \
./$LAUNCHER_NAME

$ cat mdtest-launcher.sh

#!/bin/bash

echo =================================================
set | grep ^SLURM_
echo =================================================


MDTEST_BIN=./bin/mdtest
if  [ ! -x $MDTEST_BIN ]
then
  echo "ERROR: MDTEST_BIN=$MDTEST_BIN is not executable"
  exit 1
fi

MDTEST_DIR=/lustre2/project/v1003/farhanma/ior-project/mdtest-dir_${SLURM_JOBID}

mkdir $MDTEST_DIR

if [ ! -d $MDTEST_DIR ]
then
  echo "ERROR: MDTEST_DIR=$MDTEST_DIR can not be created"
  exit 1
fi

lfs setstripe -c 1 -i -1 -S 1M $MDTEST_DIR

lfs setdirstripe -D -c -1 -i -1 $MDTEST_DIR || ( echo "ERROR: setdirstripe default failed" ; exit 1 )

echo "--------------------------------------------------------"
echo "--DNE2 dirstripe of $MDTEST_DIR"
echo "--------------------------------------------------------"
set -x
  lfs getdirstripe $MDTEST_DIR
set +x
echo "--------------------------------------------------------"
if [ -d $MDTEST_DIR/test-dir.0-0 ]
then
  set -x
  lfs getdirstripe $MDTEST_DIR/test-dir.0-0
  set +x
fi
echo "--------------------------------------------------------"

TOTAL_FILES=$(( 1 * 1024 * 1024 ))
FILES_PER_RANK=$(( $TOTAL_FILES / $SLURM_NPROCS ))

MDTEST_ARGS="-v -p 10 -F -d $MDTEST_DIR -i 1 -n $FILES_PER_RANK -L -u"

mdtest_starttime=`date +%s`
echo "---------------------------------------------------------------------"
set -x
  srun $MDTEST_BIN $MDTEST_ARGS
set +x
mdtest_endtime=`date +%s`; mdtest_runtime=$(( $mdtest_endtime - $mdtest_starttime ))
echo "---------------------------------------------------------------------"
echo "- Job $SLURM_JOBID - mdtest took: $mdtest_runtime seconds"
echo "---------------------------------------------------------------------"

# to submit IOR job to SLURM
$ ./mdtest-e1000_slurm.sh
```
