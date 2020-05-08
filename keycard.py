'''This module is responsible for Anselus keycard definition and resolution'''

import base64
import datetime

import nacl.public
import nacl.signing

def generate_signing_key():
	'''Generates a dictionary containing an Ed25519 key pair'''
	key = nacl.signing.SigningKey.generate()
	keypair = dict()
	keypair['private'] = key.encode()
	keypair['public'] = key.verify_key
	return keypair


def generate_encryption_key():
	'''Generates a dictionary containing a Curve25519 encryption key pair'''
	key = nacl.public.PrivateKey.generate()
	keypair = dict()
	keypair['private'] = key.encode()
	keypair['public'] = key.public_key.encode()
	return keypair

class ComplianceException(Exception):
	pass

class __CardBase:
	'''Represents an organizational keycard'''
	def __init__(self):
		self.fields = dict()
		self.field_names = list()
		self.required_fields = list()
		self.type = ''
		self.signatures = dict()

	def __str__(self):
		lines = list()
		if self.type:
			lines.append("Type:" + self.type)
		
		for field in self.field_names:
			# Although fields aren't technically required to be in a certain order, keycards are 
			# meant to be human-readable, so order matters in that sense.
			if field in self.fields and self.fields[field]:
				lines.append("%s:%s" % (field, self.fields[field]))
		
		# To ensure that the entire thing ends in a newline
		lines.append('')

		return '\n'.join(lines)
	
	def is_compliant(self):
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''

		if self.type != 'User' and self.type != 'Organization':
			return False
		
		# Check for existence of required fields
		for field in self.required_fields:
			if field not in self.fields or not self.fields[field]:
				return False, field
		
		return True, ''
	
	def set_from_string(self, text):
		'''Takes a string representation of the keycard and parses it into fields and signatures.'''
		if not text:
			self.fields = dict()
			self.signatures = dict()
			return
		
		lines = text.split('\n')
		for line in lines:
			line = line.strip()
			if not line:
				continue
			parts = line.split(':', 1)
			if len(parts) > 1:
				self.fields[parts[0]] = parts[1]


	def set_fields(self, fields):
		'''Takes a dictionary of fields to be assigned to the object. Any field which is not part 
		of the official spec is assigned but otherwise ignored.'''
		for field in fields:
			self.fields[field] = fields[field]
		
		# Any kind of editing invalidates the signatures
		self.signatures = dict()

	def set_expiration(self, numdays=-1):
		'''Sets the expiration field using the specific form of ISO8601 format recommended. 
		If not specified, organizational keycards expire 1 year from the present time and user 
		keycards expire after 90 numdays. Other types of keycards raise a TypeError exception.'''
		if numdays < 0:
			if self.type == 'Organization':
				numdays = 365
			elif self.type == 'User':
				numdays = 90
			else:
				raise TypeError
		
		expiration = datetime.datetime.utcnow() + datetime.timedelta(numdays)
		self.fields['Expires'] = expiration.strftime("%Y%m%d")


class OrgCard(__CardBase):
	'''Represents an organizational keycard'''
	def __init__(self):
		super().__init__()
		self.type = 'Organization'
		self.field_names = [
			'Name',
			'Street',
			'City',
			'Province',
			'Postal-Code',
			'Country',
			'Contact-Admin',
			'Contact-Abuse',
			'Contact-Support',
			'Language',
			'Website',
			'Primary-Signing-Key',
			'Secondary-Signing-Key',
			'Encryption-Key',
			'Web-Access',
			'Mail-Access',
			'Message-Size-Limit',
			'Time-To-Live',
			'Expires'
		]
		self.required_fields = [
			'Name',
			'Contact-Admin',
			'Primary-Signing-Key',
			'Encryption-Key',
			'Time-To-Live',
			'Expires'
		]
		self.fields['Time-To-Live'] = '30'
		self.set_expiration()

	def set_from_string(self, text):
		'''Initializes the keycard from string data'''
		super().set_from_string(text)
		if 'Organization-Signature' in self.fields:
			self.signatures['Organization'] = self.fields['Organization-Signature']
			del self.fields['Organization-Signature']

	def is_compliant(self):
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''
		status, bad_field = super().is_compliant()
		if not status:
			return status, bad_field
		
		if 'Organization' not in self.signatures or not self.signatures['Organization']:
			return False, 'Organizational-Signature'
		
		return True, ''

	def __str__(self):
		lines = list()
		if self.type:
			lines.append("Type:" + self.type)
		
		for field in self.field_names:
			if field in self.fields and self.fields[field]:
				lines.append("%s:%s" % (field, self.fields[field]))
		
		if 'Organization' in self.signatures and self.signatures['Organization']:
			lines.append('Organization-Signature:' + self.signatures['Organization'])
		return '\n'.join(lines)

	def sign(self, signing_key):
		'''Adds the organizational signature to the keycard. Note that for any change in the 
		keycard fields, this call must be made afterward.'''
		if not signing_key:
			raise ValueError
		
		if not isinstance(signing_key, bytes):
			raise TypeError
		
		base = super().__str__()
		key = nacl.signing.SigningKey(signing_key)
		signed = key.sign(base.encode(), Base85Encoder)
		self.signatures['Organization'] = signed.signature.decode()

	def verify(self, verify_key):
		'''Verifies the signature, given a verification key'''
		if 'Organization' not in self.signatures or not self.signatures['Organization']:
			raise ValueError
		
		base = super().__str__()
		vkey = nacl.signing.VerifyKey(Base85Encoder.decode(verify_key))
		try:
			vkey.verify(base.encode(), Base85Encoder.decode(self.signatures['Organization']))
		except nacl.exceptions.BadSignatureError:
			return False
		
		return True


