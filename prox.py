#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
#  deploy proxmox VMs from templates

import sys, os, subprocess, re, platform, getpass, argparse, logging
import time, warnings, easygui, random, json, requests, re

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import pyproxmox

logging.basicConfig(level=logging.WARNING)

__app__ = "Proxmox command line deployment tool"
__version__ = '0.9'
PROXHOST = 'proxa3.fhcrc.org'
REALM = 'FHCRC.ORG'
# REALM = 'pam'
MAILDOM = 'fredhutch.org'
LXCTEMPLATE = 'proxnfs:vztmpl/ubuntu-16.04-standard_16.04-1_amd64.tar.gz'
STORLOC = 'proxazfs'
STORNET = 'proxnfs'

homedir = os.path.expanduser("~")
cfgdir = os.path.join(homedir, '.proxmox')

j = requests.get('https://toolbox.fhcrc.org/json/sc_users.json').json()

def main():

    uselxc = True
    usegui = True
    
    if args.command == 'assist':
        if 'DISPLAY' in os.environ.keys() or sys.platform == 'win32':
            usegui = True
    
    if args.debug:
        print('Debugging ....')                                                  
        print(args, l)

    if args.command in ['straaange', 'oppptions']:
        prn("This feature is not yet implemented.", usegui)
        return False

    # getting login and password 
    user = getpass.getuser()
    #user='root'
    #pwd=''
    pwd = os.getenv('proxpw', '')
    if pwd == '':
        pwd = os.getenv('PROXPW', '')
        if pwd == '':
            pwd = getpwd("Password for '%s':" % user, usegui)
            if pwd == '':
                return False
    loginname = user + '@' + REALM

    a = pyproxmox.prox_auth(PROXHOST, loginname, pwd, True)
    if a.ticket is None:
        prn('Could not get an authentication ticket. Wrong password?', usegui)
        return False
    p = pyproxmox.pyproxmox(a)

    pool = p.getPools()['data'][0]['poolid']
    nodelist = p.getNodes()['data']
    nodes = []
    hosttempl = {}
    templlist = []
    ourmachines = {}

    for n in nodelist:
        node = n['node']
        nodes.append(node)
        # get list of containers and VMs
        conts = p.getContainers(node)['data']
        vms = p.getNodeVirtualIndex(node)['data']
        for c in conts:
            ourmachines[int(c['vmid'])] = [c['vmid'], c[
                'name'], c['type'], c['status'], node]
        for v in vms:
            # get VM templates
            # if v['name'].startswith('templ') or
            # v['name'].endswith('template'): # check for vm names
            if v['template'] == 1:
                hosttempl[v['name']] = [node, v['vmid']]
                templlist.append(v['name'])
            else:
                ourmachines[int(v['vmid'])] = [v['vmid'], v[
                    'name'], 'kvm', v['status'], node]

    # list of machine ids we want to take action on
    vmids = getvmids(ourmachines, args.hosts)
    if args.vmid != '':
        vmids.append(int(args.vmid))

    print('')
    
    if args.command == 'list' or (
        args.command in [
            'start',
            'stop',
            'destroy'] and not vmids):
        prn(' {0: <5} {1: <15} {2: <5} {3: <9} {4: <8}'.format(
            'vmid', 'name', 'type', 'status', 'node'))
        prn(' {0: <5} {1: <15} {2: <5} {3: <9} {4: <8}'.format(
            '----', '--------------', '----', '--------', '-------'))

        for k, v in ourmachines.items():
            prn(' {0: <5} {1: <15} {2: <5} {3: <9} {4: <8}'.format(*v))

    # ******************************************************************

    if args.command == 'assist':
        if not usegui:
            print('running "prox assist" command which will guide you '
              'through a number of choices, however no GUI is available')
            return False
            
        chce = []
        msg = ("Running 'prox assist'! Please select from the list "
               "below or 'Cancel' and run 'prox --help' for other options. "
               "Example: 'prox new mybox1 mybox2 mybox3' will create "
               "3 Linux machines.")
        chce = easygui.choicebox(msg, __app__,['New linux machine', 
        'New docker host', 'New virtual machine', 'List machines', 
        'Start machine', 'Stop machine', 'Modify machine', 
        'Destroy machine'])
        
        if not chce:
            return False
        
        if chce.startswith('New '):
            args.command = 'new'
            if chce != "New linux machine":
                uselxc = False
            else:                    
                msg = ("Please select the size of your machine. "
                       "Memory sizes are in MB, unless you add G "
                       "(e.g. 1G). Disk sizes are always in GB\n."
                       "Please start small, you can always resize."
                       )
                title = "Configuring Machine Size"
                fieldNames = ["Memory", "# Cores", "Disk Size"]
                fieldValues = ['512M', '2', '4G']
                fieldValues = easygui.multenterbox(msg, title,
                        fieldNames, fieldValues)
                args.mem, args.cores, args.disk = fieldValues
                                    
        elif chce.startswith('List '):
            args.command = 'list'
        elif chce.startswith('Start '):
            args.command = 'start'                
        elif chce.startswith('Stop '):
            args.command = 'stop'
        elif chce.startswith('Modify '):
            args.command = 'modify'
        elif chce.startswith('Destroy '):
            args.command = 'destroy'                
        else:
            args.command = 'assist'
                                    
    # ******************************************************************
    # setting some variables based on input from args.assist 
    ## settings for LXC containers only    
    
    if "G" in args.mem.upper():
        lxcmem = int(re.sub("[^0-9^.]", "", args.mem))*1024
    else:
        lxcmem = int(re.sub("[^0-9^.]", "", args.mem))
    lxccores = int(re.sub("[^0-9^.]", "", args.cores))
    lxcdisk = int(re.sub("[^0-9^.]", "", args.disk))
    
    # ******************************************************************

    if args.command == 'start':

        if not vmids:
            vmids.append(input('\nenter vmid to start:'))
            if not vmids:
                prn('vmid is required', usegui)
                return False

        for vmid in vmids:
            machine = ourmachines[vmid]
            if machine[3] == 'running':
                prn('Machine "%s" is already running!' % machine[1], usegui)
                return False
            if machine[2] == 'kvm':
                ret = p.startVirtualMachine(machine[4], vmid)['data']
                print('...%s' % ret)
                for i in range(15):
                    time.sleep(1)
                    ret = p.getVirtualStatus(machine[4], vmid)['data']
                    print('Machine {0: <4}: {1}, cpu: {2:.0%} '.format(
                            vmid, ret['status'], ret['cpu']))
                    if ret['cpu'] > 0.2:
                        break
            else:
                ret = p.startLXCContainer(machine[4], vmid)['data']
                print('...%s' % ret)
                for i in range(15):
                    time.sleep(1)
                    ret = p.getContainerStatus(machine[4], vmid)['data']
                    prn('Machine {0: <4}: {1}, cpu: {2:.0%} '.format(
                            vmid, ret['status'], ret['cpu']))
                    if ret['status'] == 'running':
                        break

        pingwait(machine[1])

    # ******************************************************************

    if args.command == 'stop':
        if not vmids:
            vmids.append(input('\nenter vmid to start:'))
            if not vmids:
                prn("no vmid entered", usegui)
                return False
        for vmid in vmids:
            machine = ourmachines[vmid]
            if machine[3] == 'stopped':
                prn('Machine "%s" is already stopped!' % machine[1], usegui)
                continue
            if machine[2] == 'kvm':
                ret = p.stopVirtualMachine(machine[4], vmid)['data']
                if ret:
                    print(ret)
                else:
                    prn("host with id %s not yet stopped!" % vmid, usegui)
                for i in range(15):
                    time.sleep(1)
                    ret = p.getVirtualStatus(machine[4], vmid)['data']
                    prn(
                        'Machine {0: <4}: {1}, cpu: {2:.0%} '.format(
                            vmid, ret['status'], ret['cpu']))
                    if ret['status'] == 'stopped':
                        break
            else:
                ret = p.stopLXCContainer(machine[4], vmid)['data']                
                print(ret)

    # ******************************************************************

    if args.command == 'modify':
        if not vmids:
            vmids.append(input('\nenter vmid to modify:'))
            if not vmids:
                prn("no vmid entered", usegui)
                return False
        for vmid in vmids:
            machine = ourmachines[vmid]
            if machine[2] == 'kvm':
                #ret = p.stopVirtualMachine(machine[4], vmid)['data']
                prn("currently cannot modify virtual machines.", usegui)
            else:
                #ret = p.stopLXCContainer(machine[4], vmid)['data']
                ret = p.getContainerConfig(machine[4], vmid)['data']
                rootstr=ret['rootfs']
                post_data = {}
                post_data['cpulimit'] = lxccores
                post_data['memory'] = lxcmem
                post_data['rootfs'] = re.sub(r",size=[0-9]+G", ",size=%sG" 
                                                 % lxcdisk, rootstr)
                #volume=proxazfs:subvol-126-disk-1,size=30G                            
                ret = p.setLXCContainerOptions(machine[4], vmid, post_data)['data']
                if iserr(ret,500):
                    if machine[3] == 'running':          
                        prn("Running machines can currently only be modified "
                            "through the web interface.\nStop the machine "
                            "and try again or use the web interface or "
                            "ask a systems administrator to do this for you."
                            , usegui                            
                        )
                    else:
                        print ('Error 50X, could not modify machine')
                else:
                    if ret == 0:
                        ret = p.getContainerConfig(machine[4], vmid)['data']
                        print ('Machine reconfigured. New settings '
                               'cores: %s, mem: %s MB, rootfs: %s ' 
                               % (ret['cpulimit'], ret['memory'], 
                                 ret['rootfs'])
                                )                        
                    else:
                        print(ret)
                
    # ******************************************************************

    if args.command == 'destroy':
        if not vmids:
            vmids.append(input('\nenter vmid to start:'))
            if not vmids:
                return False
        for vmid in vmids:
            if not int(vmid) in ourmachines:
                prn('machine with id %s does not exist' % vmid)
                return False
            machine = ourmachines[vmid]
            if machine[3] != 'stopped':
                print(
                'Machine "%s" needs to be stopped before it can be destroyed!' %
                    machine[1])
                return False
            if machine[2] == 'kvm':
                ret = p.deleteVirtualMachine(machine[4], vmid)['data']
                print(ret)
            else:
                ret = p.deleteLXCContainer(machine[4], vmid)['data']
                print(ret)

    # ******************************************************************

    if args.command == 'new':
        mynode = random.choice(nodes)
        mynode = 'proxa3'
        print('installing on node "%s"' % mynode)

        myhosts = args.hosts
        if len(myhosts) == 0:
            msg=("enter the hostname(s) you want to deploy (separated by "
                  "space, no domain name")
            myhosts = def_input(msg, usegui)
            myhosts = myhosts.split(' ')

        if not myhosts or myhosts == '':
            prn('hostname(s) are required', usegui)
            return False

        desc = 'testing'
        if len(args.hosts) == 0:
            msg=("What is the description/purpose of the system(s)? (e.g. "
                 "testing, development, other")
            desc = def_input(msg, 'testing', usegui)

        storage = STORLOC
        if len(args.hosts) == 0:
            if yn_choice(
                "Do you want to use local storage on '%s' (for better performance) ?" %
                    mynode) == 'n':
                storage = STORNET

        newhostids = []
        # deploy a container
        if uselxc:
            newcontid = 0
            for h in myhosts:
                oldcontid = newcontid
                for i in range(10):
                    newcontid = p.getClusterVmNextId()['data']
                    if oldcontid != newcontid:
                        break
                    time.sleep(1)

                prn(
                    'creating host %s with ID %s in pool %s' %
                    (h, newcontid, pool))

                post_data = {
                    'ostemplate': LXCTEMPLATE,
                    'cpulimit': lxccores,
                    'memory': lxcmem,
                    'rootfs': lxcdisk,
                    'vmid': newcontid,
                    'description': build_notes(user, pool, desc),
                    'hostname': h,
                    'password': pwd,
                    'storage': storage,
                    'pool': pool,
                    'net0': 'name=eth0,bridge=vmbr0,ip=dhcp'}

                ret = p.createLXCContainer(mynode, post_data)['data']
                print('    ...%s' % ret)

                newhostids.append(newcontid)

            if yn_choice("Do you want to start these machines now?"):
                for n in newhostids:
                    print('Starting host %s ..' % n)
                    ret = None
                    for i in range(15):
                        ret = p.startLXCContainer(mynode, n)['data']
                        if ret:
                            print('    ...%s' % ret)
                            break                        
                        time.sleep(1)
                        print('starting host %s, re-try %s' % (n, i))
                    if not ret:
                        print("Failed starting host id %s !" % n)
                        return False

                    for i in range(15):
                        time.sleep(1)
                        ret = p.getContainerStatus(mynode, n)['data']
                        prn(
                            'Machine {0: <4}: {1}, cpu: {2:.0%} '.format(
                                n, ret['status'], ret['cpu']))
                        if ret['status'] == 'running':
                            break
                    if not ret:
                        prn("Failed starting host id %s !" % n)
                        return False

                pingwait(myhosts[0])

        else:
            # deploy a VM from Image

            myimage = args.image
            if myimage == '':
                if not usegui:
                    msg="Please enter a template name"
                    myimage = def_input(msg, ','.join(templlist))
                else:
                    msg=("Please enter a template name or just hit enter "
                         "to select from a list:")
                    myimage = easygui.choicebox(msg, __app__,
                    ','.join(templlist))

            if myimage == ','.join(templlist) and usegui:
                myimage = easygui.choicebox(
                    'You must select a image or template name', __app__, templlist)

            if not myimage or myimage == ','.join(templlist) or myimage == '':
                prn('image is required')
                return False

            notes = build_notes(user, pool)
            for h in myhosts:
                newvmid = p.getClusterVmNextId()['data']
                prn(
                    'creating host %s with VM ID %s in pool %s' %
                    (h, newvmid, pool))
                post_data = {
                    'newid': newvmid, 
                    'name': h, 
                    'description': notes,
                    'pool': pool
                    }
                ret = p.cloneVirtualMachine(
                    hosttempl[myimage][0],
                    hosttempl[myimage][1],
                    post_data)['data']
                print('    ...' + ret)
                newhostids.append(newvmid)

            if yn_choice("Do you want to start these machines now?"):
                for n in newhostids:
                    print('Starting host %s ..' % n)
                    ret = p.startVirtualMachine(
                        hosttempl[myimage][0], n)['data']
                    print('    ...' + ret)

                pingwait(myhosts[0])
            else:
                prn('Please start the host with "prox start <hostname>"', usegui)
                                
    print('')


