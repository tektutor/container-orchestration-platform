# Day 1

## Info - Hypervisor Overview
<pre>
- Virtualization technology
- in order to install additional OS, we need to create a Virtual Machine (VM) and then install the OS within the VM
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
     - this doesn't require any Host OS on the server, we can directly install Type 1 Hypersior
     - is used in Servers & Workstations
     - examples
       - VMWare vSphere(vcenter), Microsoft Hyper-V, Linux KVM

  2. Type 2 - a.k.a Hosted Hypervisor
     - is used in Desktops, Laptops & Workstations
     - examples
       - VMWare Wokstation ( Linux & Windows )
       - VMWare Fusion ( Mac OS-X )
       - Parallels ( Mac OS-X )
       - Oracle VirtualBox ( Linux, Windows & Mac )
</pre>
