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
