'''Holds classes designed for working with encryption keys'''
import base64
import os
import re
import uuid

import nacl.public
import nacl.pwhash
import nacl.secret
import nacl.signing
import nacl.utils
from retval import RetVal, BadData, BadParameterValue, ExceptionThrown, ResourceExists

# TODO: Add support for more than just ed25519/curve25519/salsa20

def __loadfile(path: str):
	'''Loads data from a key file. This is intended to handle all the common code needed for 
	reading any key file. It returns several fields:
	keytype : str - the type of key and should be PUBLIC, PRIVATE, or SECRET
	enctype : str - encryption type
	encoding : str - type of encoding, which should be 85 or 64'''
	if not path:
		return RetVal(BadParameterValue, 'path may not be empty')
	
	lines = None
	try:
		with open(path, 'r') as f:
			lines = f.readlines()
	except Exception as e:
		return RetVal(ExceptionThrown, str(e))
	
	# Validate the data.

	# The format for a key file is expected as follows:
	# 1. First line must be 'ENCTYPE:' followed by the format in all lowercase
	# 2. Second line must be '----- BEGIN <keytype> KEY <enctype> -----' where keytype is either
	#		'PUBLIC' or 'PRIVATE' and enctype is either '64' or '85'
	# 3. Third line is the encoded key all on one line
	# 4. Fourth line is '----- END <keytype> KEY -----'

	for i in range(0, len(lines)):
		lines[i] = lines[i].strip()
		if not lines[i]:
			del lines[i]
			i = i - 1
	
	if len(lines) < 4:
		return RetVal(BadData, 'Key may only have 4 lines')

	if not lines[0].startswith('ENCTYPE:'):
		return RetVal(BadData, "First line of key must start with 'ENCTYPE:'")
	
	if not re.match('-{5} BEGIN (PRIVATE|PUBLIC|SECRET) KEY (85|64)', lines[1]):
		return RetVal(BadData, "Second line of key must be "
				"----- BEGIN (PUBLIC|PRIVATE|SECRET) KEY (85|64) -----'")
	
	if not re.match('-{5} END (PRIVATE|PUBLIC|SECRET) KEY', lines[4]):
		return RetVal(BadData, "Fourth line of key must be "
				"----- END (PUBLIC|PRIVATE|SECRET) KEY -----'")

	# Now that the general format has been validated, attempt to actually decode and load
	# the key data
	parts = lines[0].split('ENCTYPE:')
	if parts != 2 or parts[0]:
		return RetVal(BadData, 'Bad first line: %s' % lines[0])
	
	m = re.match('-{5} BEGIN (PRIVATE|PUBLIC|SECRET) KEY (85|64)', lines[1])

	r = RetVal()
	r.set_values({
		'enctype' : parts[1],
		'keytype' : m.groups[0],
		'encoding' : m.groups[1]
	})

	return r


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


class SigningPair (EncryptionKey):
	'''Represents an asymmetric signing key pair'''
	def __init__(self, category='', public=None, private=None, encryption=None):
		if public and private and encryption:
			super().__init__(category, keytype='asymmetric', enctype=encryption)
			self.public = public
			self.private = private
			self.type = encryption
		else:
			super().__init__(category, keytype='asymmetric', enctype='ed25519')
			key = nacl.signing.SigningKey.generate()
			self.public = key.verify_key.encode()
			self.private = key.encode()
		
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

	def load(self, path: str):
		'''Loads the key from a file'''
		status = __loadfile(path)
		if status.error():
			return status
		
		if status['keytype'] == 'SECRET' or status['enctype'] != 'ed25519':
			return RetVal(BadParameterValue, "Keyfile type does not match object")
		
		# TODO: Fix this -- need to load 2 files for asymmetric keys and 1 for symmetric


	def save(self, path: str, keytype: str, encoding='base85'):
		'''Saves the key to a file'''
		if not path:
			return RetVal(BadParameterValue, 'path may not be empty')
		
		if keytype not in [ 'public', 'private' ]:
			return RetVal(BadParameterValue, "keytype must be 'public' or 'private'")
		
		if encoding not in [ 'base64', 'base85' ]:
			return RetVal(BadParameterValue, "encoding must be 'base64' or 'base85'")
		
		if os.path.exists(path):
			return RetVal(ResourceExists, '%s exists' % path)

		try:
			fhandle = open(path, 'w')
			fhandle.write("ENCTYPE: %s\n" % self.enc_type.upper())
			fhandle.write('----- BEGIN %s KEY -----\n' % keytype.upper())
			
			if keytype == 'public':
				if encoding == 'base85':
					fhandle.write(self.get_public_key85() + '\n')
				else:
					fhandle.write(self.get_public_key64() + '\n')
			else:
				if encoding == 'base85':
					fhandle.write(self.get_private_key85() + '\n')
				else:
					fhandle.write(self.get_private_key64() + '\n')

			fhandle.write('----- END %s KEY -----\n' % keytype.upper())
			fhandle.close()
		
		except Exception as e:
			return RetVal(ExceptionThrown, str(e))

		return RetVal()


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
	
	Returns: RetVal
	strength: string in [very weak', 'weak', 'medium', 'strong']
	'''
	if len(indata) < 8:
		return RetVal(BadParameterValue, 'Passphrase must be at least 8 characters.') \
			.set_value('strength', 'very weak')
	
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
		status = RetVal(BadParameterValue, 'passphrase too weak')
		status.set_value('strength', strength_strings[strength_score])
		return status
	return RetVal().set_value('strength', strength_strings[strength_score])


class Password:
	'''Encapsulates hashed password interactions. Uses the Argon2id hashing algorithm.'''
	def __init__(self):
		self.hashtype = 'argon2id'
		self.strength = ''
		self.hashstring = ''

	def Set(self, text):
		'''
		Takes the given password text, checks strength, and generates a hash
		Returns: RetVal
		On success, field 'strength' is also returned
		'''
		status = check_password_complexity(text)
		if status.error():
			return status
		self.strength = status['strength']
		self.hashstring = nacl.pwhash.argon2id.str(bytes(text, 'utf8')).decode('ascii')
		
		return status
	
	def Assign(self, pwhash):
		'''
		Takes a PHC hash format string and assigns the password object to it.
		Returns: [dict]
		error : string
		'''
		self.hashstring = pwhash
		return RetVal()
	
	def Check(self, text):
		'''
		Checks the supplied password against the stored hash and returns a boolean match status.
		'''
		return nacl.pwhash.verify(self.hashstring.encode(), text.encode())
