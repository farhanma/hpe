#!/bin/bash

for i in {5100..5103} {5820..5823}
do
  sbatch -w nid0$i linpack_slurm.sh
done
