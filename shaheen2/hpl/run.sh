#!/bin/bash

for i in {1852..1855} {3324..3327} {6448..6451} {6512..6515} {6740..6743}
do
    sbatch -w nid0$i linpack_slurm.sh
done
