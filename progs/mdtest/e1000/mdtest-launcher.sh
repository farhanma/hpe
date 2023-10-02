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
