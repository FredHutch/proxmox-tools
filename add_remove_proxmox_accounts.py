#! /usr/bin/env python3

"""
automating adding and deleting proxmox users based on content of 
an external database, in this case a json file.
"""

import sys, os, json, requests, subprocess

# job titles that do not require an account. 
titignore = ["Program Assistant", "Data Coordinator", "Project Coordinator", 
             "Administrative Assistant", "Administrative Coordinator", 
             "Office Worker", "Data Operations Manager", 
             "Clinical Research Coordinator", "Administrative Manager", 
             "Data Entry Operator", "Clinical Research Nurse", 
             "Veterinary Technician", "Animal Equipment Preparer", 
             "Program Administrator", "Senior Project Manager", 
             "Coordinating Center Manager", "Animal Technician", 
             "Member Emeritus", "Nurse Manager", "Financial Analyst", 
             "Yoga Teacher", ""]

# the user database of potential scientific computing users
j = requests.get('https://toolbox.fhcrc.org/json/sc_users.json').json()


def main():

    # adding groups ##########################################

	groups = uniq(jget(j, 'pi_dept'))
	groups_add, groups_remove = listcompare('/var/tmp/groups_last.json', groups)
	
	print("\nAdding %s groups/pools...:" % len(groups_add),groups_add)
	if len(groups_add) <= 100: 
		for g in groups_add:
			d = jsearchone(j,'pi_dept',g,'department')
			s = ''
			s = s + 'pvesh create /pools -poolid %s -comment "%s"\n' % (g,d.strip())
			s = s + 'pveum groupadd %s -comment "%s"\n' % (g,d.strip())
			s = s + 'pveum aclmod /pool/%s/ -group %s -role PVEAdmin\n' % (g,g)
			s = s + 'pveum aclmod /storage/proxazfs/ -group %s -role PVEDatastoreUser\n' % g
			s = s + 'pveum aclmod /storage/proxnfs/ -group %s -role PVEDatastoreUser\n' % g
			print(s)
			ret = run_script(s, output=True)
			if ret > 0:
				print('******** Error : %s' % ret)
	else:
		print('Error: will not add batches of more than 100 groups')

			
	# save the list of currently processed groups
	with open('/var/tmp/groups_last.json', 'w') as outfile:
		json.dump(groups, outfile)

    # adding users #########################################

	uids = uniq(jget(j, 'uid'))
	uids_add, uids_del = listcompare('/var/tmp/uids_last.json', uids)


	# adding new users but never more than 1000
	x = len(uids_add) - 1
	if x > 100: x = 100
	print("\nAdding %s users...:" % len(uids_add), uids_add[0:x])
	n = 1
	if len(uids_add) <= 1000: 
		for uid in uids_add:
			print('%s: %s' % (n,uid))
			# ignore some jobtitles 
			if jsearchone(j,"uid",uid,"mail") == "" or jsearchone(j,"uid",uid,"title") in titignore:
				continue
				
			##### this is too long, /etc/pve/user.cfg can only be 128K
			#s = 'pveum useradd %s@FHCRC.ORG -email %s -firstname %s -lastname %s -groups %s -comment "%s"' % \
			#      (uids[n],mails[n], givenNames[n], sns[n], pi_depts[n], departments[n].strip())
				
			s = 'pveum useradd %s@FHCRC.ORG -groups %s' % (uid, jsearchone(j,"uid",uid,"pi_dept"))
			ret = run_script(s, output=True)
			n+=1
			if ret > 0:
				print('******** Error : %s' % ret)
	else:
		print('Error: will not add batches of more than 1000 users')

	# deleting diabled users but never more than 10
	print("\nDeleting %s users...:" % len(uids_del),uids_del)
	if len(uids_del) <= 10: 
		for uid in uids_del:
			print('test: del user %s' % uid)
			break
			s = 'pveum userdel %s@FHCRC.ORG ' % uid
			ret = run_script(s, output=True)
			if ret > 0:
				print('******** Error : %s' % ret)
	else:
		print('Error: will not delete more than 1000 users at a time')

	# save the list of currently processed uids 
	with open('/var/tmp/uids_last.json', 'w') as outfile:
		json.dump(uids, outfile)


########################################################################

# some helper functions

def listcompare(oldjsonfile,newlist):
	""" compares a list with a previously saved list and returns
	    a list of newly add items and a list of removed items.
	"""
	addedlist, removedlist = newlist, []
	if os.path.exists(oldjsonfile):
		with open(oldjsonfile, 'r') as f:
			oldlist=json.load(f)
			addedlist = [item for item in newlist if item not in oldlist]
			removedlist = [item for item in oldlist if item not in newlist]
	return addedlist, removedlist

def jsearch(json,sfld,search,rfld):
    """ return a list of values from a column based on a search """
    lst=[]
    for j in json:
        if j[sfld]==search or search == '*':
            lst.append(j[rfld].strip())
    return lst

def jsearchone(json,sfld,search,rfld):
    """ return the first search result of a column based search """
    for j in json:
        if j[sfld]==search:
            return j[rfld].strip()

def jget(json,rfld):
    """ return all values in one column """
    lst=[]
    for j in json:
        if j[rfld].strip() != "":
            lst.append(j[rfld].strip())
    return lst

def uniq(seq):
    """ remove duplicates from a list """ 
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return list(keys.keys())

class ScriptException(Exception):
    def __init__(self, returncode, stdout, stderr, script):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        Exception.__init__('Error in script')

def run_script(script, output=True, stdin=None):
    """Returns (stdout, stderr), raises error on non-zero return code"""
    # Note: by using a list here (['bash', ...]) you avoid quoting issues, as the 
    # arguments are passed in exactly this order (spaces, quotes, and newlines won't
    # cause problems):
    stdout = ""
    for line in script.split('\n'):
        if output:
            try:
                if line:
                    print("************* Executing command: %s" % line)
                    stdout = subprocess.call(line,shell=True)
            except:
                print("Error executing command: %s" % line)
                print("Error: %s" % stdout)
        else:
            proc = subprocess.Popen(['bash', '-c', line],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode:
                raise ScriptException(proc.returncode, stdout, stderr, script)
    return stdout


def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):
    """ sends email, perhaps with attachment """

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


def parse_arguments():
    """
    Gather command-line arguments.
    """
    pass

    #parser = argparse.ArgumentParser(prog='prox ',
        #description='a tool for deploying resources from proxmox ' + \
            #'(LXC containers or VMs)')
    #parser.add_argument( 'command', type=str, default='deploy', nargs='?',
        #help="a command to be executed. (deploy, start, stop)")
    #parser.add_argument('--hosts', '-n', dest='hosts', action='store', default=[],  nargs='*',
        #help='hostnames of your new VM/containers')
    #parser.add_argument('--image', '-i', dest='image', action='store', default='', 
        #help='image we use to clone')    
    #parser.add_argument( '--debug', '-d', dest='debug', action='store_true', default=False,
        #help="do not send an email but print the result to  console")
    #parser.add_argument('--mailto', '-m', dest='mailto', action='store', default='', 
        #help='send email address to notify of a new deployment.')

    #return parser.parse_args()

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
