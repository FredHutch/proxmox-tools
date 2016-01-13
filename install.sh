#! /bin/bash

mkdir -p /root/bin
cp *.py /root/bin

if [[ -d /etc/systemd/system ]]; then
  cp proxhostname.service /etc/systemd/system/
  systemctl enable proxhostname.service
elif [[ -d /etc/init ]]; then
  cp proxhostname.conf /etc/init/
fi

