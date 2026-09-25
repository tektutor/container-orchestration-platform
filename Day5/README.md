# Day 5

## Info - Images available in Openshift Internal Registry
<pre>
image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.30
image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.29
image-registry.openshift-image-registry.svc:5000/openshift/bitnami-nginx:1.28  
</pre>

## Info - Keycloak Overview
<pre>
- an opensource Identiy and Access Management (IAM) solution designed for modern application and services
- helps us manage who can access your applications, what they can do with your applications
- Mainly used for Single Sign-on(SSO)
- handles the process of verifying an user's identify
- supports below 
  - login with username & password
  - Multi-factor Authentication (MFA)
    - OTP
    - Social Media Logins
      - Facebook
      - Twitter
      - Gmail
      - GitHub, etc
- provides a centralized user management
</pre>

## Info - OpenLDAP 
<pre>
- is an opensource software commonly used in Linux distributions
- LDAP - Lightweight Directory Access Protocol
- distributed directory information services over IP
- Supports Centralized User and Identity Management
  - User Authentication
    - User and respective credentials will be stored in LDAP server
    - When we attempt to login to some software with LDAP Integration, the LDAP server will verify login and authenticates
  - Authorization
    - LDAP stores information about user's roles and group memembership
    - LDAP determines what permission a user has 
    - RBAC - Role-Based Access Control
  - Single Sign-ON(SSO)
</pre>

## Demo - Securing your Red Hat Openshift with OpenLDAP (SSO)

#### OpenLDAP on Ubuntu 24.04 as an OpenShift LDAP Identity Provider (LDAPS)

This lab installs OpenLDAP on Ubuntu 24.04, adds users and groups, enables TLS on port 636, and configures OpenShift 4 to authenticate users against it over LDAPS.

Replace these with your own values if your environment differs.

| Item | Value |
|---|---|
| LDAP server hostname | `palmeto` |
| LDAP server IP | `192.168.2.200` |
| LDAP server OS | Ubuntu 24.04 LTS |
| Domain / base DN | `palmeto.org` / `dc=palmeto,dc=org` |
| Admin (root) DN | `cn=admin,dc=palmeto,dc=org` |
| Admin password | `admin@123` |
| User password | `palmeto@123` |
| Users OU | `ou=users,dc=palmeto,dc=org` |
| Groups OU | `ou=groups,dc=palmeto,dc=org` |
| OpenShift API | `https://api.ocp4.palmeto.org:6443` |
| OpenShift node network | `192.168.100.0/24` |
| Identity provider name | `ldap` |

These passwords suit an isolated training lab only. Never reuse them on a system reachable from outside.

#### Prerequisites

- Ubuntu 24.04 server with a static IP and `sudo` access
- OpenShift 4 cluster with `cluster-admin` access (`system:admin` or `kubeadmin`)
- `oc` CLI on the LDAP server or on your workstation
- Network route from the OpenShift nodes to the LDAP server


Install OpenLDAP, preseed the install answers

Ubuntu derives the base DN from the domain you give the installer. Preseed it so the result is `dc=palmeto,dc=org`:

```bash
sudo apt update

cat <<'EOF' | sudo debconf-set-selections
slapd slapd/no_configuration boolean false
slapd slapd/domain string palmeto.org
slapd shared/organization string Palmeto
slapd slapd/password1 password admin@123
slapd slapd/password2 password admin@123
slapd slapd/purge_database boolean true
slapd slapd/move_old_database boolean true
EOF
```

Install the packages

```bash
sudo DEBIAN_FRONTEND=noninteractive apt install -y slapd ldap-utils
```

If `slapd` was already installed with a different domain, reconfigure it and answer the prompts with the values above:

```bash
sudo dpkg-reconfigure slapd
```

Verify the install

```bash
sudo systemctl status slapd --no-pager | head -3

sudo ldapsearch -Y EXTERNAL -H ldapi:/// -b cn=config -LLL \
  '(olcSuffix=*)' olcSuffix olcRootDN 2>/dev/null
```

