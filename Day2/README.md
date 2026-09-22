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
</pre>

## Info - Pod
<pre>
- is a logical grouping of related Pods
- the smallest unit that can be deployed in Kubernetes/Openshift is Pod
- all containers in a Pod, shares the same network, ports, IP-address
</pre>


## Info - Kubernetes High-Level Architecture
![kubernetes](KubernetesArchitecture2.png)

## Info - Red Hat Openshift High-Level Architecture
![openshift](openshiftArchitecture.png)
