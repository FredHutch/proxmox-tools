Promox helper scripts
==

proxhostname.py
-- 

script runs inside newly deployed ProxMox VM or Container, queries promox API for correct hostname according to MAC address found on the local system and set the new hostname

If you have an IPAM device (such as Infoblox) you just need to change the hostname on your Linux to have dynamic DNS get you a new IP address. This allows you to deploy many hosts within seconds

tested with Ubuntu 14.04 and Ubuntu 16.04 alpha 1

