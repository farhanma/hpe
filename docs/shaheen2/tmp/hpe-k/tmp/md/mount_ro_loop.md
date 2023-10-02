- `mount -o ro,loop`
  - `-o, --options <list> comma-separated list of mount options`
    - `ro     mounts a file system as read-only`
    - `loop   uses a loop device (/dev/loop*) to mount a file that contains a file system image`

- Loop device
  - Regular file or device that is mounted as a file system
  - Pseudo (fake) device by which OS kernel treats the file's contents as a block device
  - For example, an ISO file containing internal structure details of files and directories may be
    mounted as a loop device, and accessed by the OS, like a physical disk partition.
- Character device
  - The driver communicates by sending and receiving single characters (bytes, octets)
  - Example: serial ports, parallel ports, sound cards, keyboard
- Block device
  - The driver communicates by sending entire blocks of data
  - Example: hard disks, USB cameras, Disk-On-Key

- Note the filesystems can only be mounted if they are on block devices
