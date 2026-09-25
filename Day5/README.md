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

Expected output
<pre>
palmeto@palmeto:~$ kubectl version
Client Version: v1.35.2
Kustomize Version: v5.7.1
Server Version: v1.35.6

palmeto@palmeto:~$ oc version
Client Version: 4.22.15
Kustomize Version: v5.7.1
Server Version: 4.22.15
Kubernetes Version: v1.35.6

palmeto@palmeto:~$ oc get nodes
NAME                        STATUS   ROLES                  AGE   VERSION
master01.ocp4.palmeto.org   Ready    control-plane,master   13h   v1.35.6
master02.ocp4.palmeto.org   Ready    control-plane,master   13h   v1.35.6
master03.ocp4.palmeto.org   Ready    control-plane,master   13h   v1.35.6
worker01.ocp4.palmeto.org   Ready    worker                 12h   v1.35.6
worker02.ocp4.palmeto.org   Ready    worker                 12h   v1.35.6
worker03.ocp4.palmeto.org   Ready    worker                 12h   v1.35.6
</pre>

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
```
<header>.<payload>.<signature>
```

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

## Lab: X.509 Certificates

In this lab you create your own Certificate Authority (CA), issue a server certificate, inspect it, verify it, and use it in a real TLS connection. You also see the three most common certificate errors.

Replace `jegan` with your own name in every command, for example `uday-x509-lab` and `web.uday.lab`.

You need `openssl` and `curl`. Ubuntu 24.04 and RHEL 9 have both.

Step 1: Create a working folder

```
mkdir -p ~/jegan-x509-lab && cd ~/jegan-x509-lab
```

Step 2: Create your own CA

A CA is a key pair plus a self-signed certificate. Its only job is to sign other certificates.

```
openssl req -x509 -new -nodes -newkey rsa:4096 -days 3650 \
  -keyout ca.key -out ca.crt -subj "/CN=Jegan Lab CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign"
```

Inspect it:
```
openssl x509 -in ca.crt -noout -subject -issuer -dates -ext basicConstraints
```

Expected
<pre>
subject=CN = Jegan Lab CA
issuer=CN = Jegan Lab CA
notBefore=Sep 25 03:55:15 2026 GMT
notAfter=Sep 22 03:55:15 2036 GMT
X509v3 Basic Constraints: critical
    CA:TRUE
</pre>

`subject` and `issuer` are the same, so the certificate is self-signed. `CA:TRUE` allows it to sign other certificates.

Step 3: Create a key and a certificate request for the server

The server creates its own private key. It sends only a Certificate Signing Request (CSR) to the CA. The private key never leaves the server.

```
openssl req -new -nodes -newkey rsa:2048 \
  -keyout server.key -out server.csr -subj "/CN=web.jegan.lab"
```

Inspect the CSR:
```
openssl req -in server.csr -noout -subject -verify
```

Expected
<pre>
Certificate request self-signature verify OK
subject=CN = web.jegan.lab
</pre>

Step 4: Sign the request with your CA

Browsers and `curl` check the Subject Alternative Name (SAN), not the CN. List every name and IP clients will use to reach the server.

```
cat > server.ext <<'EOF'
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:web.jegan.lab, DNS:localhost, IP:127.0.0.1
EOF

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 -extfile server.ext
```

Expected
<pre>
Certificate request self-signature ok
subject=CN = web.jegan.lab
</pre>

Step 5: Inspect the server certificate

```
openssl x509 -in server.crt -noout -subject -issuer -serial -dates \
  -ext subjectAltName,extendedKeyUsage
```

Expected
<pre>
subject=CN = web.jegan.lab
issuer=CN = Jegan Lab CA
serial=415720894E9D66CEF9019F29B31397E477CB2907
notBefore=Sep 25 03:55:15 2026 GMT
notAfter=Sep 25 03:55:15 2027 GMT
X509v3 Extended Key Usage:
    TLS Web Server Authentication
X509v3 Subject Alternative Name:
    DNS:web.jegan.lab, DNS:localhost, IP Address:127.0.0.1
</pre>

Now `issuer` is your CA, not the server itself.

To see every field, run:
```
openssl x509 -in server.crt -noout -text
```
## Lab: Application Security and Access Control in OpenShift

In this lab you see how OpenShift protects the cluster from applications (Security Context Constraints) and how it controls who can do what inside a project (RBAC).

Replace `jegan` with your own name in every command, for example `uday-app`.

Step 1: Create a project and deploy an application

