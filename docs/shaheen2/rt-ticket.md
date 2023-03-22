---
title: KSL RT ticket
---

- Email incident-reply@hpc.kaust.edu.sa to create/update a KSL RT ticket
  requesting for:
    - Creating a reservation in SLURM of compute nodes for exclusive use,
    - Canceling a SLURM reservation,
    - Draining compute nodes so that no new jobs can be scheduled on them, or
    - Resuming drained compute nodes into production
- In the email, you can either include a list of the node id ( `nid` ), e.g.,
  `nid0[5100-5103,5820-5823]`, or a list of the component name ( `cname` ),
  e.g., blade id `c6-2c1s11,c0-3c0s15`
- Existing scripts available, e.g., `nid2str`, `str2nid`, and `nid2blade`, to
  get a list of the component name ( blade id ) and/or node id.
- Existing SLURM commands can be used to query the status of a reservation,
e.g., `scontrol show res rt46431`, `sinfo -T`,  and `squeue -w nid0[6448-6451,6740-6743]`

``` sh title="Description of the component name" hl_lines="3-9"
$ nid2str nid05200

c7-2c0s4n0
 │ │ │ │ │
 │ │ │ │ └───node {0..3}
 │ │ │ └───slot {0..15}
 │ │ └───chassis {0..2}
 │ └───row {0..3}
 └───cabinet {0..9}
```

``` sh title="Convert NIDs to CNAMEs"
$ NIDS=`scontrol show hostnames nid0[5100-5103,5820-5823]`; for nid in \
$NIDS; do nid2str $nid | sed 's/.\{2\}$//'; done | sort -u # (1)
```

1. The expected output is: `c0-3c0s15` and `c6-2c1s11`

``` sh title="Query the nodes states" hl_lines="4-17"
$ scontrol show node nid0[6448-6451,6740-6743] | egrep "NodeName|State" | \
awk '{print $1}' | paste -s -d' \n'

NodeName=nid06448 State=IDLE+RESERVED
NodeName=nid06449 State=IDLE+RESERVED
NodeName=nid06450 State=IDLE+RESERVED
NodeName=nid06451 State=IDLE+RESERVED
NodeName=nid06740 State=IDLE+RESERVED
NodeName=nid06741 State=IDLE+RESERVED
NodeName=nid06742 State=IDLE+RESERVED
NodeName=nid06743 State=IDLE+RESERVED
                        │    │
                        │    └───node state flags # (1)
                        └───node state codes # (2)
```

1. `RESERVED`: the node is in an advanced reservation and not generally available
2. `IDEL`: the node is not allocated to any jobs and is available for use
