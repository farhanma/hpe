---
title: HPL
---

High Performance LINPACK (HPL) is a high performance implementation of the LINear
Algebra PACKage (LINPACK) benchmarks to measure the computing power of a system's
floating-point.

- `GFLOPS = GHz * numCores * numIPC * numSockets * numNodes`
- Shaheen II compute node is Intel Haswell Xeon Processor E5-2698 v3
    - `1.2 TFLOPS = 2.3 GHz * 16 cores * 16 IPC * 2 sockets * 1 node`
    - Sustained LINPACK performance is about `935-955 GFLOPS (~80% of the peak)`
- Request a reservation on the nodes for exclusive use in SLURM

```sh
cd /scratch/farhanma/hpe/hpl/linpack

sbatch -w nid0xxxx --reservation=rtxxxxx slurm_job.sh

# example to loop over nids to run slurm job script per node
for i in {1852..1855} {3324..3327} {6448..6451} {6512..6515} {6740..6743}
do
  sbatch -w nid0$i --reservation=rtxxxxx slurm_job.sh
done

# example 1 to grep GFLOPS from results
cat *nid* | egrep -A 1 -i 'node|Maximal|pass' | grep -e Node -e Maximal -e 55000

# example 2 to grep GFLOPS from results
for i in `ls linpack-*nid*.out`
do
  grep "NODE ID" $i | awk '{print $3}' | tr '\n' ' '
  grep -A3 "Performance Summary" $i | tail -n 1 | awk '{print $4}' | tr '\n' ' '
  echo
done
```
