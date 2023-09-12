```sh title="Lustre Networking ( LNet )"
- Lustre Networking ( LNet ) supports various types of networks via Low-level
  device layer ( Lustre Network Driver ( LND ) )
  - Pluggable driver module
  - Provides an interface abstraction between the upper-level LNet protocol and
    and the kernel device driver for the network interface
    - Each low-level network protocol requires a separate LND
    - If the server requires access to more than one type of network, then
      multiple LNDs can be active on a host simultaneously
    - ksocklnd.ko module
      ││      │
      ||      └───Loadable kernel modules ( .ko files )
      |└──The abbreviation "socklnd" is for TCP/IP networks
      └─The letter "k" prefix is to emphasize that this is a kernel module
    - ko2iblnd.ko module
      ││      │
      ||      └───Loadable kernel modules ( .ko files )
      |└──The abbreviation "o2iblnd" is for RDMA networks that make use of the
      |   OFED network driver ( supports fabrics running InfiniBand, Omni-Path,
      |   and RDMA over Converged Ethernet (RoCE) )
      └─The letter "k" prefix is to emphasize that this is a kernel module
    - LNet also supports the ability to route Lustre communications between
      different networks using dedicated computers called "LNet routers" can
      direct traffic between multiple LNets
    - The address of the network interfaces
        -  LNet Network Identifier ( NID )
        -  It uniquely defines an interface for a host on an LNet communications
           fabric
        - `<address>@<LND protocol><lnd#>`
        - Node identifier -- For tcp and o2ib LNDs, the address is the IPv4
                             address of a network device on the host
        - Protocol identifier
        - Network number
        - Even though the o2ib LNet driver uses OFED Verbs for communications,
          the IP address of the IB interface is used to identify the IB interface
          for the initial connection with a peer. After the initial connection,
          the o2ib LND uses only RDMA for all further communications. By default,
          socklnd uses TCP port 988 to create connections, and this must not be
          blocked by any firewalls
```
