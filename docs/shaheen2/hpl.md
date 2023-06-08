---
title: HPL
---

High Performance LINPACK (HPL) is a high performance implementation of the
LINear Algebra PACKage (LINPACK) benchmarks to measure the computing power of
a system's floating-point.

```math title="Theoretical GFLOPS equation"
GFLOPS = GHz x num_cores x num_IPC x num_sockets x num_nodes
```

```math title="Theoretical GFLOPS of the Shaheen II Intel Haswell compute node"
1177.60 GFLOPS = 2.30 GHz x 16 cores x 16 IPC x 2 sockets x 1 node
```

The sustained LINPACK performance of the Shaheen II compute node between:
`935-955 GFLOPS (~80% of the 1177.60 GFLOPS)`.

Before running HPL, email incident-reply@hpc.kaust.edu.sa to create a KSL RT
ticket requesting a reservation of the compute nodes for exclusive use in SLURM.

```wiki title="Request a reservation in SLRUM on nid0[6448-6451] to run HPL"
Hi

Could you please create a reservation in SLURM on nid0[6448-6451] to run HPL?

Thanks

Mohammed
```

Shaheen II HPL binary and a sample SLURM script can be downloaded from:
https://github.com/farhanma/hpe/tree/opt/shaheen2/hpl. Use `git` to clone the
HPL binary branch in your `/scratch` home directory:
`git clone --single-branch --branch opt https://github.com/farhanma/hpe.git`.
