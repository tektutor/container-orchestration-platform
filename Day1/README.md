# Day 1

## Info - Hypervisor Overview
<pre>
- Virtualization technology
- in order to install additional OS, we need to create a Virtual Machine (VM) and then install the OS within the VM
- the OS that runs within the VM are called Guest OS
- the Guest OS believes it is running on a separate Server/Machine
- each VM must be allocated with dedicated H/W resources
       - CPU ( Logical/Virtual CPU Cores )
       - RAM (Actual)
       - Storage ( Actual )
       - Network (Virtual )
       - Graphics Card ( Virtual )
- Processor
  - AMD 
    - Virtualization instruction set is referred as AMD-V
  - Intel 
    - Virtualization instruction set is referred as VT-X
- There are 2 flavours of hypervisor
  1. Type 1 - a.k.a Bare Metal Hypervisor
     - this doesn't require any Host OS on the server, we can directly install Type 1 Hypervisior
     - is used in Servers & Workstations
     - examples
       - VMWare vSphere(vcenter), Microsoft Hyper-V, Linux KVM

  2. Type 2 - a.k.a Hosted Hypervisor
     - is used in Desktops, Laptops & Workstations
     - Hypervisor can only be installed on top of Host OS ( Windows, Linux or Mac OS-X )
     - examples
       - VMWare Wokstation ( Linux & Windows )
       - VMWare Fusion ( Mac OS-X )
       - Parallels ( Mac OS-X )
       - Oracle VirtualBox ( Linux, Windows & Mac )
- HyperThreading or SMT
  - each Physical CPU Core is equalivalent to 2 Logical/Virtual Cores
- Server Motherboards supports multiple Processors Sockets
  - Imagine a Server Motherboard has got 8 Processor Sockets
  - MCM (MUltiple Chip Module ) i.e multiple Processors can be packaged in a single IC
    - 2 Processors per MCM IC Chip
  - Each Processor may support
    - 128/256 CPU Cores
  - 8 Sockets x 2 Processors x 128 = 2048 Physical CPU Cores = 2048 x 2 = 4096 Logial/Virtual Cores
- this type of Virtualization is called heavy-weight virtualization
  - because each VM requires its own dedicated H/W resources
  - each OS that runs within the VM is a fully-function OS
- each VM, represents a single OS
</pre>

## Info - Containerization
<pre>
- Containerization is a light-weight virtualization technology
- unlike VMs, containers that runs on same server/machine will share the hardware resources on the underlying host OS
- containers are light-weight compared to VMs
- containers are faster compared to VM
- containers runs in it owns namespace
  - each container uses about 5~6 different namespaces
    - PID namespaces
    - Network namespace
- Each container or a group of containers represents a single application
- in many ways Container resembles a Virtual Machine (OS)
- just like each VM aquires its own IP address, each container get an IP address
- just like VM has a network stack and NIC, container also get a network stack and NIC
- just like the OS has its own filesystem and command prompt/terminal, containers also supports command prompt/terminal
- just like VM has its own port range ( 0 to 65535 ), containers also get its own port range
- but technically containers are just a Process in the Operating System it is not an OS
- technically, containers will never be able to replace OS/VM
- practically speaking, in production, one Physical Server will host many Virtual Machines, each Virtual Machine may be hosting multiple containerized
  applications
- examples
  - Docker
  - Containerd
  - Podman  
- Containerization is a Linux technology
- in Linux Kernel
  - there are 2 features which makes the Containerization possible
    1. Namespace
       - helps in isolating one container from the other containers
    2. Control Groups (CGroups)
       - helps in applying container level resource quota restrictions 
       - we can control, how much storage one container can utilize at the max
       - we can control, how many CPU cores one container can utilize at the max
</pre>

## Info - Container Runtime
<pre>
- is a low-level software that helps managing containers
  - it can create, start, stop, restart containe
</pre>

## Info - Container Engine
<pre>
       
</pre>
