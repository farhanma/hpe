#!/bin/bash
sbcast --compress=lz4 /opt/cray/diag/bin/xtfbc /tmp/xtfbc
sleep 10
LOG_FILE=$WTS_JOB_LOG
srun -n $SLURM_JOB_NUM_NODES --ntasks-per-node=1 /tmp/xtfbc -L 16 -R 1 -N 2 -l 2 -f /tmp >> $LOG_FILE 

