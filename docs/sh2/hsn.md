---
title: Trimming
---

This is a Technical Work Instruction “TWI” document on repairing HSN link issues.

This repair procedure is usually done once a link has failed on the HSN. A SEC mail alert will be generated or the daily KAUST Shaheen report will highlight link issues.

xtchecklink
xtchecklink -S
check_hsn
dcnu -i # Check Fault End Points

## Cable types

- Back plane
  - Color is green
  - Both endpoints are in the same cage
  - Example: `rxLink c4-3c1s13a0l36 <-- remote txLink c4-3c1s5a0l43`
  - Warm swap out blades and move them to different cabinets and slot locations
    often clears the link errors
- Copper
  - Color is black
  - Both endpoints are in the same cabinet group but different cages
  - Example: `rxLink c8-1c2s12a0l10 <-- remote txLink c9-1c0s12a0l11`
  - Replace dead HSN Component
  - Reseat, move, and replace sick HSN Component
- Active Optical Cable ( AOC )
  - Color is blue
  - Both endpoints are in different cabinet groups
  - Example: `rxLink c3-2c0s15a0l04 <-- remote txLink c5-2c0s15a0l04`
  - `rtr --connector-link-map=<component_name>`
  - `xtwarmswap --remove-cable <cable_endpoint>`
  - `xtwarmswap --add-cable <cable_endpoint> [--linktune]`