Expected:

```
dn: olcDatabase={1}mdb,cn=config
olcSuffix: dc=palmeto,dc=org
olcRootDN: cn=admin,dc=palmeto,dc=org
```

Test the admin bind:

```bash
ldapwhoami -x -H ldap://localhost -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123'
```

Expected: `dn:cn=admin,dc=palmeto,dc=org`

The admin DN is the database root DN. It lives in `cn=config` (`olcRootDN`, `olcRootPW`), not as an entry in the directory tree. Part 8 shows how to change its password.


Add OUs, users and groups

Create the OUs first (2.1). Then add users with either Option A (2.2, a fixed sample set) or Option B (2.3, import the local Linux users of the LDAP server). Add groups last (2.4).

Create the OUs

```bash
mkdir -p ~/ldap-lab && cd ~/ldap-lab

cat > ous.ldif <<'EOF'
dn: ou=users,dc=palmeto,dc=org
objectClass: organizationalUnit
ou: users

dn: ou=groups,dc=palmeto,dc=org
objectClass: organizationalUnit
ou: groups
EOF

ldapadd -x -H ldap://localhost -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123' -f ous.ldif
```

Expected: two `adding new entry` lines.

Import local Linux users

`gen-ldap-users.sh` reads accounts from `getent passwd` and writes an LDIF. It:

- keeps only regular accounts with UIDs between `UID_MIN` and `UID_MAX` from `/etc/login.defs` (1000 to 60000 on Ubuntu)
- always skips UID 0 and any name listed in `EXCLUDE_USERS` (default `root nobody`)
- takes `cn` from the full name in GECOS and `sn` from its last word
- generates a fresh salted hash per user with `slappasswd`, so the stored hash always matches the password you pass

```bash
#!/bin/bash
# Generate an LDIF of local Linux users (UID_MIN..UID_MAX) for OpenLDAP.
# Usage: ./gen-ldap-users.sh [password]   (default: palmeto@123)
set -euo pipefail

BASE_DN="dc=palmeto,dc=org"
USERS_OU="ou=users,${BASE_DN}"
MAIL_DOMAIN="palmeto.org"
OUTPUT_FILE="palmeto-ldap-users.ldif"
USER_PASS="${1:-palmeto@123}"
EXCLUDE_USERS="root nobody"

UID_MIN=$(awk '/^UID_MIN/ {print $2}' /etc/login.defs 2>/dev/null || true)
UID_MAX=$(awk '/^UID_MAX/ {print $2}' /etc/login.defs 2>/dev/null || true)
UID_MIN=${UID_MIN:-1000}
UID_MAX=${UID_MAX:-60000}

command -v slappasswd >/dev/null || { echo "slappasswd not found: sudo apt install slapd" >&2; exit 1; }

: > "$OUTPUT_FILE"
count=0

while IFS=':' read -r username _ uid gid gecos home shell; do
    # Regular login accounts only; never UID 0
    [[ "$uid" -eq 0 ]] && continue
    (( uid >= UID_MIN && uid <= UID_MAX )) || continue
    [[ " $EXCLUDE_USERS " == *" $username "* ]] && continue

    # GECOS is "Full Name,Room,Phone,..."; keep the name part
    full="${gecos%%,*}"
    if [[ -z "$full" ]]; then
        cn="$username"
        sn="$username"
    else
        cn="$full"
        sn="${full##* }"
    fi

    # Fresh salt per user, so equal passwords get different hashes
    hash=$(slappasswd -s "$USER_PASS")

    cat >> "$OUTPUT_FILE" <<LDIF
dn: uid=${username},${USERS_OU}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: ${username}
cn: ${cn}
sn: ${sn}
uidNumber: ${uid}
gidNumber: ${gid}
homeDirectory: ${home}
loginShell: ${shell}
mail: ${username}@${MAIL_DOMAIN}
userPassword: ${hash}

LDIF
    count=$((count + 1))
done < <(getent passwd)

echo "Wrote ${count} users to ${OUTPUT_FILE}"
```

