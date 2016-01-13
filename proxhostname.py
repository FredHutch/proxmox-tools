#! /usr/bin/env python3

# setting the proxmox VM hostname according to proxmox config

import sys, os, json, fileinput, socket, pyproxmox
#from proxmoxer import ProxmoxAPI

PROXHOST='proxmox.fhcrc.org'
NODES=['euler', 'lagrange']

def getmac(interface):
    try:
        mac = open('/sys/class/net/'+interface+'/address').readline().upper()
    except:
        mac = "00:00:00:00:00:00"
    return mac[0:17]

def getmacs():
    macs = []
    nics = os.listdir('/sys/class/net/')
    for n in nics:
        macs.append(getmac(n))
    return macs

def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

try:
    user, pwd = open(getScriptPath()+'/creds').readline().strip().split("|")
except:
    print('Could not find creds file. Exiting.')
    sys.exit()

#proxmox = ProxmoxAPI(PROXHOST, user=user, password=pwd, verify_ssl=False)
    
hostname=socket.gethostname()
newhost=hostname

a = pyproxmox.prox_auth(PROXHOST, user, pwd,False)
p = pyproxmox.pyproxmox(a)

mymacs = getmacs()

for node in NODES:
    vms = p.getNodeVirtualIndex(node)['data']
    for v in vms:
        j = p.getVirtualConfig(node,v['vmid'])
        mac=j['data']['net0'].split('=')[1].split(',')[0]
        if mac.upper() in mymacs:
            print('%s: %s' % (v['name'], mac))
            newhost=v['name'].lower()
    vms = p.getNodeContainerIndex(node)['data']
    for v in vms:
        j = p.getContainerConfig(node,v['vmid'])
        mac=j['data']['netif'].split(',')[1].split('=')[1]
        if mac.upper() in mymacs:
            print('%s: %s' % (v['name'], mac))
            newhost=v['name'].lower()

if newhost != hostname: 
    with fileinput.FileInput('/etc/hosts', inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace("127.0.0.1       %s" % hostname, "127.0.0.1       %s" % newhost), end='')
    f = open('/etc/hostname','w')
    f.write(newhost+'\n')
    f.close()
    os.system('hostname %s' % newhost)
    os.system('dhclient -r')
    os.system('dhclient')
    print ('changed hostname to %s' % newhost)
else:
    print ('hostname for this MAC is in line with proxmox db')