```
oc new-project jegan-app

oc create deployment web --image=registry.access.redhat.com/ubi9/nginx-124 --port=8080 -n jegan-app
oc expose deployment web --port=8080 -n jegan-app
oc create route edge web --service=web -n jegan-app

oc rollout status deployment/web -n jegan-app
```

`oc create deployment` may print a `PodSecurity` warning. You can ignore it here: OpenShift fills in the missing security settings when it admits the pod.

Test the application through its HTTPS route:
```
curl -sk -o /dev/null -w '%{http_code}\n' https://$(oc get route web -n jegan-app -o jsonpath='{.spec.host}')
```

Expected
<pre>
200
</pre>

`-k` skips certificate verification because the router uses the cluster's own CA. See the X.509 lab to verify it properly.

---

Part A: Application security

Step 2: See which user your application runs as

```
oc exec -n jegan-app deploy/web -- id
```

Expected (the number differs per project)
<pre>
uid=1000680000(1000680000) gid=0(root) groups=0(root),1000680000
</pre>

OpenShift did not use the user from the image. It assigned a random high UID from a range reserved for this project:

```
oc get project jegan-app -o jsonpath='{.metadata.annotations.openshift\.io/sa\.scc\.uid-range}{"\n"}'
```

Expected (similar to)
<pre>
1000680000/10000
</pre>

Every project gets a different range. If an attacker breaks out of a container, they land as a user that owns nothing on the node and nothing in any other project.

Step 3: See which security policy admitted the pod

```
oc get pod -n jegan-app -l app=web \
  -o jsonpath='{.items[0].metadata.annotations.openshift\.io/scc}{"\n"}'
```

Expected
<pre>
restricted-v2
</pre>

`restricted-v2` is the default Security Context Constraint (SCC). It forbids root, drops all Linux capabilities, blocks privilege escalation and host access, and forces the random UID you saw in Step 2.

Step 4: Try to run an application as root

```
cat <<'EOF' | oc apply -n jegan-app -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: root-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: root-test
  template:
    metadata:
      labels:
        app: root-test
    spec:
      containers:
      - name: app
        image: registry.access.redhat.com/ubi9/ubi-minimal
        command: ["tail", "-f", "/dev/null"]
        securityContext:
          runAsUser: 0
EOF
```

Check the result:
```
oc get deployment root-test -n jegan-app
```

Expected
<pre>
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
root-test   0/1     0            0           20s
</pre>

Find out why:
```
oc get events -n jegan-app --field-selector reason=FailedCreate \
  -o custom-columns=MESSAGE:.message | tail -1
```

Expected (shortened)
<pre>
pods "root-test-..." is forbidden: unable to validate against any security context constraint:
... runAsUser: Invalid value: 0: must be in the ranges: [1000680000, 1000689999] ...
</pre>

OpenShift refused to create the pod at all. The request to run as UID 0 never reached a node.

We use a Deployment on purpose. Pods it creates are checked against the permissions of the service account (`default`), which can only use `restricted-v2`. A pod you create directly as `cluster-admin` would be checked against your own permissions and could be admitted.

Remove it:
```
oc delete deployment root-test -n jegan-app
```

Part B: Access control (RBAC)

RBAC answers one question for every request: **can this identity do this verb on this resource in this project?**

- A **Role** lists allowed verbs on resources, such as `get`, `list`, `delete` on `pods`.
- A **RoleBinding** gives a Role to a user, group or service account in one project.

OpenShift ships ready-made roles: `view` (read, except secrets), `edit` (change apps, except RBAC), and `admin` (everything in the project).

In this part you use service accounts as test identities, because every trainee can create them.

Step 5: Create three identities and give them roles

```
oc create serviceaccount viewer -n jegan-app
oc create serviceaccount deployer -n jegan-app
oc create serviceaccount restarter -n jegan-app

oc policy add-role-to-user view -z viewer -n jegan-app
oc policy add-role-to-user edit -z deployer -n jegan-app
```

`restarter` gets a custom role in Step 7.

Step 6: Test what each identity can do

`oc auth can-i --as` asks the API server to check a request as another identity, without running it.

```
SA=system:serviceaccount:jegan-app

oc auth can-i list pods      -n jegan-app --as=$SA:viewer
oc auth can-i delete pods    -n jegan-app --as=$SA:viewer
oc auth can-i get secrets    -n jegan-app --as=$SA:viewer

oc auth can-i delete pods    -n jegan-app --as=$SA:deployer
oc auth can-i get secrets    -n jegan-app --as=$SA:deployer
oc auth can-i create rolebindings -n jegan-app --as=$SA:deployer

oc auth can-i list pods      -n default   --as=$SA:deployer
```

