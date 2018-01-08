## Debian Jessie minimal Template

- based on Debootstrap minimal install
- adds Python for use with Ansible for example
- removes Postfix to make room for an alternate mail server
- temporarily permits root login with password for easy initialisation
  - intended to receive proper SSHD settings and keys via Ansible
- small 117 MB compressed template
- consumes about 250 MB on disk for a running container
