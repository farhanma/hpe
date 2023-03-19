---
title: KSL RT ticket
---

- Email incident-reply@hpc.kaust.edu.sa to create a KSL RT ticket requesting for:
    - Creating a reservation in SLURM of compute nodes for exclusive use
    - Draining compute nodes so that no new jobs can be scheduled on them
- Email incident-reply@hpc.kaust.edu.sa to update a KSL RT ticket requesting for:
    - Canceling a SLURM reservation
    - Resuming drained compute nodes into production
- In the email, you can either include a list of the node id ( `nid` ), e.g.,
  `nid0[5100-5103,5820-5823]`, or a list of the component name ( `cname` ),
  e.g., blade id `c6-2c1s11,c0-3c0s15`

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
$ NIDS=`scontrol show hostnames nid0[5100-5103,5820-5823]`; for nid in $NIDS; do nid2str $nid | sed 's/.\{2\}$//' ; done | sort -u

c0-3c0s15
c6-2c1s11

# get all nids in a blade
$ nid2blade nid05200

nid0[5200-5203]

# convert a node string to a nid
$ str2nid c7-2c0s4n0

nid05200

# query reservation
$ scontrol show res rt46431

ReservationName=rt46431 StartTime=2023-03-12T09:24:54 EndTime=2023-03-15T09:24:54 Duration=3-00:00:00
   Nodes=nid0[6448-6451,6740-6743] NodeCnt=8 CoreCnt=256 Features=(null) PartitionName=(null) Flags=OVERLAP,IGNORE_JOBS,SPEC_NODES
   TRES=cpu=512
   Users=(null) Groups=(null) Accounts=k00,v1003 Licenses=(null) State=ACTIVE BurstBuffer=(null) Watts=n/a
   MaxStartDelay=(null)

$ sinfo -T

RESV_NAME        STATE           START_TIME             END_TIME     DURATION  NODELIST
rt46431         ACTIVE  2023-03-12T09:24:54  2023-03-15T09:24:54   3-00:00:00  nid0[6448-6451,6740-6743]

# query nodes slurm state
$ scontrol show node nid0[6448-6451,6740-6743] | egrep "NodeName|State" | awk '{print $1}' | paste -s -d' \n'

NodeName=nid06448 State=IDLE+RESERVED
NodeName=nid06449 State=IDLE+RESERVED
NodeName=nid06450 State=IDLE+RESERVED
NodeName=nid06451 State=IDLE+RESERVED
NodeName=nid06740 State=IDLE+RESERVED
NodeName=nid06741 State=IDLE+RESERVED
NodeName=nid06742 State=IDLE+RESERVED
NodeName=nid06743 State=IDLE+RESERVED
                        │    │
                        │    └───node state flags ( RESERVED - the node is in an advanced reservation and not generally available )
                        └───node state codes ( IDEL - the node is not allocated to any jobs and is available for use )

# check if one of the nodes are allocated for a specific job
$ squeue -w nid0[6448-6451,6740-6743]

JOBID       USER ACCOUNT           NAME  ST REASON    START_TIME                TIME  TIME_LEFT NODES
```
