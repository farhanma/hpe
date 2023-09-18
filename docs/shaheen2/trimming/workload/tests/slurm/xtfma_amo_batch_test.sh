#!/bin/bash
sbcast --compress=lz4 /opt/cray/diag/bin/xtfma_amo /tmp/xtfma_amo
sleep 10
LOG_FILE=$WTS_JOB_LOG
srun -n $SLURM_JOB_NUM_NODES --ntasks-per-node=1 /tmp/xtfma_amo -R 1 -l 2 -N 1 -M 0 >> $LOG_FILE 
