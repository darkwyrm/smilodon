#!/usr/bin/env python3
'''Generates a root user or organizational keycard after asking some questions.'''

import os
import sys
import uuid

import pyanselus.encryption as encryption
import pyanselus.keycard as keycard
# Pylint doesn't detect the RetVal usage for whatever reason
import pyanselus.retval as retval	# pylint: disable=unused-import

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
	
	domain = get_input("Primary Domain: ",ValueNotEmpty())
	admin_address = '/'.join(['admin', domain])
	out.append(('Contact-Admin',
				get_input("Administrator contact [%s]: " % admin_address,ValueNotEmpty(),
				admin_address)))
	out.append(('Contact-Abuse',
				get_input("Abuse contact [%s]: " % admin_address,ValueNotEmpty(), admin_address)))
	out.append(('Contact-Support',
				get_input("Support contact [%s]: " % admin_address,ValueNotEmpty(), admin_address)))
	out.append(('Language',get_input("Preferred Language [en]: ", ValueNotEmpty(), 'en')))
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
	
	skey.save(os.path.join(path, 'org_signing_keypair.jk'))
	print("Saved signing key org_signing_keypair.jk")
	
	ekey.save(os.path.join(path, 'org_encryption_keypair.jk'))
	print("Saved encryption key to org_encryption_keypair.jk")

	card = keycard.OrgEntry()
	for item in userdata:
		card.set_field(item[0], item[1])
	card.set_field("Primary-Signing-Key", 'ED25519:' + skey.get_public_key85())
	card.set_field("Encryption-Key", 'CURVE25519:' + ekey.get_public_key85())
	
	status = card.sign(skey.get_private_key(), 'Organization')
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
	
	card.save(os.path.join(path, 'org.kc'), True)
	

def get_user_info():
	'''Gets all user input for a user and returns a list of tuples containing it all'''
	out = list()
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
	crskey = encryption.SigningPair()
	crekey = encryption.KeyPair()
	skey = encryption.SigningPair()

	if not os.path.exists(path):
		raise OSError("Path doesn't exist")

	if not os.path.isdir(path):
		raise OSError("Path must be a directory")
	
	skey.save(os.path.join(path, 'user_signing_keypair.jk'))
	print("Saved signing key user_signing_keypair.jk")
	
	ekey.save(os.path.join(path, 'user_encryption_keypair.jk'))
	print("Saved encryption key to user_encryption_keypair.jk")

	crskey.save(os.path.join(path, 'user_crsigning_keypair.jk'))
	print("Saved signing key user_crsigning_keypair.jk")
	
	crekey.save(os.path.join(path, 'user_crencryption_keypair.jk'))
	print("Saved contact request key to user_crencryption_keypair.jk")

	card = keycard.UserEntry()
	for item in userdata:
		card.set_field(item[0], item[1])
	card.set_fields({
		"Contact-Request-Signing-Key" : crskey.enc_type.upper() + ':' + 
				crskey.get_public_key85(),
		"Contact-Request-Encryption-Key" : crekey.enc_type.upper() + ':' + 
				crekey.get_public_key85(),
		"Public-Encryption-Key" : ekey.enc_type.upper() + ':' + ekey.get_public_key85()
	})
	
	status = card.sign(skey.get_private_key(), 'User')
	if status.error():
		if status.info():
			print("User card signature failure: %s" % status.info())
		else:
			print("User card signature failure: %s" % status.error())
	
	card.save(os.path.join(path, 'user.kc'), True)


debug_app = False
debug_org = False

if __name__ == '__main__':
	if debug_app:
		if debug_org:
			generate_org_card([('Name', 'Acme, Inc.'), ('Contact-Admin', 'admin/acme.com'), 
					('Language', 'en'), ('Time-To-Live', '14'), ('Expires', '730')],
					'testcards')
		else:
			generate_user_card([('Name', 'Corbin Smith'), ('User-ID', 'csmith'),
					('Workspace-ID', 'ab9ec7a7-d3d0-4bba-a203-b421418a78f0'),
					('Domain', 'example.com')],
					'testcards')
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
