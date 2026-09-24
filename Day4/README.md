# Day 4

## Info - Persistent Volume (PV)
<pre>
- Ideally, Pods should be used like a read-only resource
- Technically, we can store/retrieve data in the Pod storage, i.e Pods are mutable
- But, using Pod storage is not recommended as per DevOps Philosophy
- Hence, we should use an external storage to persist the data
- In Kubernetes, the external storage is called Persistent Volume (PV)
- The PV can be provisioned using NFS, AWS S3, Longhorn, etc.,
- PVs can only be provisioned on the cluster scope, can never be created in the namespace scope
- There are 2 ways to provision PV by administrators cluster-wide
  1. Manually PV can be provisioned by creating a yaml file with all required permission, disk size, NFS server IP, etc.,
  2. Dynamic provision using Storage Class
     - Administrators can create Storage Class for NFS, Longhorn, AWS S3
     - The storage will take the required login credentials and provision the PV at runtime on demand 
</pre>

## Info - Persistent Volume Claim (PVC)
<pre>
- Any application that needs external storage, should ask for external storage by creating a PVC
- PVC will mention details like
  - Permission required on the external disk
  - Size of the external disk required
  - Storage Class ( Optional )
- Kubernetes cluster will search through the cluster for a matching PV
- If Kubernetes cluster is able to find an exact matching PV, it will then let the PVC go and claim it before 
  the application can use it
</pre>

## Lab - Deploying multi-pod wordpress and mysql that uses external persistent volumes
```
cd ~/container-orchestration-platform
git pull
cd Day4/wordpress-with-configmaps-and-secrets

# Edit mysql-pv.yml, mysql-pvc.yml, mysql-deploy.yml, wordpress-pv.yml, wordpress.pyc.yml, wordpress-deploy.yml
# Find and replace 'jegan' with yout name
# Update the server IP to 192.168.2.201 in case you are working in second server
# In the mysql-pv.yml and wordpress-pv.yml, update the path by checking folders reserved for you using showmount -e | grep jegan

./deploy.sh

kubectl get pv,pvc

kubectl get pods -w

# look for ready for connections
kubectl logs mysql-6d797f49d7-2tzh4

kubectl get svc

# From lab machine web browser, you need substitute the IP based on your external IP reported by the service
http://192.168.122.201:80
```
