# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

## Scratchpad

```sh
- rw- r-- r--
│ │││ │││ ││└───executable ( other ( everyone ) permissions )
│ │││ │││ │└───writable ( other ( everyone ) permissions )
│ │││ │││ └───readable ( other ( everyone ) permissions )
│ │││ │││
│ │││ ││└───executable ( group permissions )
│ │││ │└───writable ( group permissions )
│ │││ └───readable ( group permissions )
│ │││
│ ││└───executable ( user permissions )
│ │└───writable ( user permissions )
│ └───readable ( user permissions )
│
└───file type
    -    Regular file
    b    Block special file
    c    Character special file
    d    Directory
    l    Symbolic link
    p    FIFO
    s    Socket
    w    Whiteout

    user/group
        s    setuid ( Set User  IDentity )
             setgid ( Set Group IDentity )
             set on an executable file, such that the file will be executed with
             the same permissions as the owner of the executable file, for example
             $ ls -l /usr/bin/passwd
             -rwsr-xr-x 1 root root 59640 Mar 22  2019 /usr/bin/passwd
             any user running the passwd command will be running it with the
             same permission as root
    other ( everyone )
        t    sticky bit

    S/T  error that you should look into; no executable permission ( x )

# LDAP add group

    dn: cn=hpe,ou=users,dc=hpc,dc=kaust,dc=edu,dc=sa
    objectClass: top
    objectClass: posixGroup
    description: tagGroup
    gidNumber: 53297
    cn: hpe
    memberUid: farhanma
    memberUid: jonjl
    memberUid: x_thomasf
    memberUid: x_poenaras
    memberUid: x_esposia
    memberUid: castlepb
    memberUid: abdelah
    memberUid: abdulref
    memberUid: ahmeia0a

# query the group
getent group hpe

    dn: cn=hpe,ou=users,dc=hpc,dc=kaust,dc=edu,dc=sa
    changetype: modify
    add: memberUid
    memberUid: x_wauligp
    memberUid: x_judgeha
    memberUid: x_thorbej
    memberUid: x_venkatm
```