def def_input(message, defaultVal, usegui=False):
    if usegui:
        if not defaultVal:
            defaultVal = ''
        return easygui.enterbox(message, __app__, defaultVal)
    else:
        if defaultVal:
            return input("%s [%s]:" % (message, defaultVal)) or defaultVal
        else:
            return input("%s " % (message))

def yn_choice(message, default='y', usegui=False):
    if usegui:
        return easygui.boolbox(message, __app__)
    else:
        choices = 'Y/n' if default.lower() in ('y', 'yes') else 'y/N'
        choice = input("%s (%s) " % (message, choices))
        values = ('y', 'yes', '') if default == 'y' else ('y', 'yes')
        return choice.strip().lower() in values

def prn(message, usegui=False):
    if usegui:
        pwd = easygui.msgbox(message,__app__)
    else:
        print(message)

def getpwd(message, usegui=False):
    pwd = ''
    if usegui:
        pwd = easygui.passwordbox(message, __app__)
    else:
        pwd = getpass.getpass(message)
    if pwd == '':
        print('Password is required')
    return pwd

def iserr(result, httperror=400):
    """ checking return codes from REST API, if error data returns >400 """
    if isinstance(result, int):
        if result >= httperror:
            return True
    return False

def getvmids(ourmachines, hostnames):
    ids = []
    for k, v in ourmachines.items():
        for h in hostnames:
            if v[1] == h:
                ids.append(int(v[0]))
    return ids


