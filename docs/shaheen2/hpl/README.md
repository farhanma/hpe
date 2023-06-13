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
- Email [incident-reply@hpc.kaust.edu.sa](mailto:incident-reply@hpc.kaust.edu.sa)
  to create a KSL RT ticket requesting a reservation of the compute nodes for
  exclusive use in SLURM

```wiki title="Request a reservation in SLRUM on nid0[6448-6451] to run HPL"
Hi

Could you please create a reservation in SLURM on nid0[6448-6451] to run HPL?

Thanks

Mohammed
```

- Shaheen II HPL binary and a sample SLURM script can be downloaded from:
  https://github.com/farhanma/hpe/tree/opt/shaheen2/hpl. Use `git` to clone the
HPL binary branch in your `/scratch` home directory:
`git clone --single-branch --branch master https://github.com/farhanma/hpe.git`,
then `cd /scratch/farhanma/hpe/docs/shaheen2/hpl`.
