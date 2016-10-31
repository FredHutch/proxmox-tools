docker support inside lxc containers 
==

In the proxmox default config docker containers do not run inside LXC containers.
Docker has to be run in slower and more cumbersome KVM instances.

Please copy the configurations in /etc/ and /usr/ to allow docker inside lxc 
containers.

Warning: these settings are intended for development environments as the reduce
security