def pingwait(hostname):
    print(
        '\nwaiting for machine  %s to come up .. hit ctrl+c to stop ping' %
        hostname)
    while True:
        ret = os.system('ping -w 7 %s' % hostname)
        if ret in [
                0, 2]:  # 2=ctrl+c, 256=unreachable, 512=unknown host, not in DNS
            break
        time.sleep(3)
    if ret == 0:
        print('Host %s is up and running, you can now connect' % hostname)

def build_notes(user, pool, desc='testing'):
    # desc =
    # owner             : _adm/infosec
    # technical_contact : jli@fredhutch.org
    # billing_contact   : cloudops@fredhutch.org
    # description       : firewall - inside interface in dedicated subnet
    # sle               : business_hours=24x7 / grant_critical=no /
    #                     phi=no / pii=no / publicly_accessible=no
    # Tenancy           : default
    mail=jsearchone(j,'uid',user,'mail')
    division=jsearchone(j,'uid',user,'division')
    dept_manager=jsearchone(j,'uid',user,'dept_manager')
    mgr_mail=jsearchone(j,'uid',dept_manager,'mail')
    
    notes = (
    "owner: %s/%s\n" 
    "technical_contact: %s\n"
    "billing_contact: %s\n"
    "description: %s\n"
    "sle: business_hours=weekdays" % (division, pool, mail, mgr_mail, desc)
    )
    return notes

