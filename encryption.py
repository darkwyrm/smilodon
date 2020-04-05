import base64
import re
import uuid

import nacl.public
import nacl.pwhash
import nacl.secret
import nacl.utils

class EncryptionKey:
	'''Defines a generic interface to an Anselus encryption key, which contains more
	information than just the key itself'''
	def __init__(self, category='', keytype='', enctype=''):
		self.category = category
		self.id = str(uuid.uuid4())
		self.enc_type = enctype
		self.type = keytype

	def get_category(self):
		'''Returns a string containing the category of the key.'''
		return self.category

	def get_id(self):
		'''Returns the ID of the key'''
		return self.id
	
	def set_category(self, category):
		'''Sets the category of the key'''
		self.category = category
	
	def get_encryption_type(self):
		'''Returns the name of the encryption used, such as rsa, aes256, etc.'''
		return self.enc_type

	def get_type(self):
		'''Returns the type of key, such as asymmetric or symmetric'''
		return self.type


class KeyPair (EncryptionKey):
	'''Represents an assymmetric encryption key pair'''
	def __init__(self, category='', public=None, private=None, encryption=None):
		if public and private and encryption:
			super().__init__(category, keytype='asymmetric', enctype=encryption)
			self.public = public
			self.private = private
			self.type = encryption
		else:
			super().__init__(category, keytype='asymmetric', enctype='curve25519')
			key = nacl.public.PrivateKey.generate()
			self.public = key.public_key
			self.private = key
		
		self.public85 = base64.b85encode(bytes(self.public)).decode('utf8')
		self.private85 = base64.b85encode(bytes(self.private)).decode('utf8')
		self.public64 = base64.b64encode(bytes(self.public)).decode('utf8')
		self.private64 = base64.b64encode(bytes(self.private)).decode('utf8')

	def get_public_key(self):
		'''Returns the binary data representing the public half of the key'''
		return self.public
	
	def get_public_key85(self):
		'''Returns the public key encoded in base85'''
		return self.public85
	
	def get_public_key64(self):
		'''Returns the public key encoded in base64'''
		return self.public64
	
	def get_private_key(self):
		'''Returns the binary data representing the private half of the key'''
		return self.private

	def get_private_key85(self):
		'''Returns the private key encoded in base85'''
		return self.private85

	def get_private_key64(self):
		'''Returns the private key encoded in base64'''
		return self.private64


class SecretKey (EncryptionKey):
	'''Represents a secret key used by symmetric encryption'''
	def __init__(self, category='', key=None, encryption=None):
		if key and encryption:
			super().__init__(category, keytype='symmetric', enctype=encryption)
			self.key = key
			self.type = encryption
		else:
			super().__init__(category, keytype='symmetric', enctype='salsa20')
			self.key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
		self.key85 = base64.b85encode(bytes(self.key)).decode('utf8')
		self.key64 = base64.b64encode(bytes(self.key)).decode('utf8')

	def get_key85(self):
		'''Returns the key encoded in base85'''
		return self.key85
	
	def get_key64(self):
		'''Returns the key encoded in base64'''
		return self.key64
	

class FolderMapping:
	'''Represents the mapping of a server-side path to a local one'''
	def __init__(self):
		self.fid = ''
		self.address = ''
		self.keyid = ''
		self.path = ''
		self.permissions = ''
	
	def MakeID(self):
		'''Generates a FID for the object'''
		self.fid = str(uuid.uuid4())

	def Set(self, address, keyid, path, permissions):
		'''Sets the values of the object'''
		self.address = address
		self.keyid = keyid
		self.path = path
		self.permissions = permissions


def check_password_complexity(indata):
	'''Checks the requested string as meeting the needed security standards.
	
	Returns: (dict)
	error: string
	strength: string in [very weak', 'weak', 'medium', 'strong']
	'''
	if len(indata) < 8:
		return { 'error' : 'Passphrase must be at least 8 characters.'}
	
	strength_score = 0
	strength_strings = [ 'error', 'very weak', 'weak', 'medium', 'strong', 'very strong']

	# Anselus *absolutely* permits UTF-8-encoded passwords. This greatly increases the
	# keyspace
	try:
		indata.encode().decode('ascii')
	except UnicodeDecodeError:
		strength_score = strength_score + 1
	
	if re.search(r"\d", indata):
		strength_score = strength_score + 1
	
	if re.search(r"[A-Z]", indata):
		strength_score = strength_score + 1
	
	if re.search(r"[a-z]", indata):
		strength_score = strength_score + 1

	if re.search(r"[~`!@#$%^&*()_={}/<>,.:;|'[\]\"\\\-\+\?]", indata):
		strength_score = strength_score + 1

	if (len(indata) < 12 and strength_score < 3) or strength_score < 2:
		# If the passphrase is less than 12 characters, require complexity
		return { 'error' : 'passphrase too weak', 'strength' : strength_strings[strength_score] }
	
	return { 'error' : '', 'strength' : strength_strings[strength_score] }


class Password:
	'''Encapsulates hashed password interactions'''
	def __init__(self):
		self.hash = None
		self.hashtype = None
		self.strength = ''
	
	def Set(self, text):
		'''
		Takes the given password text, checks strength, and generates a hash
		Returns: [dict]
		error : string
		'''
		status = check_password_complexity(text)
		if status['error']:
			return status
		self.strength = status['strength']
		self.hash = nacl.pwhash.argon2id.str(bytes(text, 'utf8')).decode('utf8')
		self.hashtype = 'argon2id'

		return status
