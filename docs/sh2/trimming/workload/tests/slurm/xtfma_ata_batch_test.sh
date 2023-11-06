#!/bin/bash
sbcast --compress=lz4 /opt/cray/diag/bin/xtfma_ata /tmp/xtfma_ata
sleep 10
LOG_FILE=$WTS_JOB_LOG
srun -n $SLURM_JOB_NUM_NODES --ntasks-per-node=1 /tmp/xtfma_ata -R 1 -l 2 -N 1 >> $LOG_FILE 

