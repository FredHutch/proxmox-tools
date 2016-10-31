Proxmox helper scripts
==

proxhostname.py
-- 

script runs inside newly deployed ProxMox VM or Container, queries promox API for correct hostname according to MAC address found on the local system and set the new hostname

If you have an IPAM device (such as Infoblox) you just need to change the hostname on your Linux to have dynamic DNS get you a new IP address. This allows you to deploy many hosts within seconds

tested with Ubuntu 14.04 and Ubuntu 16.04

prox.py
--

prox is a command line interface to rapidly deploy VMs on proxmox from a remote host using proxmox REST API.

prox supports a number of command line options:

```
user@sphinx:~$ prox --help
usage: prox  [-h] [--runlist RUNLIST] [--mem MEM] [--disk DISK]
             [--cores CORES] [--storenet] [--vmid VMID] [--debug]
             [{new,list,start,stop,modify,destroy,assist}] [hosts [hosts ...]]

a tool for deploying resources from proxmox (LXC containers or VMs)

positional arguments:
  {new,list,start,stop,modify,destroy,assist}
                        a command to be executed. (new, list, start , stop ,
                        modify, destroy, assist
  hosts                 hostname(s) of VM/containers (separated by space),
                        example: prox new host1 host2 host3

optional arguments:
  -h, --help            show this help message and exit
  --runlist RUNLIST, -r RUNLIST
                        a local shell script file or a command to execute
                        after install
  --mem MEM, -m MEM     Memory allocation for the machine, e.g. 4G or 512
                        Default: 512
  --disk DISK, -d DISK  disk storage allocated to the machine. Default: 4
  --cores CORES, -c CORES
                        Number of cores to be allocated for the machine.
                        Default: 2
  --storenet, -n        use network storage (nfs, ceph) instead of local
                        storage
  --vmid VMID, -v VMID  vmid, proxmox primary key for a container or vm
  --debug, -g           verbose output for all commands
```

let's say you want to deploy a new docker host named sausage:

```
user@rhino3:~$ prox --mem 1024 --disk 8 new sausage
Password for 'user':

creating host sausage with ID 121 in pool SciComp
    ...UPID:proxa3:00001F6C:00F2DBDE:57EE629A:vzcreate:121:user@FHCRC.ORG:
Starting host 121 ..
    ...UPID:proxa3:00001FB3:00F2E185:57EE62A8:vzstart:121:user@FHCRC.ORG:
Machine 121 : running, cpu: 0% 

waiting for machine sausage to come up .. hit ctrl+c to stop ping
```

now you can install docker manually. 
As a next step let's assume you would like to install docker on multiple 
machines. We can create a runlist in a simple text file and each command in 
that list will be executed on each machine. In this case we made a runlist 
that installs docker:

```
user@rhino3:~$ cat ~/runlist-docker 
apt-get update
apt-get install -y docker-engine
```

now we can use the prox command to install multiple machines:

```
user@rhino3:~$ prox --runlist ~/runlist-docker --disk 8 new sausage1 sausage2 sausage3
Password for 'user':

creating host sausage1 with ID 116 in pool SciComp
    ...UPID:proxa3:000039A6:0111B96E:57EEB19E:vzcreate:116:user@FHCRC.ORG:
creating host sausage2 with ID 118 in pool SciComp
    ...UPID:proxa3:000039B6:0111B980:57EEB19E:vzcreate:118:user@FHCRC.ORG:
creating host sausage3 with ID 121 in pool SciComp
    ...UPID:proxa3:000039C4:0111B991:57EEB19E:vzcreate:121:user@FHCRC.ORG:
Starting host 116 ..
starting host 116, re-try 0
    ...UPID:proxa3:00003A04:0111BCB7:57EEB1A6:vzstart:116:user@FHCRC.ORG:
Machine 116 : running, cpu: 0% 
Starting host 118 ..
    ...UPID:proxa3:00003AF7:0111BD3C:57EEB1A8:vzstart:118:user@FHCRC.ORG:
Machine 118 : running, cpu: 0% 
Starting host 121 ..
    ...UPID:proxa3:00003BE2:0111BDC2:57EEB1A9:vzstart:121:user@FHCRC.ORG:
Machine 121 : running, cpu: -1% 
```

and after you are done with your work you can stop and then destroy these machines: 

```
user@rhino3:~$ prox stop sausage1 sausage2 sausage3
Password for 'user':

UPID:proxa2:000060FE:01121EA2:57EEB2A1:vzstop:116:user@FHCRC.ORG:
UPID:proxa3:00006110:01121EB3:57EEB2A1:vzstop:118:user@FHCRC.ORG:
UPID:proxa4:00006127:01121EC6:57EEB2A1:vzstop:121:user@FHCRC.ORG:

user@rhino3:~$ 
user@rhino3:~$ prox destroy sausage1 sausage2 sausage3
Password for 'user':

UPID:proxa2:000061C7:01122C18:57EEB2C4:vzdestroy:116:user@FHCRC.ORG:
UPID:proxa3:000061CB:01122C2A:57EEB2C4:vzdestroy:118:user@FHCRC.ORG:
UPID:proxa4:000061CF:01122C3B:57EEB2C4:vzdestroy:121:user@FHCRC.ORG:
```

