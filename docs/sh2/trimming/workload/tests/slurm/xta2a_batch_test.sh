#!/bin/bash
sbcast --compress=lz4 /opt/cray/diag/bin/xta2a /tmp/xta2a

srun -n $SLURM_JOB_NUM_NODES --ntasks-per-node=1 /tmp/xta2a -s 4 -r 200000 -m 512:512 -b 65536 -T 1800 -S -f 

