```sh
ssh shaheen.hpc.kaust.edu.sa
ssh admin@snxmgr5

  # username: admin
  # password: alphar0me0

sudo -i

  # username: admin
  # password: alphar0me0

pdsh -a dm_report | egrep -i 'failed|empty|unused' | dshbak -c

pdsh -a cat /proc/mdstat | egrep -i 'rec|sync|repair|check' | dshbak -c

  # ----------------------------------------------------------------------------
  # pdsh -a                 | target all nodes except those with "pdsh_all_skip"
  #                           attribute
  # egrep -i, --ignore-case | ignore case distinctions
  # dshbak                  | format output from pdsh command
  # dshbak -c               | do not display identical output from nodes twice
  # ----------------------------------------------------------------------------
  # /proc/mdstat is a special file that shows the state of the Linux kernel's md
  # driver. md (multiple device) driver is the software RAID implementation that
  # allows you to create any number of RAID devices based on the disk devices
  # (physical or virtual) available to your Linux system.
  # ----------------------------------------------------------------------------
```
