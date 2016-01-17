#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
#  deploy proxmox VMs from templates  

import sys, os, subprocess, re, platform, getpass, argparse, logging, time, warnings
import easygui

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    import pyproxmox

logging.basicConfig( level = logging.WARNING )

__app__ = "Proxmox command line deployment tool"
__version__= '0.9'
PROXHOST='proxmox.fhcrc.org'
REALM = 'FHCRC.ORG'

homedir = os.path.expanduser("~")
cfgdir = os.path.join(homedir,'.proxmox')

def main():

    if args.debug:
        print('Debugging ....')
        print(args,l)

    if args.command in  ['start', 'stop']:
        print("This feature is not yet implemented.")
        return False

    print ('Executing command "prox %s"' % args.command)

    user=getpass.getuser()
    pwd=getpass.getpass("Password for '%s':" % user)
    user=user+'@'+ REALM 

    a = pyproxmox.prox_auth(PROXHOST, user, pwd, False)
    p = pyproxmox.pyproxmox(a)

    pool=p.getPools()['data'][0]['poolid']

    nodes = []
    nodelist=p.getNodes()['data']
    for n in nodelist:
        nodes.append(n['node'])

    hosttempl={}
    templlist=[]
    for node in nodes:
        vms = p.getNodeVirtualIndex(node)['data']
        for v in vms:
            #if v['name'].startswith('templ') or v['name'].endswith('template'): # check for vm names
            if v['template'] == 1:
                hosttempl[v['name']]=[node,v['vmid']]
                templlist.append(v['name'])

    print('')
    if args.command == 'deploy':
        myimage=args.image
        if myimage == '':
            if not 'DISPLAY' in os.environ.keys():
                print('Please enter a template name:')
            else:
                print('Please enter a template name or just hit enter to select from a list:')
            myimage = def_input( 'enter template:', ','.join(templlist))

        if myimage == ','.join(templlist) and 'DISPLAY' in os.environ.keys():
            myimage = easygui.choicebox('You must select a image or template name',__app__,templlist)

        if not myimage or myimage==','.join(templlist) or myimage=='':
            print('image is required')
            return False

        myhosts=args.hosts
        if len(myhosts) == 0:
            print ('enter the hostname(s) you want to deploy (separated by space, no domain name)')
            myhosts = input( 'enter hostname(s):')
            myhosts = myhosts.split(' ')

        if myhosts == '':
            print('hostname(s) are required')
            return False

        newvmids=[]
        for h in myhosts:
            newvmid=p.getClusterVmNextId()['data']
            print('creating host %s with VM ID %s in pool %s' % (h,newvmid,pool))
            post_data = [('newid',newvmid),('name',h),('pool',pool)]
            ret = p.cloneVirtualMachine(hosttempl[myimage][0],hosttempl[myimage][1],post_data)
            print('    ...' + ret['data'])
            newvmids.append(newvmid)

        if yn_choice("Do you want to start these VMs now?"):
            for n in newvmids:
                print ('Starting VM %s ..' % n)
                ret = p.startVirtualMachine(hosttempl[myimage][0],n)
                print('    ...' + ret['data'])

            print ('\nwaiting for host %s to come up .. hit ctrl+c to stop ping' % myhosts[0])
            while True:
                ret=os.system('ping -w 7 %s' % myhosts[0])
                if ret in [0,2]:  #2=ctrl+c, 256=unreachable, 512=unknown host, not in DNS
                    break
                time.sleep(3)
            if ret==0:
                print ('Host %s is up and running, you can now connect' % myhosts[0])
        else:
            print('Please start the VMs with "prox start <hostname>" or via proxmox webinterface')



def def_input( message, defaultVal ):
    if defaultVal:
        return input( "%s [%s]:" % (message,defaultVal) ) or defaultVal
    else:
        return input( "%s " % (message) )
    
def uniq(seq):
   # Not order preserving
   keys = {}
   for e in seq:
       keys[e] = 1
   return keys.keys()

def yn_choice(message, default='y'):
    choices = 'Y/n' if default.lower() in ('y', 'yes') else 'y/N'
    choice = input("%s (%s) " % (message, choices))
    values = ('y', 'yes', '') if default == 'y' else ('y', 'yes')
    return choice.strip().lower() in values

def ping(hostname,timeout):
    if platform.system() == "Windows":
        command="ping "+hostname+" -n 1 -w "+str(timeout*1000)
    else:
        command="ping -i "+str(timeout)+" -c 1 " + hostname
    proccess = subprocess.Popen(command, stdout=subprocess.PIPE)
    matches=re.match('.*time=([0-9]+)ms.*', proccess.stdout.read(),re.DOTALL)
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

def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):

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

    if not isinstance(to,list):
        print("the 'to' parameter needs to be a list")
        return False    
    if len(to)==0:
        print("no 'to' email addresses")
        return False
    
    myhost=socket.getfqdn()

    if smtphost == '':
        smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')
        
    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
           '.'.join(myhost.split(".")[-2:]) #extract domain from host
    tc=0
    for t in to:
        if '@' not in t:
            # if no email domain given use domain from local host
            to[tc]=t + '@' + '.'.join(myhost.split(".")[-2:])
        tc+=1

    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)
    message['Bcc'] = COMMASPACE.join(bcc)

    body = Template('This is a notification message from $application, running on \n' + \
            'host $host. Please review the following message:\n\n' + \
            '$notify_text\n\n'
            )
    host_name = socket.gethostname()
    full_body = body.substitute(host=host_name.upper(), notify_text=text, application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
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
    parser.add_argument( 'command', type=str, default='deploy', nargs='?',
        help="a command to be executed. (deploy, start, stop)")
    parser.add_argument('--hosts', '-n', dest='hosts', action='store', default=[],  nargs='*',
        help='hostnames of your new VM/containers')
    parser.add_argument('--image', '-i', dest='image', action='store', default='', 
        help='image we use to clone')    
    parser.add_argument( '--debug', '-d', dest='debug', action='store_true', default=False,
        help="do not send an email but print the result to  console")
    parser.add_argument('--mailto', '-m', dest='mailto', action='store', default='', 
        help='send email address to notify of a new deployment.')

    return parser.parse_args()

if __name__=="__main__":
    args = parse_arguments()
    try:
        main()
    except KeyboardInterrupt:
        print ('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