Expected
<pre>
yes
no
no
yes
yes
no
no
</pre>

What this shows:
- `view` can read pods but **cannot read secrets**, so you can safely give it to auditors and support teams.
- `edit` can change applications and read secrets, but **cannot grant access** to anyone else.
- Both roles apply only inside `jegan-app`. The last check against `default` fails.

Step 7: Create a least-privilege role

Suppose a monitoring job only needs to restart stuck pods. `edit` would give it far too much. Create a role with exactly what it needs:

```
oc create role pod-restarter --verb=get,list,delete --resource=pods -n jegan-app
oc create rolebinding restarter-binding --role=pod-restarter \
  --serviceaccount=jegan-app:restarter -n jegan-app
```

Test it:
```
oc auth can-i delete pods         -n jegan-app --as=$SA:restarter
oc auth can-i delete deployments  -n jegan-app --as=$SA:restarter
oc auth can-i get secrets         -n jegan-app --as=$SA:restarter
```

Expected
<pre>
yes
no
no
</pre>

Step 8: Use the identity for real

`can-i` only asks. Now send real requests with the service account's token:

```
TOKEN=$(oc create token restarter -n jegan-app)

oc --token="$TOKEN" delete pod -l app=web -n jegan-app
oc --token="$TOKEN" get secrets -n jegan-app
oc --token="$TOKEN" delete deployment web -n jegan-app
```

Expected (pod name differs)
<pre>
pod "web-6d8f7c9b5d-x2kqp" deleted
Error from server (Forbidden): secrets is forbidden: User "system:serviceaccount:jegan-app:restarter" cannot list resource "secrets" in API group "" in the namespace "jegan-app"
Error from server (Forbidden): deployments.apps "web" is forbidden: User "system:serviceaccount:jegan-app:restarter" cannot delete resource "deployments" in API group "apps" in the namespace "jegan-app"
</pre>

The deployment creates a replacement pod, so the application keeps running:
```
oc get pods -n jegan-app -l app=web
```

Step 9: Review and revoke access

List who has which role in the project:
```
oc get rolebindings -n jegan-app -o wide
```

Ask the reverse question: who can delete pods here?
```
oc adm policy who-can delete pods -n jegan-app
```

Look for `restarter` and `deployer` in the service account list.

Revoke `restarter` and check again:
```
oc delete rolebinding restarter-binding -n jegan-app
oc auth can-i delete pods -n jegan-app --as=$SA:restarter
oc --token="$TOKEN" delete pod -l app=web -n jegan-app
```

Expected
<pre>
no
Error from server (Forbidden): pods "web-..." is forbidden: User "system:serviceaccount:jegan-app:restarter" cannot delete resource "pods" ...
</pre>


The token is still valid, but it no longer grants anything. RBAC is checked on every request, 
so revoking a binding takes effect immediately.


Step 10: Clean up

```
oc delete project jegan-app
unset SA TOKEN
```
Summary

| Control | Question it answers | What you saw |
|---|---|---|
| SCC (`restricted-v2`) | What may this **application** do on the node? | Random non-root UID; a root container was refused |
| Role / RoleBinding | What may this **identity** do in this project? | `view`, `edit` and a custom role gave three different sets of rights |
| `oc auth can-i` | Would this request be allowed? | Test access without making changes |
| `oc adm policy who-can` | Who is allowed to do this? | Audit access from the resource side |

| Good practice | Why |
|---|---|
| Build images that run as any non-root UID | They work under `restricted-v2` without extra SCCs |
| Never grant `anyuid` or `privileged` to fix a failing image | Fix the image instead; those SCCs remove the node protection |
| Give each application its own service account | You can grant and revoke its access separately |
| Start from `view` or a custom role, not `edit` or `admin` | Least privilege limits the damage from a stolen token |
| Give `view` instead of `edit` to people who only need to look | `view` hides secrets |
Step 6: Verify the certificate

Check that your CA signed it:
```
openssl verify -CAfile ca.crt server.crt
```

Expected
<pre>
server.crt: OK
</pre>

Without the CA, verification fails, because nobody vouches for the certificate:
```
openssl verify server.crt
```

Expected
<pre>
CN = web.jegan.lab
error 20 at 0 depth lookup: unable to get local issuer certificate
error server.crt: verification failed
</pre>

