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
- is a logical grouping of related Pods
- the smallest unit that can be deployed in Kubernetes/Openshift is Pod
- all containers in a Pod, shares the same network, ports, IP-address
</pre>

## Info - Type of applications
<pre>
- Stateless ( Deployment )
- Stateful  ( StatefulSet )
- One time Job ( Job )
- Recurring Jobs (CronJob)
- Running one Pod per Node ( DaemonSet )
</pre>


## Info - Kubernetes High-Level Architecture
![kubernetes](KubernetesArchitecture2.png)

## Info - Red Hat Openshift High-Level Architecture
![openshift](openshiftArchitecture.png)
