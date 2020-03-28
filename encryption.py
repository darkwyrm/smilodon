import base64
import uuid

import nacl.public
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
	