Run it and review the list before loading:

```bash
chmod +x gen-ldap-users.sh
./gen-ldap-users.sh 'palmeto@123'
grep '^dn:' palmeto-ldap-users.ldif
```

Load it:

```bash
ldapadd -c -x -H ldap://localhost -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123' \
  -f palmeto-ldap-users.ldif
```

`-c` continues past entries that already exist (`Already exists (68)`). Existing users keep their old password. Reset all users to a known password with:

```bash
for u in $(ldapsearch -x -H ldap://localhost -b ou=users,dc=palmeto,dc=org -LLL \
             '(objectClass=inetOrgPerson)' uid | awk '/^uid:/ {print $2}'); do
  ldappasswd -x -H ldap://localhost -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123' \
    -s 'palmeto@123' "uid=$u,ou=users,dc=palmeto,dc=org" && echo "reset $u"
done
```

Do not hard-code a `{SSHA}` hash in scripts. You cannot tell by looking at it which password produced it, and a wrong hash only shows up later as `Invalid credentials (49)`.

LDIF requires base64 encoding (`cn:: <base64>`) for values with non-ASCII characters. The script writes names as plain text, so keep GECOS names ASCII or encode those values by hand.

Check that no UID 0 account slipped in from an earlier import:

```bash
ldapsearch -x -H ldap://localhost -b ou=users,dc=palmeto,dc=org -LLL '(uidNumber=0)' dn
```

If it prints a DN, delete it:

```bash
ldapdelete -x -H ldap://localhost -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123' \
  "uid=root,ou=users,dc=palmeto,dc=org"
```

Add groups

`groupOfNames` requires at least one `member`. The member DNs below must match users you created in 2.2 or 2.3.

```bash
cat > groups.ldif <<'EOF'
dn: cn=ocp-admins,ou=groups,dc=palmeto,dc=org
objectClass: groupOfNames
cn: ocp-admins
member: uid=jegan,ou=users,dc=palmeto,dc=org

dn: cn=ocp-developers,ou=groups,dc=palmeto,dc=org
objectClass: groupOfNames
cn: ocp-developers
member: uid=uday,ou=users,dc=palmeto,dc=org
EOF

ldapadd -x -H ldap://localhost -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123' -f groups.ldif
```

Verify

```bash
ldapsearch -x -H ldap://localhost -b ou=users,dc=palmeto,dc=org -LLL uid cn mail

ldapwhoami -x -H ldap://localhost -D "uid=uday,ou=users,dc=palmeto,dc=org" -w 'palmeto@123'
```

The first command runs anonymously. Ubuntu's default ACL allows anonymous reads of everything except `userPassword`. The second must print `dn:uid=uday,ou=users,dc=palmeto,dc=org`.

Enable TLS (LDAPS on port 636)

A fresh install listens only on 389 with no TLS. You can confirm this: the root DSE lacks the StartTLS OID `1.3.6.1.4.1.1466.20037`.

```bash
ldapsearch -x -H ldap://localhost -b "" -s base supportedExtension | grep 1466.20037
```

No output means TLS is not configured.

Create a CA and a server certificate

OpenShift checks the certificate's Subject Alternative Name (SAN), not the CN. Put the exact address the cluster uses to reach LDAP into the SAN.

```bash
mkdir -p ~/ldap-tls && cd ~/ldap-tls

openssl req -x509 -new -nodes -newkey rsa:4096 -days 3650 \
  -keyout ca.key -out ca.crt -subj "/CN=Palmeto LDAP CA"

openssl req -new -nodes -newkey rsa:2048 \
  -keyout ldap.key -out ldap.csr -subj "/CN=192.168.2.200"

cat > san.ext <<'EOF'
subjectAltName = IP:192.168.2.200
extendedKeyUsage = serverAuth
EOF

openssl x509 -req -in ldap.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out ldap.crt -days 825 -extfile san.ext

openssl x509 -in ldap.crt -noout -ext subjectAltName
```

