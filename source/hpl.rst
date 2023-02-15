HPL
===

.. meta::
  :description: HPL benchmark on Shaheen II
  :keywords: HPL, gflops, linpack

HPL ( High Performance LINPACK ( Linear Algebra PACKage ) ) benchmarks are a
measure of a system's floating-point computing power. The equation to calculate
the theoretical peak of the floating-point performance of a system can be
measured by the following equation:

.. math::

  GFLOPS = \text{CPU GHz} \times \text{cores} \times
  \text{instruction per cycle} \times \text{sockets} \times \text{nodes}

The Intel Haswell node of Shahenn II delivers a theoretical peak performance of:
:math:`1177.6 \text{ GFLOPS }`,
whereas the sustained LINPACK performance of a Shaheen II compute node is between:
:math:`935-955 \text{ GFLOPS ( } \sim80\% \text{ of the peak performance ) }`.

..
  Get the LINKPACK binary for Shaheen-II and a SLURM script at ``_.

Request reservation
-------------------

Send an email to: incident-reply@hpc.kaust.edu.sa, to create a KSL RT ticket
requesting for reservation on the nodes to be tested ( e.g.,
:code:`nid0[5100-5103,5820-5823]` ) or you can use the blade ID for your request.
To get the blade ID from a node ID, use: :code:`nid2str` script, e.g.,
:code:`nid2str nid05100 | head -c -3; echo`.

.. code-block:: console

  c6-2c1s5n0
  │ │ │ │ │
  │ │ │ │ └───node {0..3}
  │ │ │ └───slot {0..15}
  │ │ └───chassis {0..2}
  │ └───row {0..3}
  └───cabinet {0..9}

Make sure the nodes are not in a drained state. If they are in a drained state
asked for the nodes to be resumed in the KSL RT ticket.

.. code-block:: console

  $ NID=nid0[5100-5103,5820-5823]
  $ echo; scontrol show node $NID | egrep "NodeName|State" | awk '{print $1}' | paste -s -d' \n'; echo

  NodeName=nid05100 State=ALLOCATED
  NodeName=nid05101 State=ALLOCATED
  NodeName=nid05102 State=ALLOCATED
  NodeName=nid05103 State=ALLOCATED
  NodeName=nid05820 State=ALLOCATED
  NodeName=nid05821 State=ALLOCATED
  NodeName=nid05822 State=ALLOCATED
  NodeName=nid05823 State=ALLOCATED

  $ echo; squeue -w $NID; echo

    JOBID       USER ACCOUNT           NAME  ST REASON    START_TIME                TIME  TIME_LEFT NODES

  $ echo; scontrol show res rt29677; echo

  ReservationName=rt29677 StartTime=2020-02-27T12:31:52 EndTime=2020-02-28T00:31:52 Duration=12:00:00
     Nodes=nid0[5100-5103,5820-5823] NodeCnt=8 CoreCnt=256 Features=(null) PartitionName=(null) Flags=SPEC_NODES
     TRES=cpu=512
     Users=(null) Groups=(null) Accounts=v1003,k00, k01 Licenses=(null) State=ACTIVE BurstBuffer=(null) Watts=n/a
     MaxStartDelay=(null)

LINPACK SLURM script
--------------------

Shaheen-II LINKPACK binary and a sample SLURM script can be downloaded from
`<https://github.com/farhanma/hpe-docs/tree/opt/hpl>`_.

.. code-block:: console

  #!/bin/bash

  #SBATCH -N 1
  #SBATCH -t 0:50:00
  #SBATCH --output=linpack-%A_%a_%N.out
  #SBATCH --err=linpack-%A_%a_%N.err
  #SBATCH --ntasks=1
  #SBATCH --cpus-per-task=32
  #SBATCH --sockets-per-node=2
  #SBATCH --cores-per-socket=16
  #SBATCH --threads-per-core=1
  #SBATCH --hint=nomultithread
  #SBATCH --account=v1003
  #SBATCH --reservation=rt29677

  export OMP_NUM_THREADS=32
  export KMP_AFFINITY=nowarnings,scatter,1,0,granularity=fine

  ./xlinpack_xeon64 lininput_xeon64

Lunching multiple LINPACK script
--------------------------------

.. code-block:: console

  for i in {5100..5103} {5820..5823}
  do
    sbatch -w nid0$i linpack_slurm.sh
  done
