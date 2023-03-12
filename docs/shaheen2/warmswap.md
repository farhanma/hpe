---
title: Warm swap
---

- Cray XC-40 warm swap procedure on `smw2` ( Shaheen2 ) `smw3` ( TDS ( Osprey ) )
    - SMW: System Management Workstation
- Warm swap procedure is done on blade(s) for hardware repair work or without
  carrying out any repair work
- Once you receive an email from the KSL RT ticketing system that "drained on
  blade(s) has begun", you can start with the warm swap operation

```sh
$ ssh smw2

# Check the blade type -- the procedures are for compute blades not service
# blades, for example

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

# note "Service" column
#   -           compute node
#   service     service node

$ xtcli halt <blade_id>

# warm swap out the blade from the HSN ( High Speed Network )
$ xtwarmswap -r <blade_id>

# check the serial number of the blade and the two HPDCs and make a note of this
$ sn <blade_id>

$ xtcli power down <blade_id>

# confirm if the blade has been powered down
$ xtalive -t2 <blade_id>

################################################################################
#                                                                              #
# carry out the hardware repair work: FRP ( Field Replacement Procedure )      #
#                                                                              #
################################################################################

$ xtcli power up <blade_id>

$ xtbounce -o link_deadstart=false <blade_id>

# check firmware versions
$ xtzap -rvv <blade_id>
# if you have replaced an HPDC, or the entire blade, then there is a possibility
# of firmware mismatch, in this case, you should "xtzap" the blade
$ xtzap -bv <blade_id>

$ xtwarmswap -a <blade_id>
# if you have not done any hardware work, and if you are simply warm swapping a
# blade to clear HSN errors, then
$ xtwarmswap -a <blade_id> --linktune

$ xtbootsys --reboot -r BLADEreboot <blade_id>

# if you have replaced an HPDC, or the entire blade, then make a note of the new
# serial numbers
$ sn <blade_id>
```