Check that the certificate and key belong together. Both hashes must match:
```
openssl x509 -in server.crt -noout -pubkey | sha256sum
openssl pkey -in server.key -pubout | sha256sum
```

A mismatch here is a common reason a web server refuses to start after a certificate renewal.

Step 7: Check the expiry date

`-checkend` takes seconds and tells you whether the certificate expires within that time.

```
# Does it expire within 1 day?
openssl x509 -in server.crt -noout -checkend 86400

# Does it expire within 1 year?
openssl x509 -in server.crt -noout -checkend 31536000
```

Expected
<pre>
Certificate will not expire
Certificate will expire
</pre>

The exit code is `0` for "will not expire" and `1` for "will expire", so you can use it in monitoring scripts.

Step 8: Use the certificate in a real HTTPS server

Start a test HTTPS server on port 8443 in the background:
```
openssl s_server -accept 8443 -cert server.crt -key server.key -www -quiet >/dev/null 2>&1 &
```

**Test 1: client trusts your CA and uses a name from the SAN (success)**
```
openssl s_client -connect localhost:8443 -CAfile ca.crt -verify_hostname localhost \
  </dev/null 2>/dev/null | grep -m1 'Verify return code'

curl -sS -o /dev/null -w '%{http_code}\n' --cacert ca.crt https://localhost:8443/
```

Expected
<pre>
Verify return code: 0 (ok)
200
</pre>

**Test 2: client does not trust your CA (fails)**
```
openssl s_client -connect localhost:8443 </dev/null 2>/dev/null | grep -m1 'Verify return code'

curl -sS -o /dev/null https://localhost:8443/
```

Expected
<pre>
Verify return code: 21 (unable to verify the first certificate)
curl: (60) SSL certificate problem: unable to get local issuer certificate
</pre>

**Test 3: client trusts your CA but uses a name not in the SAN (fails)**
```
openssl s_client -connect localhost:8443 -CAfile ca.crt -verify_hostname other.jegan.lab \
  </dev/null 2>/dev/null | grep -m1 'Verify return code'

curl -sS -o /dev/null --cacert ca.crt \
  --resolve other.jegan.lab:8443:127.0.0.1 https://other.jegan.lab:8443/
```

Expected
<pre>
Verify return code: 62 (hostname mismatch)
curl: (60) SSL: no alternative certificate subject name matches target host name 'other.jegan.lab'
</pre>

`--resolve` points the name at 127.0.0.1 without editing `/etc/hosts`.

Stop the test server:
```
kill %1
```
Step 9 (optional): Inspect real OpenShift certificates

Use the same commands on a live cluster. Change the cluster domain to match yours.

The API server certificate:
```
openssl s_client -connect api.ocp4.palmeto.org:6443 </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

The router (ingress) certificate, which serves every route:
```
openssl s_client -connect console-openshift-console.apps.ocp4.palmeto.org:443 \
  -servername console-openshift-console.apps.ocp4.palmeto.org </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Look for:
- `issuer`: on a default install, an internal OpenShift signer, not a public CA
- `subjectAltName`: the router certificate holds a wildcard such as `DNS:*.apps.ocp4.palmeto.org`, so one certificate covers every route
- `notAfter`: when it expires

`-servername` sends the host name during the handshake (SNI). The router uses it to pick the right certificate, so leave it out and you may get a different one.


Step 10: Clean up
```
cd ~ && rm -rf ~/jegan-x509-lab
```

Summary

| File | What it is | Share it? |
|---|---|---|
| `ca.key` | CA private key | Never. Anyone with it can issue trusted certificates |
| `ca.crt` | CA certificate | Yes. Clients need it to trust your server |
| `server.key` | Server private key | Never. It stays on the server |
| `server.csr` | Signing request | Yes, to the CA. Not needed after signing |
| `server.crt` | Server certificate | Yes. The server sends it to every client |

| Error | Meaning | Fix |
|---|---|---|
| `unable to get local issuer certificate` (20 or 21) | Client does not trust the issuing CA | Give the client `ca.crt` |
| `hostname mismatch` (62), `no alternative certificate subject name matches` | Name the client used is not in the SAN | Reissue with the name added to `subjectAltName` |
| `certificate has expired` (10) | `notAfter` has passed | Reissue and redeploy; monitor with `-checkend` |

## Lab: Application Security and Access Control in OpenShift

<pre>
- In this lab you see how OpenShift protects the cluster from applications (Security Context Constraints) 
  and how it controls who can do what inside a project (RBAC).
</pre>

