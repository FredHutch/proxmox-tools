#! /bin/bash

#### prepare install for KVM ##### 

apt-get install -y python3-pip vim mc chef software-properties-common qemu-guest-agent
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
cp creds /root/bin

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


