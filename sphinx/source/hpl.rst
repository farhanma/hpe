HPL
===

.. meta::
  :description: HPL benchmark on Shaheen II
  :keywords: HPL, gflops, linpack

High Performance LINPACK ( HPL ) is a high performance implementation of the
LINear Algebra PACKage ( LINPACK ) benchmarks to measure the computing power of
a system's floating-point. Theoretically, the floating-point of a system can be
calculated by the following equation:

.. math::

  GFLOPS = \text{CPU GHz} \times \text{cores} \times
  \text{instruction per cycle} \times \text{sockets} \times \text{nodes}

For instance, the Intel Haswell CPU that's used in Shahenn II delivers a
theoretical peak performance of: :math:`1.18 \text{ TFLOPS }`,
whereas the sustained LINPACK performance of single compute node of Shaheen II is
between: :math:`935-955 \text{ GFLOPS ( } \sim80\% \text{ of the peak performance ) }`.

1. Request reservation

  - Email incident-reply@hpc.kaust.edu.sa, to create a KSL RT ticket requesting
    for reservation on the nodes to be benchmarked
  - You can provide either the node ID, e.g., :code:`nid0[5100-5103,5820-5823]`,
    or the blade ID, e.g., :code:`c6-2c1s11,c0-3c0s15`

    .. code-block:: console

      $ nid2str nid05200

        c7-2c0s4n0
        │ │ │ │ │
        │ │ │ │ └───node {0..3}
        │ │ │ └───slot {0..15}
        │ │ └───chassis {0..2}
        │ └───row {0..3}
        └───cabinet {0..9}

  - Make sure the nodes are not in a drained state

    .. code-block:: console

      $ NID=nid0[5100-5103,5820-5823]
      $ scontrol show node $NID | egrep "NodeName|State" | awk '{print $1}' | paste -s -d' \n'
      $ squeue -w $NID
      $ scontrol show res <reservation_id>

  - If they're in a drained state, then ask for the nodes to be resumed in the RT
    ticket

2. Shaheen II HPL binary and a sample SLURM script can be downloaded from:
   `<https://github.com/farhanma/hpe-docs/tree/opt/hpl>`_
3. Once reservation is granted and nodes SLURM state are IDLE+DRAIN, run HPL through SLURM as follows:

  .. code-block:: console

    $ cd /scratch/<username>
    $ git clone --branch opt https://github.com/farhanma/hpe_sysadmin_guide.git
    $ cd hpe_sysadmin_guide/shaheen2/hpl
    $ cat linpack_slurm.sh

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
    #SBATCH --account=<account_name>         # e.g., v1003
    #SBATCH --reservation=<reservation_name> # e.g., rt29677

    export OMP_NUM_THREADS=32
    export KMP_AFFINITY=nowarnings,scatter,1,0,granularity=fine

    ./xlinpack_xeon64 lininput_xeon64

    $ cat run.sh

    for i in {5100..5103} {5820..5823}
    do
      sbatch -w nid0$i linpack_slurm.sh
    done

    # to run the above bash script
    $ ./run.sh

    # to check the submitted SLURM jobs
    $ squeue -u <shaheen_username>