Replace `jegan` with your own name in every command, for example `uday-app`.

Step 1: Create a project and deploy an application

```
oc new-project jegan-app

oc create deployment web --image=registry.access.redhat.com/ubi9/nginx-124 --port=8080 -n jegan-app
oc expose deployment web --port=8080 -n jegan-app
oc create route edge web --service=web -n jegan-app

oc rollout status deployment/web -n jegan-app
```

`oc create deployment` may print a `PodSecurity` warning. You can ignore it here: OpenShift fills in the missing security settings when it admits the pod.

Test the application through its HTTPS route:
```
curl -sk -o /dev/null -w '%{http_code}\n' https://$(oc get route web -n jegan-app -o jsonpath='{.spec.host}')
```

Expected
<pre>
200
</pre>

`-k` skips certificate verification because the router uses the cluster's own CA. See the X.509 lab to verify it properly.

Part A: Application security

Step 2: See which user your application runs as

```
oc exec -n jegan-app deploy/web -- id
```

Expected (the number differs per project)
<pre>
uid=1000680000(1000680000) gid=0(root) groups=0(root),1000680000
</pre>

OpenShift did not use the user from the image. It assigned a random high UID from a range reserved for this project:

```
oc get project jegan-app -o jsonpath='{.metadata.annotations.openshift\.io/sa\.scc\.uid-range}{"\n"}'
```

Expected (similar to)
<pre>
1000680000/10000
</pre>

Every project gets a different range. If an attacker breaks out of a container, they land as a user that owns nothing on the node and nothing in any other project.

Step 3: See which security policy admitted the pod

```
oc get pod -n jegan-app -l app=web \
  -o jsonpath='{.items[0].metadata.annotations.openshift\.io/scc}{"\n"}'
```

Expected
<pre>
restricted-v2
</pre>

`restricted-v2` is the default Security Context Constraint (SCC). It forbids root, drops all Linux capabilities, blocks privilege escalation and host access, and forces the random UID you saw in Step 2.

Step 4: Try to run an application as root

```
cat <<'EOF' | oc apply -n jegan-app -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: root-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: root-test
  template:
    metadata:
      labels:
        app: root-test
    spec:
      containers:
      - name: app
        image: registry.access.redhat.com/ubi9/ubi-minimal
        command: ["tail", "-f", "/dev/null"]
        securityContext:
          runAsUser: 0
EOF
```

Check the result:
```
oc get deployment root-test -n jegan-app
```

Expected
<pre>
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
root-test   0/1     0            0           20s
</pre>

Find out why:
```
oc get events -n jegan-app --field-selector reason=FailedCreate \
  -o custom-columns=MESSAGE:.message | tail -1
```

Expected (shortened)
<pre>
pods "root-test-..." is forbidden: unable to validate against any security context constraint:
... runAsUser: Invalid value: 0: must be in the ranges: [1000680000, 1000689999] ...
</pre>

OpenShift refused to create the pod at all. The request to run as UID 0 never reached a node.

We use a Deployment on purpose. Pods it creates are checked against the permissions of the service account (`default`), which can only use `restricted-v2`. A pod you create directly as `cluster-admin` would be checked against your own permissions and could be admitted.

Remove it:
```
oc delete deployment root-test -n jegan-app
```

Part B: Access control (RBAC)

RBAC answers one question for every request: **can this identity do this verb on this resource in this project?**

- A **Role** lists allowed verbs on resources, such as `get`, `list`, `delete` on `pods`.
- A **RoleBinding** gives a Role to a user, group or service account in one project.

OpenShift ships ready-made roles: `view` (read, except secrets), `edit` (change apps, except RBAC), and `admin` (everything in the project).

In this part you use service accounts as test identities, because every trainee can create them.

Step 5: Create three identities and give them roles

```
oc create serviceaccount viewer -n jegan-app
oc create serviceaccount deployer -n jegan-app
oc create serviceaccount restarter -n jegan-app

oc policy add-role-to-user view -z viewer -n jegan-app
oc policy add-role-to-user edit -z deployer -n jegan-app
```

`restarter` gets a custom role in Step 7.

Step 6: Test what each identity can do

`oc auth can-i --as` asks the API server to check a request as another identity, without running it.

```
SA=system:serviceaccount:jegan-app

oc auth can-i list pods      -n jegan-app --as=$SA:viewer
oc auth can-i delete pods    -n jegan-app --as=$SA:viewer
oc auth can-i get secrets    -n jegan-app --as=$SA:viewer

oc auth can-i delete pods    -n jegan-app --as=$SA:deployer
oc auth can-i get secrets    -n jegan-app --as=$SA:deployer
oc auth can-i create rolebindings -n jegan-app --as=$SA:deployer

oc auth can-i list pods      -n default   --as=$SA:deployer
```

