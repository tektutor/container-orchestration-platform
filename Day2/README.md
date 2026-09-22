# Day 2

## Info - Container Orchestration Platform
<pre>
- the motivation for using Container Orchestration Platforms
  - in-built load-balancing
  - in-built monitoring and self-healing
  - in-built scale up/down manually/automatically
  - rolling update
    - upgrading your already live application from one version to other without any downtime
    - rollback to older stable version if required
  - service discovery
    - accessing an application using its service name
    - in-built dns to resolve the service name to its corresponding IP address
  - service ( represents a group of Pods from a single application )
    - service name and server IP is stable but Pods are temporary
    - internal
    - external
- examples
  - Docker SWARM ( Docker's native Container Orchestration Platform )
  - Google Kubernetes ( Command-line only )
  - Rancher ( Kubernetes with Webconsole )
  - Red Hat Openshift ( Red Hat's distribution of Kubernetes )
  - ROSA (Managed - Openshift cluster from AWS )
  - ARO ( Managed - Opeshift cluster from Azure )
  - eks ( Managed Kubernetes cluster from AWS )
  - aks ( Managed Kubernetes cluster from Azure )
</pre>

## Info - Docker SWARM Overview
<pre>
- Docker's native Container Orchestration Platform
- it is opensource
- it only supports Docker Containerized applications to be deployed
- it is very light-weight, easy to setup, easy to learn
- ideal for learning, dev/qa setup
- not production-grade
</pre>  

# Info - Kubernetes
<pre>
- developed by Google with Go language
- it is opensource, and supports only command-line interface
- it is robust, hence it is production-grade
- there are several ways to install Kubernetes
- inside Google, it was originally developed and used as borg project
- later, borg was refactored and donated to Cloud Native Cloud Foundation in the name Kubernetes
  that's how it has become open-source
- it supports Role Base Access Control but no User Management
- there is a namespace concept, every team can create their own application deployment in a Kuberenetes namespace
- namespace is a way to seggregate the application deployments between teams
- Kubernetes works as a cluster of many machines(nodes)
- Kubernetes nodes can be
  - Physical Server
  - Virtual Machine
  - an ec2 instance in AWS
  - an azure vm
- there are 2 types of Nodes
  - Master Node
    - Control Plane components only runs in the master node
    - Control Plane Components are also Pods
      1. API Server
      2. etcd - key/value datastore
      3. Scheduler
      4. Controller Managers ( collection of many Controllers )
  - Worker Node
    - user application are deployed here as Pods
- these are built-in type of resources supported by Kubernetes (k8s)
  - Pod
  - ReplicaSet
  - Deployment
  - DaemonSet
  - StatefulSet
  - Job
  - CronJob
  - Service
  - EndPoint
- Kubernetes also supports adding our own custom resources types and we can extend K8s API and features
- the basic build blocks required to extend K8s comes out of the box in K8s
  - Custom Resource Definitions (CRD) - we can add new type of Resource by creating CRD yaml file
  - To manage our custom resource, we also need to provide our own Controller
- application can be deployed and managed in 2 style
  - imperative style ( plain commands in CLI )
  - declarative style ( yaml file - manifests )
</pre>

## Info - Pod
<pre>
- is a logical grouping of related Containers
- the smallest unit that can be deployed in Kubernetes/Openshift is Pod
- all containers in a Pod, shares the same network, ports, IP-address
- is a configuration object/resource that is stored and managed in etcd database by API Server
- a built-in resource type supported in Kubernetes & Openshift
</pre>

## Info - ReplicaSet
<pre>
- an in-built resource type supported in Kubernetes & Openshift
- it is a Configuration Object/Resource stored and managed by etcd datastore 
- ReplicaSet capture below details
  - desired number of Pods that must be created/running
  - Container Image that must be used 
  - labels selectors that are used to identify the respective Pods
</pre>

## Info - Deployment
<pre>
- is a built-in resource type that is maintained in etcd database by API Server
- it is used to deploy stateless application
- Deployment has one or more ReplicaSets
- ReplicaSet has one or more Pods
- Pods has one or more Containers
</pre>

## Info - Type of applications
<pre>
- Stateless ( Deployment )
- Stateful  ( StatefulSet )
- One time Job ( Job )
- Recurring Jobs (CronJob)
- Running one Pod per Node ( DaemonSet )
</pre>

## Info - Control Plane Components
<pre>
- collectively all 4 components supports the Container Orchestration Platform features
- all the Control Planes components are all also called as Static Pods
- the Control Planes components are created and managed by kubelet Container agent that runs on every node
- kubelet is service not a Pod
- whenever the node OS is booted, the kubelet service is started automatically, and kubelet starts the control plane
- kubelet also runs on worker nodes, kubelet communicates with the Container Runtime to pull, create and manage the containers
  on the node where kubelet is running
- kubelet monitors the status of all Pod containers that runs on the current node and keeps reporting the status to API Server
  at regular intervals in a heart-beat fashion
</pre>

## Info - API Server Control-Plane Component (Pod)
<pre>
- this is the heart/brain of Kubernetes
- it maintains the Cluster and application status in the etcd distributed database
- ApI Server is the only component that can read/write to/from the etcd database
- all the Kubernetes components they communicated only to API Server via REST API calls
- API Server has REST API for all the features supported in Kubernetes
- Whenever API SErver updates the etcd database, API Server will send a event about the update
</pre>

## Info - etcd (Pod)
<pre>
- it is an opensource independent project
- it is a distributed database that stores and retrieves data as key/value
- generally this works as a cluster - a group of etcd databases as a cluster
- hence when data is updated on one instance of etcd, it automatically gets synchronized in other instances of etcd database
</pre>


## Info - Scheduler (Pod)
<pre>
- this component is responsible to identify in which node a new Pod can be deployed
- the Scheduler by itself can't schedule the pods on any node, it can only identify a healthy node where a Pod can be 
  deployed, this scheduling recommendation is forwarded to API Server via REST call by Scheduler
</pre>

## Info - Controller Managers (Pod)
<pre>
- it is a collection of many Controllers
- each Controller manages one type of Kubernetes Resource
- example
  - ReplicaSet Controller takes ReplicaSet as an input and manages Pods
  - Deployment Controller takes Deployment as an input and managed ReplicaSet
  - StatefulSet Controller takes StatefulSet as input and manages Pods
</pre>

## Info - Kubernetes High-Level Architecture
![kubernetes](KubernetesArchitecture2.png)

## Info - Red Hat Openshift High-Level Architecture
![openshift](openshiftArchitecture.png)

## Lab - Listing all nodes in the Kubernetes cluster
```
kubectl version

kubectl get nodes
kubectl get nodes -o wide
```
