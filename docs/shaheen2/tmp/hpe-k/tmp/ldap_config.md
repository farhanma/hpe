```sh
$ zypper -n openldap2
$ cp /etc/sysconfig/openldap /etc/sysconfig/openldap.org
$ vi /etc/sysconfig/openldap

# line 151: change
OPENLDAP_CONFIG_BACKEND="ldap"

$ cd /etc/tmpfiles.d
$ echo 'D /run/openldap 0755 ldap ldap' >> slapd.conf
$ systemd-tmpfiles --create
$ systemctl start slapd
$ systemctl enable slapd
```
