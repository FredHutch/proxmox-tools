Proxmox tools / scripts
=======================

prox
----

prox is a command line interface to rapidly deploy LXC containers on proxmox from a remote host
using proxmox REST API.

prox supports a number of sub commands and command line options:

::

    > prox --help
    usage: prox  [-h] [--debug]
                 {assist,gui,ssh,connect,list,ls,show,start,run,stop,shutdown,destroy,delete,modify,mod,snap,snapshot,rollback,rb,new,create}
                 ...

    a tool for deploying resources from proxmox (LXC containers or VMs)

    positional arguments:
      {assist,gui,ssh,connect,list,ls,show,start,run,stop,shutdown,destroy,delete,modify,mod,snap,snapshot,rollback,rb,new,create}
                            sub-command help
        assist (gui)        navigate application via GUI (experimental)
        ssh (connect)       connect to first host via ssh
        list (ls, show)     list hosts(s) with status, size and contact (optional)
        start (run)         start the host(s)
        stop (shutdown)     stop the host(s)
        destroy (delete)    delete the hosts(s) from disk
        modify (mod)        modify the config of one or more hosts
        snap (snapshot)     take a snapshot of the host
        rollback (rb)       roll back a snapshot
        new (create)        create one or more new hosts

    optional arguments:
      -h, --help            show this help message and exit
      --debug, -g           verbose output for all commands

and one of the most common sub command will the 'prox new' to create a new machine:

::

    > prox new --help
    usage: prox new [-h] [--runlist RUNLIST] [--mem MEM] [--disk DISK]
                    [--cores CORES] [--store-net] [--bootstrap] [--no-bootstrap]
                    [hosts [hosts ...]]

    positional arguments:
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
      --store-net, -s       use networked storage with backup (nfs, ceph) instead
                            of local storage
      --bootstrap, -b       auto-configure the system using Chef.
      --no-bootstrap, -n    do not auto-configure the system using Chef.

To install prox you can simply use pip3. But before you may need a few OS packages. On Ubuntu /
Debian you would run:

::

    sudo apt-get install -y python3-pip python3-dev libffi-dev libssl-dev

and on CentOS/RedHat you would run:

::

    yum -y install epel-release python34-devel libffi-devel openssl-devel

after that you can run pip3:

::

    pip3 install --upgrade pip
    pip3 install --upgrade proxmox-tools

after that you just need to configure prox, you can do this by uncommenting the lines that start
with 'export ' directly in file /usr/local/bin/prox or you paste the export statements into file
~/.proxrc in the home directory of the user who runs prox.

::

    > cat ~/.proxrc
    export PPROXHOST='proxmox.domain.org'
    export PREALM='pam' 
    export PLXCTEMPLATE='proxnfs:vztmpl/ubuntu-16.04-standard_16.04-1_amd64.tar.gz'
    export PSTORLOC='proxazfs'
    export PSTORNET='proxnfs'

now let's say you want to deploy a new docker host named sausage:

::

    > prox new --mem 1024 --disk 8 sausage
    Password for 'user':

    creating host sausage with ID 121 in pool SciComp
        ...UPID:proxa3:00001F6C:00F2DBDE:57EE629A:vzcreate:121:user@DOMAIN.ORG:
    Starting host 121 ..
        ...UPID:proxa3:00001FB3:00F2E185:57EE62A8:vzstart:121:user@DOMAIN.ORG:
    Machine 121 : running, cpu: 0% 

    waiting for machine sausage to come up .. hit ctrl+c to stop ping

now you can install docker manually. As a next step let's assume you would like to install docker on
multiple machines. We can create a runlist in a simple text file and each command in that list will
be executed on each machine. In this case we made a runlist that installs docker:

::

    > cat ~/runlist-docker
    sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
    sudo echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" > /etc/apt/sources.list.d/docker.list
    sudo apt-get update
    sudo apt-get install -y docker-engine

now we can use the prox command to install multiple machines:

::

    > prox new --runlist ~/runlist-docker --disk 8 sausage1 sausage2 sausage3
    Password for 'user':

    creating host sausage1 with ID 116 in pool SciComp
        ...UPID:proxa3:000039A6:0111B96E:57EEB19E:vzcreate:116:user@DOMAIN.ORG:
    creating host sausage2 with ID 118 in pool SciComp
        ...UPID:proxa3:000039B6:0111B980:57EEB19E:vzcreate:118:user@DOMAIN.ORG:
    creating host sausage3 with ID 121 in pool SciComp
        ...UPID:proxa3:000039C4:0111B991:57EEB19E:vzcreate:121:user@DOMAIN.ORG:
    Starting host 116 ..
    starting host 116, re-try 0
        ...UPID:proxa3:00003A04:0111BCB7:57EEB1A6:vzstart:116:user@DOMAIN.ORG:
    Machine 116 : running, cpu: 0% 
    Starting host 118 ..
        ...UPID:proxa3:00003AF7:0111BD3C:57EEB1A8:vzstart:118:user@DOMAIN.ORG:
    Machine 118 : running, cpu: 0% 
    Starting host 121 ..
        ...UPID:proxa3:00003BE2:0111BDC2:57EEB1A9:vzstart:121:user@DOMAIN.ORG:
    Machine 121 : running, cpu: -1% 

and after you are done with your work you can stop and then destroy these machines:

::

    > prox stop sausage1 sausage2 sausage3
    Password for 'user':

    UPID:proxa2:000060FE:01121EA2:57EEB2A1:vzstop:116:user@DOMAIN.ORG:
    UPID:proxa3:00006110:01121EB3:57EEB2A1:vzstop:118:user@DOMAIN.ORG:
    UPID:proxa4:00006127:01121EC6:57EEB2A1:vzstop:121:user@DOMAIN.ORG:

    > prox destroy sausage1 sausage2 sausage3
    Password for 'user':

    UPID:proxa2:000061C7:01122C18:57EEB2C4:vzdestroy:116:user@DOMAIN.ORG:
    UPID:proxa3:000061CB:01122C2A:57EEB2C4:vzdestroy:118:user@DOMAIN.ORG:
    UPID:proxa4:000061CF:01122C3B:57EEB2C4:vzdestroy:121:user@DOMAIN.ORG:

proxhostname.py
---------------

script runs inside newly deployed ProxMox VM or Container, queries promox API for correct hostname
according to MAC address found on the local system and set the new hostname

If you have an IPAM device (such as Infoblox) you just need to change the hostname on your Linux to
have dynamic DNS get you a new IP address. This allows you to deploy many hosts within seconds

tested with Ubuntu 14.04 and Ubuntu 16.04
