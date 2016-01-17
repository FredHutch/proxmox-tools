Promox helper scripts
==

proxhostname.py
-- 

script runs inside newly deployed ProxMox VM or Container, queries promox API for correct hostname according to MAC address found on the local system and set the new hostname

If you have an IPAM device (such as Infoblox) you just need to change the hostname on your Linux to have dynamic DNS get you a new IP address. This allows you to deploy many hosts within seconds

tested with Ubuntu 14.04 and Ubuntu 16.04 alpha 1

prox.py
--

prox is a command line interface to rapidly deploy VMs on proxmox from a remote host using proxmox REST API.

prox supports a number of command line options:

```
user1@rhino1:$ prox.py --help
usage: prox  [-h] [--hosts [HOSTS [HOSTS ...]]] [--image IMAGE] [--debug]
             [--mailto MAILTO]
             [command]

a tool for deploying resources from proxmox (LXC containers or VMs)

positional arguments:
  command               a command to be executed. (deploy, start, stop)

optional arguments:
  -h, --help            show this help message and exit
  --hosts [HOSTS [HOSTS ...]], -n [HOSTS [HOSTS ...]]
                        hostnames of your new VM/containers
  --image IMAGE, -i IMAGE
                        image we use to clone
  --debug, -d           do not send an email but print the result to console
  --mailto MAILTO, -m MAILTO
                        send email address to notify of a new deployment.

```


However if you want to use it interactivelty you can just invoke the command prox (or prox.py)


```
user1@rhino:$ prox.py 
Executing command "prox deploy"
Password for 'user1':

Please enter a template name or just hit enter to select from a list:
enter template: [templ1404,win7template,templ1604,templcoreh0]:templ1604 

enter the hostname(s) you want to deploy (separated by space, no domain name)
enter hostname(s):testvm1 testvm2 testvm3

creating host testvm1 with VM ID 101 in pool scicomp
    ...UPID:euler:000F1637:680EBD3C:569BCC9A:qmclone:140:user1@FHCRC.ORG:
creating host testvm2 with VM ID 115 in pool scicomp
    ...UPID:euler:000F163C:680EBD46:569BCC9A:qmclone:140:user1@FHCRC.ORG:
creating host testvm3 with VM ID 116 in pool scicomp
    ...UPID:euler:000F1641:680EBD51:569BCC9A:qmclone:140:user1@FHCRC.ORG:

Do you want to start these VMs now? (Y/n) y

Starting VM 101 ..
    ...UPID:euler:000F1713:680EC7AE:569BCCB5:qmstart:101:user1@FHCRC.ORG:
Starting VM 115 ..
    ...UPID:euler:000F171A:680EC7B4:569BCCB5:qmstart:115:user1@FHCRC.ORG:
Starting VM 116 ..
    ...UPID:euler:000F172F:680EC7BB:569BCCB5:qmstart:116:user1@FHCRC.ORG:

waiting for host testvm1 to come up .. hit ctrl+c to stop ping
ping: unknown host testvm1
ping: unknown host testvm1
ping: unknown host testvm1
ping: unknown host testvm1
PING testvm1.fhcrc.org (10.10.117.191) 56(84) bytes of data.
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=1 ttl=63 time=3.98 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=2 ttl=63 time=0.211 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=3 ttl=63 time=0.235 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=4 ttl=63 time=0.194 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=5 ttl=63 time=0.214 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=6 ttl=63 time=0.137 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=7 ttl=63 time=0.164 ms
64 bytes from testvm1.fhcrc.org (10.10.117.191): icmp_seq=8 ttl=63 time=0.174 ms

--- testvm1.fhcrc.org ping statistics ---
8 packets transmitted, 8 received, 0% packet loss, time 6999ms
rtt min/avg/max/mdev = 0.137/0.663/3.981/1.254 ms
0
Host testvm1 is up and running, you can now connect
```