class UserCard(__CardBase):
	'''Represents a user keycard'''
	def __init__(self):
		super().__init__()
		self.type = 'User'
		self.field_names = [
			'Workspace-ID',
			'Workspace-Name',
			'Domain',
			'Contact-Request-Key',
			'Public-Encryption-Key',
			'Alternate-Encryption-Key',
			'Time-To-Live',
			'Expires'
		]
		self.required_fields = [
			'Workspace-ID',
			'Domain',
			'Contact-Request-Key',
			'Public-Encryption-Key',
			'Time-To-Live',
			'Expires'
		]
		self.fields['Time-To-Live'] = '7'
		self.set_expiration()

	def is_compliant(self):
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''
		status, bad_field = super().is_compliant()
		if not status:
			return status, bad_field
		
		if 'User' not in self.signatures or not self.signatures['User']:
			return False, 'User-Signature'
		
		if 'Organization' not in self.signatures or not self.signatures['Organization']:
			return False, 'Organizational-Signature'
		
		return True, ''

	def set_from_string(self, text):
		'''Initializes the keycard from string data'''
		super().set_from_string(text)
		
		signatures = {
			'User-Signature':'User',
			'Custody-Signature':'Custody',
			'Organization-Signature':'Organization'
		}
		for k,v in signatures.items():
			if k in self.fields:
				self.signatures[v] = self.fields[k]
				del self.fields[k]
		
	def __str__(self):
		lines = list()
		if self.type:
			lines.append("Type:" + self.type)
		
		for field in self.field_names:
			if field in self.fields and self.fields[field]:
				lines.append("%s:%s" % (field, self.fields[field]))
		
		for sig in [ 'Custody', 'User', 'Organization' ]:
			if sig in self.signatures and self.signatures[sig]:
				lines.append(''.join([sig, '-Signature:', self.signatures['User']]))
		
		return '\n'.join(lines)

	def sign(self, signing_key, sigtype):
		'''Adds a signature to the keycard. Note that for any change in the keycard fields, this 
		call must be made afterward. Note that successive signatures are deleted, such that 
		updating a User signature will delete the Organization signature which depends on it. The 
		sigtype must be Custody, User, or Organization, and the type is case-sensitive.'''
		if not signing_key or sigtype not in ['Custody', 'User', 'Organization']:
			raise ValueError
		
		if not isinstance(signing_key, bytes):
			raise TypeError
		
		key = nacl.signing.SigningKey(signing_key)
		parts = [ super().__str__() ]
		
		if sigtype == 'Custody':
			if 'User' in self.signatures:
				del self.signatures['User']
				del self.signatures['Organization']
		
		if sigtype == 'User':
			if 'User' in self.signatures:
				del self.signatures['Organization']
			if self.signatures['Custody']:
				parts.append('Custody-Signature:' + self.signatures['Custody'] + '\n')
		elif sigtype == 'Orgnization':
			if not self.signatures['User']:
				raise ComplianceException
			parts.append('User-Signature:' + self.signatures['User'] + '\n')
		
		signed = key.sign(''.join(parts).encode(), Base85Encoder)
		self.signatures[sigtype] = signed.signature.decode()

	def verify(self, verify_key, sigtype):
		'''Verifies a signature, given a verification key'''
		if sigtype not in self.signatures or not self.signatures[sigtype]:
			raise ValueError
		
		vkey = nacl.signing.VerifyKey(Base85Encoder.decode(verify_key))
		parts = [ super().__str__() ]
		
		if sigtype == 'User' and 'Custody' in self.signatures:
			if self.signatures['Custody']:
				parts.append('Custody-Signature:' + self.signatures['Custody'] + '\n')
			else:
				# The Custody-Signature field must be populated if it exists
				raise ComplianceException
		elif sigtype == 'Orgnization':
			if 'User' not in self.signatures or not self.signatures['User']:
				raise ComplianceException
			parts.append('User-Signature:' + self.signatures['User'] + '\n')
		
		try:
			vkey.verify(''.join(parts).encode(), Base85Encoder.decode(self.signatures[sigtype]))
		except nacl.exceptions.BadSignatureError:
			return False
		
		return True


class Base85Encoder:
	'''Base85 encoder for PyNaCl library'''
	@staticmethod
	def encode(data):
		'''Returns Base85 encoded data'''
		return base64.b85encode(data)
	
	@staticmethod
	def decode(data):
		'''Returns Base85 decoded data'''
		return base64.b85decode(data)


if __name__ == '__main__':
	skey = nacl.signing.SigningKey.generate()
	ekey = nacl.public.PrivateKey.generate()

	card = UserCard()
