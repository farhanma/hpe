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
