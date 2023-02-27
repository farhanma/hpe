---
title: Trimming
---

## Workload Test Suite ( WTS )

If LINPACK performance on a node does not match the minimum expected performance
( `~935 GFLOPS` ), then it needs to be trimmed.

Before starting the trimming procedures, [request for reservation in slurm](slurm_res.md)
on the nodes to be trimmed.

The performance of the nodes must be benchmarked via [HPL](hpl.md) before and
after the trimming, for the following reasons:

  - pre-trimming: to confirm the reported low HPL performance
  - post-trimming: to confirm the successfulness of the trimming procedure

Report the post-trimming HPL results in email to KSL updating the RT ticket.

The trimming python script is located in the Shaheen's `gateway` nodes:
`/opt/cray/diag/workload/xtvrmscreen`.

## Useful commands

```sh
$ ssh gateway1

# export SLURM environment variables to make them accessible by xtvrmscreen
$ export SLURM_RESERVATION=<reservation_name>
$ export SLURM_PARTITION=all
$ export OMP_STACKSIZE=128M
$ export SLURM_ACCOUNT=<account_name>

# modify shell resource limits
#   -s unlimited    set the maximum stack size no limit
$ ulimit -s unlimited

# screen manager ( interactive shell )
#   -L               turn on output logging
#   -S <sockname>    session name ( <pid>.sockname )
#   -ls              list all of the screen sessions
#   -x               attach to a not detached screen
$ screen -L -S <sockname>
$ screen -ls
$ screen -x <pid>.sockname

# run xtvrmscreen iterations
$ /opt/cray/diag/workload/xtvrmscreen -s smw2 -r <reservation_name> -c <blade_id0>,<blade_id1>,...,<blade_idn>
```
