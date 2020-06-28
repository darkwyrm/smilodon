#!/usr/bin/env python3
'''Generates a root user or organizational keycard after asking some questions.'''

import os
import sys
import uuid

import encryption
import keycard
# Pylint doesn't detect the RetVal usage for whatever reason
import retval	# pylint: disable=unused-import

class Validator:
	'''Abstract class for validating input from the user.'''
	def IsValid(self, data: str):	# pylint: disable=unused-argument
		'''Returns True if data is valid, False if not'''
		return True


class ValueNotEmpty (Validator):
	'''Accepts any non-empty string'''
	def IsValid(self, data: str):
		return bool(data)


class ValueInList (Validator):
	'''Determines if data is in the supplied list'''
	def __init__(self, values: list):
		self.values = values
	
	def IsValid(self, data: str):
		return data in self.values


class IValueInList (Validator):
	'''Determines if data is in the supplied list'''
	def __init__(self, values: list):
		self.values = values
	
	def IsValid(self, data: str):
		return data.casefold() in self.values

class ValueIsInteger (Validator):
	'''Determines if the data is a number'''
	def IsValid(self, data: str):
		try:
			_ = int(data)
		except:
			return False
		return True


def print_usage():
	'''Prints usage information'''
	print("%s: <org|user> <directory>\nInteractively generate a keycard and associated keys." % \
			os.path.basename(__file__))

def get_input(prompt, compare=Validator(), default_value=''):
	'''Gets info from the user with an optional default value'''
	value = ''
	while not value:
		value = input(prompt)
		if not value:
			value = default_value
		
		if compare.IsValid(value):
			break
	
	return value.strip()
	

def get_org_info():
	'''Gets all user input for an organization and returns a list of tuples containing it all'''
	out = list()
	out.append(('Name', get_input("Organization Name: ", ValueNotEmpty())))
	out.append(('Street-Address',get_input("Street Address: ", ValueNotEmpty())))
	out.append(('Extended-Address',get_input("Address Line 2: ")))
	out.append(('City',get_input("City: ")))
	out.append(('Province',get_input("Province/State: ")))
	out.append(('Postal-Code',get_input("Postal Code: ")))
	out.append(('Country',get_input("Country: ")))
	
	domain = get_input("Domain: ",ValueNotEmpty())
	out.append(('Domain',domain))
	admin_address = '/'.join(['admin', domain])
	out.append(('Contact-Admin',
				get_input("Administrator contact [%s]: " % admin_address,ValueNotEmpty(),
				admin_address)))
	out.append(('Contact-Abuse',
				get_input("Abuse contact [%s]: " % admin_address,ValueNotEmpty(), admin_address)))
	out.append(('Contact-Support',
				get_input("Support contact [%s]: " % admin_address,ValueNotEmpty(), admin_address)))
	out.append(('Language',get_input("Preferred Language [en]: ", ValueNotEmpty(), 'en')))
	out.append(('Website',get_input("Website URL: ")))

	web_access = 'webmail.' + domain
	out.append(('Web-Access',get_input("Webmail Access [%s]: " % web_access, Validator(),
			web_access)))
	mail_access = 'anselus.' + domain
	out.append(('Anselus-Access',get_input("Anselus Access [%s]: " % mail_access,
			Validator(), mail_access)))
	out.append(('Item-Size-Limit',get_input("Item Size Limit [30MB]: ", ValueIsInteger(), '30')))
	out.append(('Message-Size-Limit',get_input("Message Size Limit [30MB]: ", ValueIsInteger(), 
			'30')))
	out.append(('Time-To-Live',get_input("Cache Update Period (days) [14]: ", ValueIsInteger(), '14')))
	out.append(('Expires',get_input("Time Valid (days) [730]: ", ValueIsInteger(), '730')))
	
	return out


def generate_org_card(userdata: list, path: str):
	'''Generates an organizational keycard from supplied user data'''
	ekey = encryption.KeyPair()
	skey = encryption.SigningPair()
	
	if not os.path.exists(path):
		raise OSError("Path doesn't exist")

	if not os.path.isdir(path):
		raise OSError("Path must be a directory")
	
	outpath = os.path.join(path, 'org_signing.priv.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % skey.enc_type.upper(),
			"----- BEGIN PRIVATE KEY -----\n",
			skey.get_private_key85() + '\n',
			"----- END PRIVATE KEY -----\n"
		])
	
	outpath = os.path.join(path, 'org_signing.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % skey.enc_type.upper(),
			"----- BEGIN PRIVATE KEY -----\n",
			skey.get_private_key85() + '\n',
			"----- END PRIVATE KEY -----\n"
		])
	
	print("Saved signing keys to org_signing.*")
	
	outpath = os.path.join(path, 'org_encryption.priv.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % ekey.enc_type.upper(),
			"----- BEGIN PRIVATE KEY -----\n",
			ekey.get_private_key85() + '\n',
			"----- END PRIVATE KEY -----\n"
		])
	
	outpath = os.path.join(path, 'org_encryption.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % ekey.enc_type.upper(),
			"----- BEGIN PUBLIC KEY -----\n",
			ekey.get_public_key85() + '\n',
			"----- END PUBLIC KEY -----\n"
		])
	
	print("Saved encryption keys to org_encryption.*")

	card = keycard.OrgCard()
	for item in userdata:
		card.set_field(item[0], item[1])
	card.set_field("Primary-Signing-Key", skey.get_public_key85())
	card.set_field("Encryption-Key", ekey.get_public_key85())
	
	status = card.sign(skey.get_private_key())
	if status.error():
		if status.info():
			print("Org card signature failure: %s" % status.info())
		else:
			print("Org card signature failure: %s" % status.error())
	
	status = card.is_compliant()
	if status.error():
		if status.info():
			print("Org card not compliant: %s" % status.info())
		else:
			print("Org card not compliant: %s" % status.error())
	
	outpath = os.path.join(path, 'org.keycard')
	with open(outpath, 'w') as f:
		f.write(str(card) + '\n')
	