Expected: `IP Address:192.168.2.200`

To use a hostname as well, change the SAN line before signing, for example:
`subjectAltName = IP:192.168.2.200, DNS:ldap.palmeto.org`

Keep `ca.key` safe and off the cluster. You need it to reissue the server certificate before it expires.

Install the files

```bash
sudo install -d -m 755 /etc/ldap/tls
sudo cp ca.crt ldap.crt ldap.key /etc/ldap/tls/
sudo chown root:openldap /etc/ldap/tls/ldap.key
sudo chmod 640 /etc/ldap/tls/ldap.key
```

slapd runs as user `openldap`, so the key must be readable by that group.

Point slapd at the certificates

```bash
cat > tls.ldif <<'EOF'
dn: cn=config
changetype: modify
replace: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/ldap/tls/ca.crt
-
replace: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ldap/tls/ldap.crt
-
replace: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ldap/tls/ldap.key
EOF

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f tls.ldif
```

Expected: `modifying entry "cn=config"`

Verify all three attributes:

```bash
sudo ldapsearch -Y EXTERNAL -H ldapi:/// -b cn=config -s base -LLL \
  olcTLSCACertificateFile olcTLSCertificateFile olcTLSCertificateKeyFile 2>/dev/null
```

Enable the ldaps listener

```bash
sudo sed -i 's|^SLAPD_SERVICES=.*|SLAPD_SERVICES="ldap:/// ldapi:/// ldaps:///"|' /etc/default/slapd
grep ^SLAPD_SERVICES /etc/default/slapd
sudo systemctl restart slapd
sudo ss -tlnp | grep slapd
```

Expected: slapd on `:389` and `:636`.

Verify TLS

```bash
openssl s_client -connect 192.168.2.200:636 -CAfile ~/ldap-tls/ca.crt < /dev/null 2>/dev/null \
  | grep 'Verify return code'

ldapsearch -x -H ldap://192.168.2.200 -b "" -s base supportedExtension | grep 1466.20037

LDAPTLS_CACERT=~/ldap-tls/ca.crt ldapwhoami -x -H ldaps://192.168.2.200 \
  -D "uid=uday,ou=users,dc=palmeto,dc=org" -w 'palmeto@123'
```

Expected:

```
Verify return code: 0 (ok)
supportedExtension: 1.3.6.1.4.1.1466.20037
dn:uid=uday,ou=users,dc=palmeto,dc=org
```

Open the firewall

OpenShift only needs port 636. Allow it from the cluster node network:

```bash
sudo ufw allow from 192.168.100.0/24 to any port 636 proto tcp
sudo ufw status
```

If `ufw` is inactive, make sure SSH is allowed before you enable it:

```bash
sudo ufw allow 22/tcp
sudo ufw enable
```

Local admin work uses `ldap://localhost` and `ldapi:///`, so 389 does not need to be open to the network.

Test from an OpenShift node

The OAuth server pods connect from the cluster network, so test from a node, not only from the LDAP host.

Check the route

```bash
oc debug node/$(oc get nodes -o jsonpath='{.items[0].metadata.name}') -- \
  chroot /host ip route get 192.168.2.200
```

The node must reach LDAP at the same address that appears in the certificate SAN.

Check the port

```bash
oc debug node/$(oc get nodes -o jsonpath='{.items[0].metadata.name}') -- \
  chroot /host bash -c 'timeout 3 bash -c "</dev/tcp/192.168.2.200/636" && echo open || echo closed'
```

Expected: `open`

Check TLS with the CA

`oc debug` does not attach stdin by default, so pass the CA as base64 inside the command:

```bash
CA_B64=$(base64 -w0 ~/ldap-tls/ca.crt)

oc debug node/$(oc get nodes -o jsonpath='{.items[0].metadata.name}') -- \
  chroot /host bash -c "echo $CA_B64 | base64 -d > /tmp/ca.crt; \
  openssl s_client -connect 192.168.2.200:636 -CAfile /tmp/ca.crt < /dev/null 2>&1 \
  | grep -E 'Verify return code|errno|error'"
```

