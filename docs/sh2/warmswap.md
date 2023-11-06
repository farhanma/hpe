---
title: Warm swap
---

- Cray XC-40 warm swap procedure on System Management Workstation ( SMW )
    - `ssh smw2` ( _Shaheen2_ )
    - `ssh smw3` ( _Osprey_ -- Test and Development System ( TDS ) )
- Warm swap procedure is done on blade(s) for hardware repair work or without
  carrying out any repair work
- Once you receive an email from the KSL RT ticketing system that "drained on
  blade(s) has begun", you can start with the warm swap operation
- The procedures are for compute blades not for service blades
- If a Haswell Processor Daughter Card ( HPDC ) is being replaced, note:
    - Serial number of the blade: `sn <blade_id>`
    - Firmware versions: `xtzap -rvv <blade_id>`
    - In case of firmware mismatch, you should `xtzap` the blade: `xtzap -bv <blade_id>`

```sh title="Check the blade type" hl_lines="6-14 18-26"

#   -          compute node
#   service    service node

$ xtcli status c8-3c2s3

Network topology: class 2
Network type: Aries
           Nodeid: Service  Core Arch|  Comp state      [Flags]
--------------------------------------------------------------------------------
       c8-3c2s3n0:       -  HW32  X86|       ready      [noflags|]
       c8-3c2s3n1:       -  HW32  X86|       ready      [noflags|]
       c8-3c2s3n2:       -  HW32  X86|       ready      [noflags|]
       c8-3c2s3n3:       -  HW32  X86|       ready      [noflags|]
--------------------------------------------------------------------------------

$ xtcli status c8-3c0s0

Network topology: class 2
Network type: Aries
           Nodeid: Service  Core Arch|  Comp state      [Flags]
--------------------------------------------------------------------------------
       c8-3c0s0n0: service           |       empty      [noflags|]
       c8-3c0s0n1: service  SB08  X86|       ready      [noflags|]
       c8-3c0s0n2: service  SB08  X86|       ready      [noflags|]
       c8-3c0s0n3: service           |       empty      [noflags|]
--------------------------------------------------------------------------------
```

```sh title="Warm swap out the blade from the HSN ( High Speed Network )"
$ xtcli halt <blade_id>

$ xtwarmswap -r <blade_id>

$ xtcli power down <blade_id>

# confirm if the blade has been powered down
$ xtalive -t2 <blade_id>
```

- Carry out the hardware repair work: FRP ( Field Replacement Procedure )

```sh title="Warm swap in the blade to the HSN ( High Speed Network )"
$ xtcli power up <blade_id>

$ xtbounce -o link_deadstart=false <blade_id>

#   linktune        no hardware work, and
#                   the warm swap is done to clear the HSN errors
$ xtwarmswap -a <blade_id> [--linktune]

$ xtbootsys --reboot -r BLADEreboot <blade_id>
```
