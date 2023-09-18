---
title: HPL
---

High Performance LINPACK (HPL) is a high performance implementation of the
LINear Algebra PACKage (LINPACK) benchmarks to measure the computing power of
a system's floating-point.

- `GFLOPS = GHz * numCores * numIPC * numSockets * numNodes`
- Shaheen II compute node is Intel Haswell Xeon Processor E5-2698 v3
    - `1177.60 GFLOPS = 2.30 GHz * 16 cores * 16 IPC * 2 sockets * 1 node`
    - Sustained LINPACK performance is between `935-955 GFLOPS (~80% of the peak)`
- Create a KSL RT ticket requesting for reservation on the nodes for exclusive
  use in SLURM
- `sbatch -w nid0xxxx linpack_slurm.sh`