Expected: `Verify return code: 0 (ok)`

Configure OpenShift

Store the CA and bind password

The ConfigMap key must be `ca.crt`. The secret key must be `bindPassword`. Both must live in `openshift-config`.

```bash
oc create configmap ldap-ca --from-file=ca.crt=$HOME/ldap-tls/ca.crt -n openshift-config

oc create secret generic ldap-secret -n openshift-config \
  --from-literal=bindPassword='admin@123'
```

Check for existing identity providers

```bash
oc get oauth cluster -o jsonpath='{.spec.identityProviders[*].name}{"\n"}'
```

The target configuration looks like this:

```yaml
spec:
  identityProviders:
  - name: ldap
    mappingMethod: claim
    type: LDAP
    ldap:
      url: "ldaps://192.168.2.200:636/ou=users,dc=palmeto,dc=org?uid"
      insecure: false
      ca:
        name: ldap-ca
      bindDN: "cn=admin,dc=palmeto,dc=org"
      bindPassword:
        name: ldap-secret
      attributes:
        id: ["dn"]
        preferredUsername: ["uid"]
        name: ["cn"]
        email: ["mail"]
```

The URL format is `ldaps://host:port/<search base>?<login attribute>`. Users type their `uid` at login.

No providers yet (empty output)

```bash
oc patch oauth cluster --type=merge -p '{"spec":{"identityProviders":[{
  "name":"ldap",
  "mappingMethod":"claim",
  "type":"LDAP",
  "ldap":{
    "url":"ldaps://192.168.2.200:636/ou=users,dc=palmeto,dc=org?uid",
    "insecure":false,
    "ca":{"name":"ldap-ca"},
    "bindDN":"cn=admin,dc=palmeto,dc=org",
    "bindPassword":{"name":"ldap-secret"},
    "attributes":{
      "id":["dn"],
      "preferredUsername":["uid"],
      "name":["cn"],
      "email":["mail"]
    }
  }
}]}}'
```

Other providers exist (for example `htpasswd`)

A merge patch replaces the whole list and would delete them. Append instead:

```bash
oc patch oauth cluster --type=json -p '[{"op":"add","path":"/spec/identityProviders/-","value":{
  "name":"ldap",
  "mappingMethod":"claim",
  "type":"LDAP",
  "ldap":{
    "url":"ldaps://192.168.2.200:636/ou=users,dc=palmeto,dc=org?uid",
    "insecure":false,
    "ca":{"name":"ldap-ca"},
    "bindDN":"cn=admin,dc=palmeto,dc=org",
    "bindPassword":{"name":"ldap-secret"},
    "attributes":{
      "id":["dn"],
      "preferredUsername":["uid"],
      "name":["cn"],
      "email":["mail"]
    }
  }
}}]'
```

An `ldap` provider already exists (for example an old insecure one)

Update it in place. Do not rename it and do not change its `id` attribute. OpenShift names each identity `<provider>:<id>`, so either change breaks users who already logged in.

Find its index first (the first provider is `0`):

```bash
oc get oauth cluster -o jsonpath='{range .spec.identityProviders[*]}{.name}{"\n"}{end}' | cat -n
```

Then patch only the fields that change (index `0` shown):

```bash
oc patch oauth cluster --type=json -p '[
  {"op":"replace","path":"/spec/identityProviders/0/ldap/url","value":"ldaps://192.168.2.200:636/ou=users,dc=palmeto,dc=org?uid"},
  {"op":"replace","path":"/spec/identityProviders/0/ldap/insecure","value":false},
  {"op":"add","path":"/spec/identityProviders/0/ldap/ca","value":{"name":"ldap-ca"}}
]'
```

Watch the rollout

```bash
oc get co authentication -w
```

