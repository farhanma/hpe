---
title: Trimming
---

If LINPACK performance on a compute node does not match the minimum acceptable
performance (i.e., `~935 GFLOPS`), then it needs to be trimmed using Cray Workload
Test Suite (WTS).

- Create a KSL RT ticket requesting for reservation on the nodes to be trimmed
- Make sure that the nodes' SLURM state is `IDLE+RESERVED` (not `DRAIN`)
- Run HPL before trimming to confirm the low performance
- Use Shaheen internal login nodes (`gateway`) to perform trimming
    - Trimming scripts are installed in `/opt/cray/diag/workload/`
- Run HPL after the trimming to confirm the trimming successfulness
- Report the post-trimming HPL results in email to KSL updating the RT ticket

```sh
$ ssh farhanma@shaheen.hpc.kaust.edu.sa
$ git clone https://github.com/farhanma/hpe.git /scratch/farhanma/.
$ ssh gateway1
$ cd /scratch/farhanma/hpe/docs/shaheen2/trimming/workload

$ export SLURM_RESERVATION=rt46392
$ export SLURM_ACCOUNT=v1003
$ export SLURM_PARTITION=all
$ export OMP_STACKSIZE=128M
$ ulimit -s unlimited

$ screen -L -S trimming.rt46392
#  -L  turn on output logging
#  -S  session name
$ ./xtvrmscreen -s smw2 -c <blade_id0>,<blade_id1>,...,<blade_idn>

$ screen -ls                   # list all of the screen sessions
$ screen -x <pid>.sockname     # reattach to existing trimming screen session
#  detach screen from this terminal
#    C-a d
#    C-a C-d
#  enter copy/scrollback mode
#    C-a [
#    C-a C-[
#    C-a esc

# if trimming fails, then check the logs for hardware failure, e.g., high DIMM
# error count, CPU issue, ... etc

$ ssh shaheen
$ ssh crayadm@smw2
$ logs # ( cd /var/opt/cray/log/p0-current )
$ xthwerrlog -M -i -f hwerrlog.p0-20230301t162823 -C c3-3c1s12

Node         Count     Chan  Type           DIMM   BIT(s)  Detail
--------------------------------------------------------------------------------
c3-3c1s12n0  642       0     CORRECTABLE    J4002          Read Error
c3-3c1s12n0  40671590  0     CORRECTABLE    J4002  DQ19    Memory Scrub Error
c3-3c1s12n0  2570      0     CORRECTABLE    J4002  DQ19    Read Error

Node          Socket  Count    Bank                  Type
--------------------------------------------------------------------------------
c3-3c1s12n0   1       642      8   (HA 1)            CORRECTABLE
c3-3c1s12n0   1       19101384 13  (iMC 4)           CORRECTABLE
```
