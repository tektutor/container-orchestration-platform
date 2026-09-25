# Day 5

## Info - Red Hat Openshift Access Details
<pre>
- I have replaced Kubernetes cluster with Red Hat Openshift in server1(192.168.2.200) and server2(192.168.2.201)
- You can find the Red Hat Openshift access details on a file named openshift.txt in your home directory
- For instance, cat /home/jegan/openshift.txt
</pre>

You can check if you are able to access Openshift cluster
```
oc version
kubectl version

oc get nodes
kubectl get nodes

oc whoami --show-server
oc whoami --show-console
```

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

Install OpenLDAP in Ubuntu (Just for your reference, please don't attempt this in our lab environment )
```
sudo apt update
sudo apt install slapd ldap-utils -y
```
Configuring LDAP Server
<pre>
sudo dpkg-reconfigure slapd  
</pre>

How to respond when the above commands prompts your response ?
<pre>
Omit OpenLDAP server configuration?	No
DNS domain name?	palmeto.org
Organization name?	Palmeto
Administrator password?	palmeto@123
Database backend?	MDB
Remove database when slapd is purged?	No
Move old database?	Yes
</pre>

Check if LDAP Server is running
```
sudo systemctl status slapd
sudo ss -tulnp | grep :389
```

Check if LDAP search works
```
ldapsearch -x -LLL -H ldap://localhost -b dc=palmeto,dc=org
```

Create a file named base.ldif
<pre>
dn: ou=users,dc=palmeto,dc=org
objectClass: organizationalUnit
ou: users

dn: ou=groups,dc=palmeto,dc=org
objectClass: organizationalUnit
ou: groups  
</pre>

Apply the above configuration
```
ldapadd -x -D "cn=admin,dc=palmeto,dc=org" -W -f base.ldif
```

Add LDAP users, creat a file named users.ldif
<pre>
dn: uid=jegan,ou=users,dc=palmeto,dc=org
objectClass: inetOrgPerson
uid: jegan
sn: Swaminathan
cn: Jeganathan Swaminathan
mail: jegan@tektutor.org
userPassword: palmeto@123

dn: cn=admins,ou=groups,dc=palmeto,dc=org
objectClass: groupOfNames
cn: admins
member: uid=jegan,ou=users,dc=palemto,dc=org  
</pre>

Create the user
```
ldapadd -x -D "cn=admin,dc=palmeto,dc=org" -W -f users.ldif
```

Search users
```
ldapsearch -x -LLL -b "ou=users,dc=palmeto,dc=org"
```

Search groups
```
ldapsearch -x -LLL -b "ou=groups,dc=palmeto,dc=org"
```

Configure Ubuntu firewall to allow LDAP
```
sudo ufw allow 389
```

LDAP Server details
<pre>
Base DN : dc=palmeto,dc=org
Admin DN: cn=admin,dc=palmeto,dc=org
User DN	: uid=jegan,ou=users,dc=palmeto,dc=org
Group DN: cn=admins,ou=groups,dc=palmeto,dc=org
Password: palmeto@123
</pre>

Script to extract existing linux users and add them as users in LDAP server
```
#!/bin/bash

# Hashed value of "palmeto@123" using slappasswd
LDAP_PASS="{SSHA}Xky2OjkOZt5U4eebv9rWsk9VUYR6Fa9Z"

# Output LDIF file
OUTPUT_FILE="palmeto-ldap-users.ldif"
> "$OUTPUT_FILE"

for user in $(ls -l /home | awk '{print $3}' | sort -u); do
    # Get user details from /etc/passwd
    IFS=':' read -r username _ uid gid full home shell <<< "$(getent passwd "$user")"

    # Skip if user not found
    [ -z "$username" ] && continue

    # Set default values for cn and sn
    if [ -z "$full" ]; then
        cn="$username"
        sn="user"
    else
        cn=$(echo "$full" | cut -d' ' -f1)
        sn=$(echo "$full" | cut -d' ' -f2)
        [ -z "$cn" ] && cn="$username"
        [ -z "$sn" ] && sn="user"
    fi

    # Set email from username
    email="${username}@palmeto.org"

    cat <<EOF >> "$OUTPUT_FILE"
dn: uid=$username,ou=users,dc=palmeto,dc=org
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
cn: $cn
sn: $sn
uid: $username
uidNumber: $uid
gidNumber: $gid
homeDirectory: $home
loginShell: $shell
mail: $email
userPassword: $LDAP_PASS

EOF
done

echo "LDIF file generated: $OUTPUT_FILE"
```

In case you wish to delete existing users from LDAP server before adding the below users
```
ldapsearch -LLL -x -D "cn=admin,dc=palmeto,dc=org" -w 'palmeto@123' -b "ou=users,dc=palmeto,dc=org" "(objectClass=inetOrgPerson)" dn \
  | grep '^dn:' \
  | sed 's/^dn: //' \
  | xargs -n1 ldapdelete -x -D "cn=admin,dc=palmeto,dc=org" -w 'palmeto@123'
```

Let's add the ldap users now
```
ldapadd -x -D "cn=admin,dc=palmeto,dc=org" -W -f palmeto-ldap-users.ldif
```

Integrate OpenLDAP with OpenShift v4.22 (ldap-idp.yaml)
```
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: ldap
    mappingMethod: claim
    type: LDAP
    ldap:
      attributes:
        id:
        - dn
        preferredUsername:
        - uid
        name:
        - cn
        email:
        - mail
      bindDN: "cn=admin,dc=palmeto,dc=org"
      bindPassword:
        name: ldap-secret
      insecure: true
      url: "ldap://192.168.2.200:389/ou=people,dc=palmeto,dc=org?uid"
```

Create LDAP bind password secret
```
oc create secret generic ldap-secret \
  --from-literal=bindPassword=root@123 \
  -n openshift-config
```

Create LDAP server certificate
```
# Get LDAP server certificate
openssl s_client -connect 192.168.2.200:389 -showcerts < /dev/null 2>/dev/null | openssl x509 -outform PEM > ldap-ca.crt

# Create configmap
oc create configmap ldap-ca \
  --from-file=ca.crt=ldap-ca.crt \
  -n openshift-config
```

Create the LDAP Identify Provider Configuration
```
oc apply -f ldap-idp.yaml
```

Create ClusterRoleBinding for LDAP users
```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ldap-cluster-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: User
  name: jegan
```
```
oc apply -f /tmp/ldap-admin-binding.yml
```

Verify the integration
```
#Update password
ldappasswd -x -H ldap://192.168.2.200:389 -D "cn=admin,dc=palmeto,dc=org" -W -S "uid=jegan,ou=people,dc=palmeto,dc=org"

# Test authentication after password update
ldapwhoami -x -H ldap://192.168.2.200:389 -D "uid=jegan,ou=people,dc=palmeto,dc=org" -W
# Enter password: palmeto@123

#Alternate approach
slappasswd -s "palmeto@123"

# Check OAuth configuration
oc get oauth cluster -o yaml | grep -A 20 "ldap:"

# Check authentication operators
oc get pods -n openshift-authentication-operator

# If still showing ldaps://, reapply the configuration
oc apply -f /tmp/ldap-non-ssl.yaml

# Wait for OAuth configuration to propagate (2-3 minutes)
sleep 180

# Try OpenShift login
oc login --username=jegan --password='palmeto@123' --insecure-skip-tls-verify

# In another terminal, monitor authentication attempts
oc logs -n openshift-authentication deployment/oauth-openshift -f | grep -E "(jegan|ldap|bind|authentication|error)"
```

## Lab - JWT ( JSON Web Token )

Note
<pre>
- Authentication happens once, when you log in with a password, LDAP bind or client certificate
- The issuer then writes the outcome into a signed JWT: "this is uday, verified at 07:30, valid until 08:30." 
- Every later request shows that token as proof
- Think of the difference between checking someone's ID at the front desk and the visitor badge you hand 
  them afterwards. The JWT is the badge.
</pre>

A JSON Web Token (JWT) has three base64url-encoded parts separated by dots
<pre>
<header>.<payload>.<signature>
</pre>

<pre>
- Header - signing algorithm (alg) and key ID (kid)
- Payload- claims such as issuer (iss), subject (sub), audience (aud) and expiry (exp)
- Signature - RSA signature over <header>.<payload>
- The payload is signed, not encrypted
- Anyone holding the token can read every claim. 
- Only the private key holder can create a valid signature
</pre>

Replace `jegan` with your own name in every command, for example `uday-shop`

Let's create a project
```
oc new-project jegan-shop
oc create serviceaccount inventory-api -n jegan-shop
oc create serviceaccount order-service -n jegan-shop
oc adm policy add-cluster-role-to-user system:auth-delegator -z inventory-api -n jegan-shop
```

Deploy inventory-api - a small Python server that sends a TokenReview for every request
```
cat <<'EOF' | oc apply -n jegan-shop -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: inventory-api-code
data:
  server.py: |
    import json, ssl, urllib.request
    from http.server import BaseHTTPRequestHandler, HTTPServer

    SA = "/var/run/secrets/kubernetes.io/serviceaccount/"
    NAMESPACE = open(SA + "namespace").read().strip()
    ALLOWED = "system:serviceaccount:%s:order-service" % NAMESPACE
    CTX = ssl.create_default_context(cafile=SA + "ca.crt")

    def who_is(token):
        # Ask the API server: who owns this token, and is it meant for us?
        body = json.dumps({
            "apiVersion": "authentication.k8s.io/v1",
            "kind": "TokenReview",
            "spec": {"token": token, "audiences": ["inventory-api"]},
        }).encode()
        req = urllib.request.Request(
            "https://kubernetes.default.svc/apis/authentication.k8s.io/v1/tokenreviews",
            data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + open(SA + "token").read().strip()})
        with urllib.request.urlopen(req, context=CTX) as r:
            return json.load(r)["status"]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            auth = self.headers.get("Authorization", "")
            status = who_is(auth[7:]) if auth.startswith("Bearer ") else {}
            user = status.get("user", {}).get("username", "")
            if not status.get("authenticated"):
                code, msg = 401, "rejected: unknown caller\n"
            elif user != ALLOWED:
                code, msg = 403, "rejected: %s is not allowed\n" % user
            else:
                code, msg = 200, "stock reserved for %s\n" % user
            self.send_response(code)
            self.end_headers()
            self.wfile.write(msg.encode())

    HTTPServer(("", 8080), Handler).serve_forever()
---
apiVersion: v1
kind: Pod
metadata:
  name: inventory-api
  labels:
    app: inventory-api
spec:
  serviceAccountName: inventory-api
  containers:
  - name: app
    image: registry.access.redhat.com/ubi9/python-311
    command: ["python3", "-u", "/app/server.py"]
    ports:
    - containerPort: 8080
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      runAsNonRoot: true
      seccompProfile:
        type: RuntimeDefault
    volumeMounts:
    - name: code
      mountPath: /app
  volumes:
  - name: code
    configMap:
      name: inventory-api-code
---
apiVersion: v1
kind: Service
metadata:
  name: inventory-api
spec:
  selector:
    app: inventory-api
  ports:
  - port: 8080
EOF

oc wait --for=condition=Ready pod/inventory-api -n jegan-shop --timeout=300s
```

Deploy order-service with a token meant for inventory-api
```
cat <<'EOF' | oc apply -n jegan-shop -f -
apiVersion: v1
kind: Pod
metadata:
  name: order-service
spec:
  serviceAccountName: order-service
  containers:
  - name: app
    image: registry.access.redhat.com/ubi9/ubi-minimal
    command: ["tail", "-f", "/dev/null"]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      runAsNonRoot: true
      seccompProfile:
        type: RuntimeDefault
    volumeMounts:
    - name: inventory-token
      mountPath: /var/run/secrets/tokens
      readOnly: true
  volumes:
  - name: inventory-token
    projected:
      sources:
      - serviceAccountToken:
          audience: inventory-api
          expirationSeconds: 600
          path: inventory-api-token
EOF

oc wait --for=condition=Ready pod/order-service -n jegan-shop --timeout=120s
```

order-service calls inventory-api (allowed)
```
oc exec -n jegan-shop order-service -- sh -c \
  'curl -s -H "Authorization: Bearer $(cat /var/run/secrets/tokens/inventory-api-token)" http://inventory-api:8080/'
```
Expected
<pre>
stock reserved for system:serviceaccount:jegan-shop:order-service
</pre>

Wrong audience and wrong caller (both rejected)
```
# Right caller, but the token is meant for the OpenShift API, not inventory-api
oc exec -n jegan-shop order-service -- sh -c \
  'curl -s -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" http://inventory-api:8080/'

# Right audience, but the token belongs to a different service account
oc exec -n jegan-shop order-service -- curl -s \
  -H "Authorization: Bearer $(oc create token default -n jegan-shop --audience=inventory-api)" \
  http://inventory-api:8080/
```

Expected
<pre>
rejected: unknown caller
rejected: system:serviceaccount:jegan-shop:default is not allowed
</pre>

To watch the requests arrive on the server side:
```
oc logs -n jegan-shop inventory-api
```

Clean up
```
oc adm policy remove-cluster-role-from-user system:auth-delegator -z inventory-api -n jegan-shop
oc delete project jegan-shop
```