`-w` keeps watching and never returns on its own. Press Ctrl+C once `PROGRESSING` goes from `True` back to `False` (usually 2 to 4 minutes).

Log in as an LDAP user

Trust the cluster certificates

`oc login` talks to two endpoints: the API server and the OAuth route `oauth-openshift.apps.<cluster>`. The OAuth route uses the default ingress certificate, which a separate ingress CA signs. Without that CA, login fails with `x509: certificate signed by unknown authority`.

The instructor builds a bundle with both CAs, using an admin kubeconfig:

```bash
cd ~/ldap-tls

oc config view --minify --raw \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d > api-ca.crt

oc get configmap default-ingress-cert -n openshift-config-managed \
  -o jsonpath='{.data.ca-bundle\.crt}' > ingress-ca.crt

cat api-ca.crt ingress-ca.crt > ocp-ca-bundle.crt
```

Share `ocp-ca-bundle.crt` with trainees. It contains only public certificates.

Log in

Note your admin context first so you can return to it:

```bash
oc config current-context
```

Log in as `uday`:

```bash
oc login -u uday -p 'palmeto@123' \
  --certificate-authority=ocp-ca-bundle.crt \
  https://api.ocp4.palmeto.org:6443
oc whoami
```

Expected: `Login successful.` then `uday`.

`oc login` saves the CA to `~/.kube/config` only after a successful login. After that, the flag is no longer needed.

For a quick lab test without the bundle, use a separate kubeconfig so your admin context stays untouched:

```bash
KUBECONFIG=~/.kube/uday oc login -u uday -p 'palmeto@123' \
  --insecure-skip-tls-verify=true https://api.ocp4.palmeto.org:6443
```

Switch back to admin and check the identity

```bash
oc config use-context <admin-context-from-7.2>
oc whoami
oc get identity | grep ldap
```

Example output:

```
ldap:dWlkPXVkYXksb3U9dXNlcnMsZGM9cGFsbWV0byxkYz1vcmc   ldap   dWlkPXVkYXksb3U9dXNlcnMsZGM9cGFsbWV0byxkYz1vcmc   uday   01f3d7cb-...
```

OpenShift base64-encodes the DN in the identity name. Decode it:

```bash
echo 'dWlkPXVkYXksb3U9dXNlcnMsZGM9cGFsbWV0byxkYz1vcmc' | base64 -d; echo
```

Output: `uid=uday,ou=users,dc=palmeto,dc=org`

Grant roles

OpenShift creates the `User` object on first login. Grant cluster roles after that:

```bash
oc adm policy add-cluster-role-to-user cluster-admin jegan
oc adm policy add-role-to-user edit uday -n <project>
```

If a `root` user ever logged in through LDAP before you removed it, delete its OpenShift objects too:

```bash
oc get identity | grep -w root
oc delete user root
oc delete identity <identity-name-from-above>
```

Change the admin (root DN) password

`ldappasswd` against `cn=admin,dc=palmeto,dc=org` fails with `No such object (32)`, because the root DN is not a directory entry. Change `olcRootPW` in `cn=config` instead. The `ldapi:///` socket works even if the current admin password is unknown.

Replace `NewAdminPassword` with the new value:

```bash
sudo -v
HASH=$(slappasswd -s 'NewAdminPassword')
echo "$HASH"

printf 'dn: olcDatabase={1}mdb,cn=config\nchangetype: modify\nreplace: olcRootPW\nolcRootPW: %s\n' "$HASH" \
  | sudo ldapmodify -Y EXTERNAL -H ldapi:///

LDAPTLS_CACERT=~/ldap-tls/ca.crt ldapwhoami -x -H ldaps://192.168.2.200 \
  -D "cn=admin,dc=palmeto,dc=org" -w 'NewAdminPassword'
```

`echo "$HASH"` must print a line starting with `{SSHA}`. Only after `ldapwhoami` succeeds, update the OpenShift secret:

