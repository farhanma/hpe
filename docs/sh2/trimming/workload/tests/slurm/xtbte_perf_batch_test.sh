#!/bin/bash
sbcast --compress=lz4 /opt/cray/diag/bin/xtbte_perf /tmp/xtbte_perf
sleep 10
LOG_FILE=$WTS_JOB_LOG
srun -n $SLURM_JOB_NUM_NODES --ntasks-per-node=1 /tmp/xtbte_perf -B 6 -N 2 -l 2 -S 0x7 -f /tmp >> $WTS_JOB_LOG 