def jsearchone(json,sfld,search,rfld):
    """ return the first search result of a column based search """
    for j in json:
        if j[sfld]==search:
            return j[rfld].strip()

def uniq(seq):
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return keys.keys()

def ping(hostname, timeout):
    if platform.system() == "Windows":
        command = "ping " + hostname + " -n 1 -w " + str(timeout * 1000)
    else:
        command = "ping -i " + str(timeout) + " -c 1 " + hostname
    proccess = subprocess.Popen(command, stdout=subprocess.PIPE)
    matches = re.match(
        '.*time=([0-9]+)ms.*',
        proccess.stdout.read(),
        re.DOTALL)
    if matches:
        return matches.group(1)
    else:
        return False


def isServiceUp(host, port):
    captive_dns_addr = ""
    host_addr = ""
    try:
        host_addr = socket.gethostbyname(host)
        if (captive_dns_addr == host_addr):
            return False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((host, port))
        s.close()
    except:
        return False
    return True


def send_mail(
        to,
        subject,
        text,
        attachments=[],
        cc=[],
        bcc=[],
        smtphost="",
        fromaddr=""):

    if sys.version_info[0] == 2:
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEBase import MIMEBase
        from email.MIMEText import MIMEText
        from email.Utils import COMMASPACE, formatdate
        from email import Encoders
    else:
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email.utils import COMMASPACE, formatdate
        from email import encoders as Encoders
    from string import Template
    import socket
    import smtplib

    if not isinstance(to, list):
        print("the 'to' parameter needs to be a list")
        return False
    if len(to) == 0:
        print("no 'to' email addresses")
        return False

    myhost = socket.getfqdn()

    if smtphost == '':
        smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')

    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
            '.'.join(myhost.split(".")[-2:])  # extract domain from host
    tc = 0
    for t in to:
        if '@' not in t:
            # if no email domain given use domain from local host
            to[tc] = t + '@' + '.'.join(myhost.split(".")[-2:])
        tc += 1

    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)
    message['Bcc'] = COMMASPACE.join(bcc)

    body = Template(
        'This is a notification message from $application, running on \n' +
        'host $host. Please review the following message:\n\n' +
        '$notify_text\n\n')
    host_name = socket.gethostname()
    full_body = body.substitute(
        host=host_name.upper(),
        notify_text=text,
        application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            'attachment; filename="%s"' %
            os.path.basename(f))
        message.attach(part)

    addresses = []
    for x in to:
        addresses.append(x)
    for x in cc:
        addresses.append(x)
    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(smtphost)
    smtp.sendmail(fromaddr, addresses, message.as_string())
    smtp.close()

    return True