```bash
oc create secret generic ldap-secret -n openshift-config \
  --from-literal=bindPassword='NewAdminPassword' --dry-run=client -o yaml | oc apply -f -

oc get co authentication -w
```

If the two passwords disagree, the OAuth server cannot bind and every LDAP login fails.

Check the current value at any time:

```bash
sudo ldapsearch -Y EXTERNAL -H ldapi:/// -b cn=config -LLL \
  '(olcRootDN=cn=admin,dc=palmeto,dc=org)' olcRootPW 2>/dev/null
```

To reset one user's password:

```bash
LDAPTLS_CACERT=~/ldap-tls/ca.crt ldappasswd -x -H ldaps://192.168.2.200 \
  -D "cn=admin,dc=palmeto,dc=org" -w 'admin@123' \
  -s 'palmeto@123' "uid=uday,ou=users,dc=palmeto,dc=org"
```

Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `openssl x509`: `Could not read certificate from <stdin>` | `s_client` failed and `2>/dev/null` hid the error | Rerun `openssl s_client` without `2>/dev/null` and read the error |
| `nc -zv host 636`: `Connection refused` | slapd not listening on 636 | Part 3.3 and 3.4, then `sudo ss -tlnp \| grep slapd` |
| Connection to 636 times out | Firewall drops the traffic | Part 4 |
| `STARTTLS failed, LDAP Result Code: 2` | No certificate loaded in slapd | Part 3 |
| `ldapmodify` returns `error (80)` | slapd cannot read the key or certificate | Check owner `root:openldap` and mode `640` on `ldap.key`; check `sudo journalctl -k \| grep -i apparmor` |
| `ldapadd`: `Already exists (68)` | Entry was imported earlier | Use `ldapadd -c`; reset passwords with the loop in 2.3 |
| User bind fails with the "right" password | Stored `userPassword` hash came from a different string (for example a hard-coded hash) | Reset with `ldappasswd` (Part 2.3 or Part 8) |
| `ldappasswd` on `cn=admin`: `No such object (32)` | Root DN is not a directory entry | Part 8 |
| Admin bind fails after a password change | Placeholder text or wrong hash in `olcRootPW` | Check `olcRootPW` (Part 8) and set it again |
| `oc debug ... < file` prints nothing | `oc debug` did not attach stdin | Use the base64 method in Part 5.3 |
| `oc login`: `x509: certificate signed by unknown authority` | Client does not trust the ingress CA on the OAuth route | Part 7.1 |
| `oc login`: `401 Unauthorized` | Wrong user password or bind password | Test with `ldapwhoami` as the user and as `cn=admin`; check OAuth logs |
| Login worked before, fails after config change | Provider renamed or `id` attribute changed | Restore the original name and `id`, or delete the stale `User` and `Identity` objects |
| `oc get co authentication -w` never returns | `-w` watches indefinitely | Press Ctrl+C |

OAuth server logs:

```bash
oc logs -n openshift-authentication -l app=oauth-openshift --tail=50 --all-containers \
  | grep -iE 'ldap|error'
```

Common log messages:

| Log message | Meaning |
|---|---|
| `LDAP Result Code 49 "Invalid Credentials"` | Wrong user password or wrong bind password |
| `LDAP Result Code 32 "No Such Object"` | Search base in the URL does not exist |
| `x509` | CA in `ldap-ca` does not match the LDAP server certificate, or the SAN does not match the URL host |

Hardening beyond the lab

- Replace the `cn=admin` bind with a read-only account limited to `ou=users`, or remove `bindDN` and `bindPassword` if anonymous search is acceptable. The directory admin password in `openshift-config` gives anyone who can read that secret full write access to LDAP.
- Restrict port 636 to the cluster node network and admin workstations only.
- Reissue `ldap.crt` before it expires (825 days) with the same CA. The OpenShift ConfigMap does not change as long as the CA stays the same.
- Sync `ou=groups` into OpenShift groups with `oc adm groups sync` and grant roles to groups instead of individual users.
