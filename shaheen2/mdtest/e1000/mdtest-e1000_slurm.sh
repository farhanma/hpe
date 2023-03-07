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