class Settings(easygui.EgStore):

    def __init__(self, filename):  # filename is required
        #-------------------------------------------------
        # Specify default/initial values for variables that
        # this particular application wants to remember.
        #-------------------------------------------------
        self.userId = ""
        self.targetServer = ""

        #-------------------------------------------------
        # For subclasses of EgStore, these must be
        # the last two statements in  __init__
        #-------------------------------------------------
        self.filename = filename  # this is required
        self.restore()            # restore values from the storage file if possible


def parse_arguments():
    """
    Gather command-line arguments.
    """
       
    parser = argparse.ArgumentParser(prog='prox ',
        description='a tool for deploying resources from proxmox ' + \
            '(LXC containers or VMs)')
    parser.add_argument( 'command', type=str, default='assist', nargs='?',
        choices=['new','list','start','stop', 'modify','destroy', 'assist'],
        help="a command to be executed. (new, list, start , stop , modify, destroy, assist")
    parser.add_argument('hosts', action='store', default=[],  nargs='*',
        help='hostname(s) of VM/containers (separated by space), ' +
              '   example: prox new host1 host2 host3')
    parser.add_argument('--vmid', '-v', dest='vmid', action='store', default='', 
        help='vmid, proxmox primary key for a container or vm')
    parser.add_argument('--image', '-i', dest='image', action='store', default='', 
        help='QEMU / KVM image we clone to create a new VM')
    parser.add_argument('--mem', '-m', dest='mem', action='store', default='512',
        help='Memory allocation for the machine, e.g. 4G or 512 Default: 512')
    parser.add_argument('--cores', '-c', dest='cores', action='store', default='2', 
        help='Number of cores to be allocated for the machine. Default: 2')       
    parser.add_argument('--disk', '-d', dest='disk', action='store', default='4', 
        help='disk storage allocated to the machine. Default: 4')       
    parser.add_argument( '--storenet', '-n', dest='stornet', action='store_true', default=False,
        help="use network storage (nfs, ceph) instead of local storage")
    parser.add_argument( '--debug', '-g', dest='debug', action='store_true', default=False,
        help="verbose output for all commands")
    parser.add_argument('--mailto', '-e', dest='mailto', action='store', default='', 
        help='send to this email address to notify of a new deployment.')

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    try:
        main()
    except KeyboardInterrupt:
        print('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
