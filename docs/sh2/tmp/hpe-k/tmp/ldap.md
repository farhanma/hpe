- LDAP directory
  - _tree_ structure
  - all entries called _objects_ have a defined position within _hierarchy_
    - objects type is called _object class_, which determines what _attributes_ the relevant object must or can be assigned
    - _Schema_ globally stored definitions of all object classes and attributes
  - hierarchy is called _directory information tree ( DIT )_
  - the complete path to the desired entry is called _distinguished name ( DN )_
  - a single node along the path to this entry is called _relative distinguished name ( RDN )_

```sh
# dn: uid=farhanma,ou=users,dc=hpc,dc=kaust,dc=edu,dc=sa
# dn: uid=shahinws,ou=users,dc=hpc,dc=kaust,dc=edu,dc=sa
dc=hpc,dc=kaust,dc=edu,dc=sa
│   ...
│   ...
│
└───ou=users
│   │   ...
│   │   ...
│   │
│   └───uid=farhanma
│   │   cn=Mohammed Al Farhan
│   │   sn=Al Farhan
│   │   ...
│   │
│   └───uid=shahinws
│   │   cn=Wijdan Shahin
│   │   sn=Shahin
│   │   ...
│
└───ou=...
    │   ...
    │   ...

```

  - schema determines the type of information entries in the DIT
  - type of an object is determined by the object class

- CN  Common Name          Mohammed Al Farhan
- OU  Organizational Unit  users
- DC  Domain Component     hpc.kaust.edu.sa
