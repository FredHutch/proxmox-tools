
BASEDIR:=$(shell dab basedir)

all: info/init_ok
	dab bootstrap
	dab install python3-pip python3-dev python3-setuptools gcc vim mc software-properties-common libtcl8.5
	echo BASEDIR: ${BASEDIR}
	sed -e 's/^PermitRootLogin prohibit-password/PermitRootLogin yes/' -i ${BASEDIR}/etc/ssh/sshd_config
	mkdir -p ${BASEDIR}/etc/chef
	mkdir -p ${BASEDIR}/opt/chef/tmp
	mkdir -p ${BASEDIR}/var/log/chef
	echo 'chef_server_url "https://chef.fhcrc.org/organizations/cit"' >> ${BASEDIR}/etc/chef/client.rb
	echo 'validation_client_name "cit-validator"' >> ${BASEDIR}/etc/chef/client.rb
	echo 'log_location "/var/log/chef/client.log"' >> ${BASEDIR}/etc/chef/client.rb
	rm -f ${BASEDIR}/opt/chef/tmp/*
	wget -P ${BASEDIR}/opt/chef/tmp https://packages.chef.io/stable/ubuntu/12.04/chef_12.14.77-1_amd64.deb
	ln -s /opt/chef/tmp/chef_12.14.77-1_amd64.deb ${BASEDIR}/opt/chef/tmp/chef_amd64.deb
	mkdir -p ${BASEDIR}/root/.chef ${BASEDIR}/root/bin/
	cp /root/bin/chef-bootstrap.sh ${BASEDIR}/root/bin/
	cp /root/.chef/* ${BASEDIR}/root/.chef/
	cp /root/cfg/49-remote.conf ${BASEDIR}/etc/rsyslog.d/
	dab finalize

info/init_ok: dab.conf
	dab init
	touch $@

.PHONY: clean
clean:
	dab clean
	rm -f *~

.PHONY: dist-clean
dist-clean:
	dab dist-clean
	rm -f *