Expected
<pre>
yes
no
no
yes
yes
no
no
</pre>

What this shows:
- `view` can read pods but **cannot read secrets**, so you can safely give it to auditors and support teams.
- `edit` can change applications and read secrets, but **cannot grant access** to anyone else.
- Both roles apply only inside `jegan-app`. The last check against `default` fails.

Step 7: Create a least-privilege role

Suppose a monitoring job only needs to restart stuck pods. `edit` would give it far too much. Create a role with exactly what it needs:

```
oc create role pod-restarter --verb=get,list,delete --resource=pods -n jegan-app
oc create rolebinding restarter-binding --role=pod-restarter \
  --serviceaccount=jegan-app:restarter -n jegan-app
```

Test it:
```
oc auth can-i delete pods         -n jegan-app --as=$SA:restarter
oc auth can-i delete deployments  -n jegan-app --as=$SA:restarter
oc auth can-i get secrets         -n jegan-app --as=$SA:restarter
```

Expected
<pre>
yes
no
no
</pre>

Step 8: Use the identity for real

`can-i` only asks. Now send real requests with the service account's token:

```
TOKEN=$(oc create token restarter -n jegan-app)

oc --token="$TOKEN" delete pod -l app=web -n jegan-app
oc --token="$TOKEN" get secrets -n jegan-app
oc --token="$TOKEN" delete deployment web -n jegan-app
```

Expected (pod name differs)
<pre>
pod "web-6d8f7c9b5d-x2kqp" deleted
Error from server (Forbidden): secrets is forbidden: User "system:serviceaccount:jegan-app:restarter" cannot list resource "secrets" in API group "" in the namespace "jegan-app"
Error from server (Forbidden): deployments.apps "web" is forbidden: User "system:serviceaccount:jegan-app:restarter" cannot delete resource "deployments" in API group "apps" in the namespace "jegan-app"
</pre>

The deployment creates a replacement pod, so the application keeps running:
```
oc get pods -n jegan-app -l app=web
```

Step 9: Review and revoke access

List who has which role in the project:
```
oc get rolebindings -n jegan-app -o wide
```

Ask the reverse question: who can delete pods here?
```
oc adm policy who-can delete pods -n jegan-app
```

Look for `restarter` and `deployer` in the service account list.

Revoke `restarter` and check again:
```
oc delete rolebinding restarter-binding -n jegan-app
oc auth can-i delete pods -n jegan-app --as=$SA:restarter
oc --token="$TOKEN" delete pod -l app=web -n jegan-app
```

Expected
<pre>
no
Error from server (Forbidden): pods "web-..." is forbidden: User "system:serviceaccount:jegan-app:restarter" cannot delete resource "pods" ...
</pre>

The token is still valid, but it no longer grants anything. RBAC is checked on every request, so revoking a binding takes effect immediately.

Step 10: Clean up

```
oc delete project jegan-app
unset SA TOKEN
```

Summary
| Control | Question it answers | What you saw |
|---|---|---|
| SCC (`restricted-v2`) | What may this **application** do on the node? | Random non-root UID; a root container was refused |
| Role / RoleBinding | What may this **identity** do in this project? | `view`, `edit` and a custom role gave three different sets of rights |
| `oc auth can-i` | Would this request be allowed? | Test access without making changes |
| `oc adm policy who-can` | Who is allowed to do this? | Audit access from the resource side |

| Good practice | Why |
|---|---|
| Build images that run as any non-root UID | They work under `restricted-v2` without extra SCCs |
| Never grant `anyuid` or `privileged` to fix a failing image | Fix the image instead; those SCCs remove the node protection |
| Give each application its own service account | You can grant and revoke its access separately |
| Start from `view` or a custom role, not `edit` or `admin` | Least privilege limits the damage from a stolen token |
| Give `view` instead of `edit` to people who only need to look | `view` hides secrets |

