#! /bin/bash

#### prepare install for KVM ##### 
DEBIAN_FRONTEND=noninteractive apt-get install -y -q python3-pip vim mc software-properties-common qemu-guest-agent
wget -P /tmp https://packages.chef.io/stable/ubuntu/12.04/chef_12.14.77-1_amd64.deb
dpkg -i /tmp/chef_12.14.77-1_amd64.deb
sed -e 's/^PermitRootLogin prohibit-password/PermitRootLogin yes/' -i /etc/ssh/sshd_config
echo 'APT::Get::AllowUnauthenticated "true";' > ${BASEDIR}/etc/apt/apt.conf.d/99aptnokey
mkdir -p /etc/chef
mkdir -p /var/log/chef
echo 'chef_server_url "https://chef.fhcrc.org/organizations/cit"' > /etc/chef/client.rb
echo 'validation_client_name "cit-validator"' >> ${BASEDIR}/etc/chef/client.rb
echo 'log_location "/var/log/chef/client.log"' >> ${BASEDIR}/etc/chef/client.rb
### end prepare 

mkdir -p /root/bin/
cp proxhostname.py /root/bin/
cp pyproxmox.py /root/bin

ubuntuver=$( lsb_release -r | awk '{ print $2 }' | sed 's/[.]//' )

if [[ $ubuntuver -ge 1504 ]]; then
  cp proxhostname.service /etc/systemd/system/
  systemctl enable proxhostname.service
else
  cp proxhostname.conf /etc/init/
fi

### copy chef cert
mkdir -p /root/.chef 
scp root@proxa1:/root/.chef/cit-validator.pem /root/.chef/

### copy proxmoxer creds file
scp root@proxa1:/root/bin/creds /root/bin/