def get_user_info():
	'''Gets all user input for a user and returns a list of tuples containing it all'''
	out = list()
	out.append(('Name', get_input("Name (optional, but recommended): ")))
	out.append(('User-ID', get_input(
			"User ID (optional, but recommended): ")))
	
	wid = get_input("Workspace ID (leave empty to generate): ")
	if not wid:
		wid = str(uuid.uuid4())
	out.append(('Workspace-ID', wid))
	out.append(('Domain', get_input("Domain: ", ValueNotEmpty())))
	return out


def generate_user_card(userdata: list, path: str):
	'''Generates a user keycard from supplied user data and a directory'''
	
	# Generate and save the necessary keys
	ekey = encryption.KeyPair()
	crkey = encryption.KeyPair()
	skey = encryption.SigningPair()

	if not os.path.exists(path):
		raise OSError("Path doesn't exist")

	if not os.path.isdir(path):
		raise OSError("Path must be a directory")
	
	outpath = os.path.join(path, 'user_encryption.priv.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % ekey.enc_type.upper(),
			"----- BEGIN PRIVATE KEY -----\n",
			ekey.get_private_key85() + '\n',
			"----- END PRIVATE KEY -----\n"
		])
	
	outpath = os.path.join(path, 'user_encryption.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % ekey.enc_type.upper(),
			"----- BEGIN PUBLIC KEY -----\n",
			ekey.get_public_key85() + '\n',
			"----- END PUBLIC KEY -----\n"
		])
	
	print("Saved encryption keys to user_encryption.*")

	outpath = os.path.join(path, 'user_request.priv.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % crkey.enc_type.upper(),
			"----- BEGIN PRIVATE KEY -----\n",
			crkey.get_private_key85() + '\n',
			"----- END PRIVATE KEY -----\n"
		])
	
	outpath = os.path.join(path, 'user_request.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % crkey.enc_type.upper(),
			"----- BEGIN PUBLIC KEY -----\n",
			crkey.get_public_key85() + '\n',
			"----- END PUBLIC KEY -----\n"
		])
	
	print("Saved contact request keys to user_request.*")

	outpath = os.path.join(path, 'user_signing.priv.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % skey.enc_type.upper(),
			"----- BEGIN PRIVATE KEY -----\n",
			skey.get_private_key85() + '\n',
			"----- END PRIVATE KEY -----\n"
		])
	
	outpath = os.path.join(path, 'user_signing.key')
	with open(outpath, 'w') as f:
		f.writelines([
			"KEYTYPE: %s B85\n" % skey.enc_type.upper(),
			"----- BEGIN PUBLIC KEY -----\n",
			skey.get_private_key85() + '\n',
			"----- END PUBLIC KEY -----\n"
		])
	
	print("Saved signing keys to user_signing.*")

	card = keycard.UserCard()
	for item in userdata:
		card.set_field(item[0], item[1])
	card.set_fields({
		"Contact-Request-Key" : crkey.get_public_key85(),
		"Public-Encryption-Key" : ekey.get_public_key85(),
	})
	
	outpath = os.path.join(path, 'user.keycard')
	with open(outpath, 'w') as f:
		f.write(str(card) + '\n')


debug_app = False

if __name__ == '__main__':
	if debug_app:
		if sys.argv[1] == 'org':
			generate_org_card([('Name', 'Acme, Inc.'), ('Street-Address', '1313 Mockingbird Lane'), 
					('Extended-Address', ''), ('City', 'Schenectady'), ('Province', 'NY'), 
					('Postal-Code', '12345'), ('Country', 'United States'), ('Domain', 'acme.com'), 
					('Contact-Admin', 'admin/acme.com'), ('Contact-Abuse', 'admin/acme.com'), 
					('Contact-Support', 'admin/acme.com'), ('Language', 'en'), 
					('Website', 'www.acme.com'), ('Web-Access', 'webmail.acme.com'), 
					('Anselus-Access', 'anselus.acme.com'), ('Item-Size-Limit', '30'), 
					('Message-Size-Limit', '30'), ('Time-To-Live', '14'), ('Expires', '730')],
					'foo')
		else:
			generate_user_card([('Name', 'Jon Yoder'), ('User-ID', 'jyoder'),
					('Workspace-ID', 'ab9ec7a7-d3d0-4bba-a203-b421418a78f0'),
					('Domain', 'example.com')],
					'foo')
		sys.exit(0)
	
	if len(sys.argv) < 3 or sys.argv[1].casefold() not in [ 'org', 'user' ]:
		print_usage()
		sys.exit(0)

	cardtype = sys.argv[1].casefold()
	if cardtype == 'org':
		info = get_org_info()
		generate_org_card(info, sys.argv[2])
	else:
		info = get_user_info()
		generate_user_card(info, sys.argv[2])
