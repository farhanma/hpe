---
title: Reservation
---

## Request reservation in slurm

1. Email incident-reply@hpc.kaust.edu.sa to create a KSL RT ticket requesting
   for reservation on the nodes to be allocated
2. If a specific list of nodes needs to reserved, then in the RT ticket email,
   provide either the node id ( `nid` ), e.g., `nid0[5100-5103,5820-5823]`, or
   the component name ( `cname` ), e.g., blade id `c6-2c1s11,c0-3c0s15`
3. Email incident-reply@hpc.kaust.edu.sa to update the KSL RT ticket requesting
   for reservation on the nodes to be removed and the nodes will automatically
   be incorporated into SLURM production

## Useful commands

```sh
# convert a node id ( nid ) into the component name ( cname )
# node id to blade name
$ nid2str nid05200
   c7-2c0s4n0
   │ │ │ │ │
   │ │ │ │ └───node {0..3}
   │ │ │ └───slot {0..15}
   │ │ └───chassis {0..2}
   │ └───row {0..3}
   └───cabinet {0..9}

# useful script to handle multiple nids
$ NIDS=`scontrol show hostnames nid0[5100-5103,5820-5823]`; \
  for nid in $NIDS; do nid2str $nid | sed 's/.\{2\}$//' ; done | sort -u
   c0-3c0s15
   c6-2c1s11
2
# get all nids in a blade
$ nid2blade nid05200
   nid0[5200-5203]

# query reservation
$ scontrol show res <reservation_id>
$ sinfo -T

# query nodes slurm state
$ scontrol show node nid0[5100-5103,5820-5823] | egrep "NodeName|State" | \
  awk '{print $1}' | paste -s -d' \n'

# check if one of the nodes are allocated for a specific job
$ squeue -w nid0[5100-5103,5820-5823]
```