## Lab - Taints and Tolerations
<pre>
- By default, OpenShift won't schedule your application pods on master nodes
- The masters carry a taint, and a pod lands on a tainted node only if it tolerates that taint
- In this lab we make user pods run on the master nodes in two ways
  - 1. Add a toleration to a single deployment (you can do this yourself)
  - 2. Make all the masters schedulable for the whole cluster (I'll do this part, as it needs cluster-admin)
</pre>

Use your name in the project name, for example `uday-taint`. I use `jegan-taint` in the commands below.
<pre>
- Please don't try this on a production cluster. 
- The masters run etcd and the API server, and a heavy application pod there can slow down the entire cluster
</pre>

Check the nodes and their taints
```
oc get nodes
```

Sample output
<pre>
NAME                        STATUS   ROLES                  AGE   VERSION
master01.ocp4.palmeto.org   Ready    control-plane,master   30d   v1.35.x
master02.ocp4.palmeto.org   Ready    control-plane,master   30d   v1.35.x
master03.ocp4.palmeto.org   Ready    control-plane,master   30d   v1.35.x
worker01.ocp4.palmeto.org   Ready    worker                 30d   v1.35.x
worker02.ocp4.palmeto.org   Ready    worker                 30d   v1.35.x
</pre>

Now list the taints on each node
```
oc get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.taints[*]}{.key}:{.effect} {end}{"\n"}{end}'
```

Sample output
<pre>
master01.ocp4.palmeto.org   node-role.kubernetes.io/master:NoSchedule
master02.ocp4.palmeto.org   node-role.kubernetes.io/master:NoSchedule
master03.ocp4.palmeto.org   node-role.kubernetes.io/master:NoSchedule
worker01.ocp4.palmeto.org
worker02.ocp4.palmeto.org
</pre>

<pre>
- A taint is written as `key=value:effect`
- The master taint has no value
- The effect `NoSchedule` tells the scheduler not to place any new pod on this node unless 
  the pod tolerates the taint
- The workers have no taint, which is why all your pods end up there
- If you don't see any taint on the masters and their role also shows `worker`, the masters are 
  already schedulable
</pre>

Create your project
```
oc new-project jegan-taint
```

Deploy on the masters without a toleration
Let's first see what happens when we ask for the master nodes without tolerating their taint.
```
cat <<'EOF' | oc apply -n jegan-taint -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: on-master
spec:
  replicas: 3
  selector:
    matchLabels:
      app: on-master
  template:
    metadata:
      labels:
        app: on-master
    spec:
      nodeSelector:
        node-role.kubernetes.io/master: ""
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
EOF
```

```
oc get pods -n jegan-taint -o wide
```

Sample output
<pre>
NAME                         READY   STATUS    RESTARTS   AGE   IP       NODE
on-master-7c9d5b8f6d-4kx2m   0/1     Pending   0          15s   &lt;none&gt;   &lt;none&gt;
on-master-7c9d5b8f6d-9tq7w   0/1     Pending   0          15s   &lt;none&gt;   &lt;none&gt;
on-master-7c9d5b8f6d-zr5hn   0/1     Pending   0          15s   &lt;none&gt;   &lt;none&gt;
</pre>

All three pods are stuck in Pending. Let's ask the scheduler why.
```
oc get events -n jegan-taint --field-selector reason=FailedScheduling \
  -o custom-columns=MESSAGE:.message | tail -1
```

Sample output
<pre>
0/5 nodes are available: 2 node(s) didn't match Pod's node affinity/selector,
3 node(s) had untolerated taint {node-role.kubernetes.io/master: }. ...
</pre>

<pre>
- Read the message carefully. The workers don't match our `nodeSelector`, and the masters 
  reject the pods because of the taint. That leaves no node for our pods
</pre>

Method 1 - Add a toleration to the deployment
```
oc patch deployment on-master -n jegan-taint --type=merge -p '{
  "spec":{"template":{"spec":{"tolerations":[
    {"key":"node-role.kubernetes.io/master","operator":"Exists","effect":"NoSchedule"},
    {"key":"node-role.kubernetes.io/control-plane","operator":"Exists","effect":"NoSchedule"}
  ]}}}}'
```

```
oc rollout status deployment/on-master -n jegan-taint
oc get pods -n jegan-taint -o wide
```

Sample output
<pre>
NAME                         READY   STATUS    RESTARTS   AGE   IP            NODE
on-master-5f8b6c7d9c-2hxqv   1/1     Running   0          20s   10.128.0.54   master01.ocp4.palmeto.org
on-master-5f8b6c7d9c-8wlpz   1/1     Running   0          18s   10.129.0.61   master02.ocp4.palmeto.org
on-master-5f8b6c7d9c-q4n7t   1/1     Running   0          16s   10.130.0.47   master03.ocp4.palmeto.org
</pre>

The pods are running on the masters now.
<pre>
A few points about the toleration:
- `operator: Exists` matches the key irrespective of its value, which suits the master 
  taint as it has no value
- I have added the `control-plane` key as well. Some clusters taint the masters with that key
- Tolerating a taint that isn't present does no harm.
- Never write a toleration with `operator: Exists` and no key. That tolerates every taint on the cluster, 
  including the ones OpenShift adds to nodes that are down or under maintenance.
</pre>

Toleration is not the same as nodeSelector
<pre>
- The toleration only allows the pod on a tainted node
- It doesn't send the pod there. The `nodeSelector` is what sends it
- Remove the `nodeSelector` and watch where the pods go.
</pre>

```
oc patch deployment on-master -n jegan-taint --type=json \
  -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"}]'

oc rollout status deployment/on-master -n jegan-taint
oc get pods -n jegan-taint -o wide
```
<pre>
- This time the pods spread across masters and workers, wherever the scheduler finds room
- If you want pods only on the masters, you need both the toleration and the `nodeSelector`.
</pre>

Delete the deployment before we move on.
```
oc delete deployment on-master -n jegan-taint
```

Method 2 - Make the masters schedulable (cluster-admin)
<pre>
- I'll run this on server1 and server2, as it changes the scheduler setting for the whole cluster
- If each of you runs it, you will keep flipping it for everyone else
</pre>
```
oc patch schedulers.config.openshift.io cluster --type=merge \
  -p '{"spec":{"mastersSchedulable":true}}'
```

Give it a minute, then check the nodes and taints again.
```
oc get nodes
oc get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.taints[*]}{.key}:{.effect} {end}{"\n"}{end}'
```

Sample output
<pre>
NAME                        STATUS   ROLES                         AGE   VERSION
master01.ocp4.palmeto.org   Ready    control-plane,master,worker   30d   v1.35.x
master02.ocp4.palmeto.org   Ready    control-plane,master,worker   30d   v1.35.x
master03.ocp4.palmeto.org   Ready    control-plane,master,worker   30d   v1.35.x
...

master01.ocp4.palmeto.org
master02.ocp4.palmeto.org
master03.ocp4.palmeto.org
</pre>

The masters have picked up the `worker` role and the taint is gone.
<pre>
- You may find blogs that remove the taint by hand with `oc adm taint, don't do that on OpenShift
- The `mastersSchedulable` setting is the supported way, and a taint you remove by hand can come back, 
  for instance when the node registers again after a reboot or an upgrade.
</pre>

Now deploy with no toleration at all.
```
cat <<'EOF' | oc apply -n jegan-taint -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: no-toleration
spec:
  replicas: 3
  selector:
    matchLabels:
      app: no-toleration
  template:
    metadata:
      labels:
        app: no-toleration
    spec:
      nodeSelector:
        node-role.kubernetes.io/master: ""
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
EOF
```

```
oc rollout status deployment/no-toleration -n jegan-taint
oc get pods -n jegan-taint -o wide
```

All three pods should be running on the masters. This is the same spec that stayed Pending earlier.

Put the taint back (cluster-admin)

Again, I'll run this one.
```
oc patch schedulers.config.openshift.io cluster --type=merge \
  -p '{"spec":{"mastersSchedulable":false}}'
```

After a minute the taint is back on the masters. Now check your pods.
```
oc get pods -n jegan-taint -o wide
```
<pre>
- Surprised? Your pods are still running on the masters. 
- `NoSchedule` only stops new pods from being placed, it doesn't evict pods that are already running
</pre>

Restart the deployment and see what happens to the new pods.
```
oc rollout restart deployment/no-toleration -n jegan-taint
oc get pods -n jegan-taint -o wide
```

The new pods go back to Pending, as the masters are tainted again.
<pre>
- If you want running pods to be evicted as well, the taint must use the `NoExecute` effect
- OpenShift uses it on nodes that stop responding, for example `node.kubernetes.io/unreachable:NoExecute`, 
  so that their pods get rescheduled elsewhere
</pre>

Quick reference on the three effects:
| Effect | New pods without toleration | Pods already running |
|---|---|---|
| PreferNoSchedule | Avoided if another node is available | Keep running |
| NoSchedule | Not scheduled | Keep running |
| NoExecute | Not scheduled | Evicted |

## Cleanup
```
oc delete project jegan-taint
```

I'll confirm the scheduler setting is back to `false` at my end.
```
oc get schedulers.config.openshift.io cluster -o jsonpath='{.spec.mastersSchedulable}{"\n"}'
```
