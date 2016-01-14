#! /bin/bash

mkdir -p /root/bin
cp *.py /root/bin

ubuntuver=$( lsb_release -r | awk '{ print $2 }' | sed 's/[.]//' )

if [[ $ubuntuver -ge 1504 ]]; then
  cp proxhostname.service /etc/systemd/system/
  systemctl enable proxhostname.service
else
  cp proxhostname.conf /etc/init/
fi

