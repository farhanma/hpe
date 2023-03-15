#!/bin/bash

LAUNCHER_NAME="ior-launcher-rw.sh"

if [ ! -x $LAUNCHER_NAME ]
then
   echo "LAUNCHER_NAME=$LAUNCHER_NAME doesn't exist"
   exit 1
fi

SLURM_PART='workq'
SLURM_ACCOUNT='v1003'
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

OUT_FPATH=./output.`date +"%Y%m%d-%H%M%S"`

rm -rf ${OUT_FPATH} && mkdir -p ${OUT_FPATH}

OUTFILE=${OUT_FPATH}/out-ior-${NODES}-nodes-${NODES}x${PPN}-$NP-procs-job-%J.ior

IOR_FILEPATH=${1:-/lustre2/project/v1003/farhanma/}

sbatch \
	--comment="$TEST_NAME" --cpu-freq=Performance --hint=compute_bound \
	-d singleton --exclusive -J "ior_pj" -m block  --nodes=$NODES \
	--ntasks-per-node=$PPN -p $SLURM_PART $SLURM_RES_ARG --wait-all-nodes=1 \
	--time=01:00:01 $SLURM_ACC_ARG -o $OUTFILE ./$LAUNCHER_NAME ${IOR_FILEPATH}
