'''This module is part of the successor to the original keycard module. It contains the classes 
representing the entry blocks which are chained together in a keycard.'''

import base64
import datetime
import os

import nacl.public
import nacl.signing

from retval import RetVal, BadData, BadParameterValue, BadParameterType, EmptyData, \
		ExceptionThrown, ResourceNotFound, ResourceExists, Unimplemented

UnsupportedKeycardType = 'UnsupportedKeycardType'
InvalidKeycard = 'InvalidKeycard'

# These three return codes are associated with a second field, 'field', which indicates which
# signature field is related to the error
NotCompliant = 'NotCompliant'
RequiredFieldMissing = 'RequiredFieldMissing'
SignatureMissing = 'SignatureMissing'

class ComplianceException(Exception):
	'''Custom exception for spec compliance failures'''

class __EntryBase:
	'''Base class for all code common to org and user cards'''
	def __init__(self):
		self.fields = dict()
		self.field_names = list()
		self.required_fields = list()
		self.type = ''
		self.signatures = dict()

	def is_compliant(self):
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''

		if self.type != 'User' and self.type != 'Organization':
			return RetVal(UnsupportedKeycardType).set_info('Unsupported card type %s' % self.type)
		
		# Check for existence of required fields
		for field in self.required_fields:
			if field not in self.fields or not self.fields[field]:
				return RetVal(RequiredFieldMissing).set_info('Missing field %s' % field)
		
		return RetVal()
	
	def set_field(self, field_name: str, field_value: str):
		'''Takes a dictionary of fields to be assigned to the object. Any field which is not part 
		of the official spec is assigned but otherwise ignored.'''
		self.fields[field_name] = field_value
		
		# Any kind of editing invalidates the signatures
		self.signatures = dict()

	def set_fields(self, fields: dict):
		'''Takes a dictionary of fields to be assigned to the object. Any field which is not part 
		of the official spec is assigned but otherwise ignored.'''
		for field in fields:
			self.fields[field] = fields[field]
		
		# Any kind of editing invalidates the signatures
		self.signatures = dict()
	
	def set(self, data: bytes) -> RetVal:
		'''Sets the object's information from a bytestring'''
		# TODO: Implement

		return RetVal(Unimplemented)

	def make_bytestring(self, include_signatures : bool) -> bytes:
		'''Method to be implemented by child classes. Returns a bytes object representing the 
		entry'''
		return b''
	
	def set_expiration(self, numdays=-1):
		'''Sets the expiration field using the specific form of ISO8601 format recommended. 
		If not specified, organizational keycards expire 1 year from the present time and user 
		keycards expire after 90 days. Other types of keycards return an error.'''
		if numdays < 0:
			if self.type == 'Organization':
				numdays = 365
			elif self.type == 'User':
				numdays = 90
			else:
				return RetVal(UnsupportedKeycardType)
		
		expiration = datetime.datetime.utcnow() + datetime.timedelta(numdays)
		self.fields['Expires'] = expiration.strftime("%Y%m%d")
		return RetVal()


class OrgEntry(__EntryBase):
	'''Represents an organizational keycard entry'''
	def __init__(self):
		super().__init__()
		self.type = 'Organization'
		self.field_names = [
			'Name',
			'Contact-Admin',
			'Contact-Abuse',
			'Contact-Support',
			'Primary-Signing-Key',
			'Secondary-Signing-Key',
			'Encryption-Key',
			'Time-To-Live',
			'Expires',
			'Hash-ID'
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

	def is_compliant(self):
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''
		rv = super().is_compliant()
		if rv.error():
			return rv
		
		if 'Organization' not in self.signatures or not self.signatures['Organization']:
			rv = RetVal(SignatureMissing)
			rv['field'] = 'Organization-Signature'
			return rv
		
		return RetVal()

	def make_bytestring(self, include_signatures : bool) -> bytes:
		'''Creates a byte string from the fields in the keycard. Because this doesn't use the 
		string version of join(), it is not affected by Python's line ending handling, which is
		critical to ensure that signatures are not invalidated.'''
		lines = list()
		if self.type:
			lines.append(b':'.join([b'Type', self.type.encode()]))

		for field in self.field_names:
			if field in self.fields and self.fields[field]:
				lines.append(b':'.join([field.encode(), self.fields[field].encode()]))
		
		if include_signatures:
			if 'Organization' in self.signatures and self.signatures['Organization']:
				lines.append(b'Organization-Signature:' + self.signatures['Organization'].encode())
		lines.append(b'')
		
		return b'\r\n'.join(lines)
	
	def sign(self, signing_key: bytes):
		'''Adds the organizational signature to the  Note that for any change in the 
		keycard fields, this call must be made afterward.'''
		if not signing_key:
			return RetVal(BadParameterValue)
		
		key = nacl.signing.SigningKey(signing_key)
		signed = key.sign(self.make_bytestring(True), Base85Encoder)
		self.signatures['Organization'] = 'ED25519:' + signed.signature.decode()
		return RetVal()

	def verify(self, verify_key: bytes):
		'''Verifies the signature, given a verification key'''
		if 'Organization' not in self.signatures or not self.signatures['Organization']:
			return RetVal(SignatureMissing)
		
		rv = RetVal()
		vkey = nacl.signing.VerifyKey(Base85Encoder.decode(verify_key))
		try:
			vkey.verify(self.make_bytestring(True), Base85Encoder.decode(self.signatures['Organization']))
		except nacl.exceptions.BadSignatureError:
			rv.set_error(InvalidKeycard)
		
		return rv


class UserEntry(__EntryBase):
	'''Represents a user keycard entry'''
	def __init__(self):
		super().__init__()
		self.type = 'User'
		self.field_names = [
			'Workspace-ID',
			'User-ID',
			'Domain',
			'Contact-Request-Signing-Key',
			'Contact-Request-Encryption-Key',
			'Public-Encryption-Key',
			'Alternate-Encryption-Key',
			'Time-To-Live',
			'Expires',
			'Hash-ID'
		]
		self.required_fields = [
			'Workspace-ID',
			'Domain',
			'Contact-Request-Signing-Key',
			'Contact-Request-Encryption-Key',
			'Public-Encryption-Key',
			'Time-To-Live',
			'Expires'
		]
		self.fields['Time-To-Live'] = '7'
		self.set_expiration()

	def is_compliant(self):
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''
		rv = super().is_compliant()
		if rv.error():
			return rv
		
		if 'User' not in self.signatures or not self.signatures['User']:
			return RetVal(SignatureMissing, 'User-Signature')
		
		if 'Organization' not in self.signatures or not self.signatures['Organization']:
			return RetVal(SignatureMissing, 'Organization-Signature')
		
		if 'Entry' not in self.signatures or not self.signatures['Entry']:
			return RetVal(SignatureMissing, 'Entry-Signature')

		return rv

	def make_bytestring(self, include_signatures : int) -> bytes:
		'''Creates a byte string from the fields in the keycard. Because this doesn't use join(), 
		it is not affected by Python's line ending handling, which is critical in ensuring that 
		signatures are not invalidated. The second parameterm, include_signatures, specifies 
		which signatures to include. 0 = None, 1 = Custody only, 2 = Custody + User, 3+ = all'''
		lines = list()
		if self.type:
			lines.append(b':'.join([b'Type', self.type.encode()]))

		for field in self.field_names:
			if field in self.fields and self.fields[field]:
				lines.append(b':'.join([field.encode(), self.fields[field].encode()]))
		
		if include_signatures > 0 and 'Custody' in self.signatures:
			lines.append(b''.join([b'Custody-Signature:',
							self.signatures['Custody'].encode()]))
		if include_signatures > 1 and 'User' in self.signatures:
			lines.append(b''.join([b'User-Signature:',
							self.signatures['User'].encode()]))
		if include_signatures > 2 and 'Organization' in self.signatures:
			lines.append(b''.join([b'Organization-Signature:',
							self.signatures['Organization'].encode()]))
		if include_signatures > 3 and 'Entry' in self.signatures:
			lines.append(b''.join([b'Entry-Signature:',
							self.signatures['Entry'].encode()]))

		lines.append(b'')
		return b'\r\n'.join(lines)

	def sign(self, signing_key: bytes, sigtype: str):
		'''Adds a signature to the  Note that for any change in the keycard fields, this 
		call must be made afterward. Note that successive signatures are deleted, such that 
		updating a User signature will delete the Organization signature which depends on it. The 
		sigtype must be Custody, User, or Organization, and the type is case-sensitive.'''
		if not signing_key:
			return RetVal(BadParameterValue, 'signing key')
		
		if sigtype not in ['Custody', 'User', 'Organization']:
			return RetVal(BadParameterValue, 'sigtype')
		
		key = nacl.signing.SigningKey(signing_key)
		
		if sigtype == 'Custody':
			if 'User' in self.signatures:
				del self.signatures['User']
			
			if 'Organization' in self.signatures:
				del self.signatures['Organization']
		
		elif sigtype == 'User':
			if 'Organization' in self.signatures:
				del self.signatures['Organization']
		
			if 'Entry' in self.signatures:
				del self.signatures['Entry']
			
		elif sigtype == 'Organization':
			if 'Entry' in self.signatures:
				del self.signatures['Entry']
			
			if not self.signatures['User']:
				raise ComplianceException
		
		elif sigtype == 'Entry':
			if not self.signatures['User'] or not self.signatures['Organization']:
				raise ComplianceException
		
		sig_map = {
			'Custody' : 0,
			'User' : 1,
			'Organization' : 2,
			'Entry' : 3
		}
		signed = key.sign(self.make_bytestring(sig_map[sigtype]), Base85Encoder)
		self.signatures[sigtype] = 'ED25519' + signed.signature.decode()
		return RetVal()

	def verify(self, verify_key: bytes, sigtype: str):
		'''Verifies a signature, given a verification key'''
	
		rv = RetVal()
		if not verify_key:
			rv.set_error(BadParameterValue)
			rv['parameter'] = 'verify_key'
			return rv 
		
		if sigtype not in ['Custody', 'User', 'Organization']:
			rv.set_error(BadParameterValue)
			rv['parameter'] = 'sigtype'
			return rv 
		
		vkey = nacl.signing.VerifyKey(verify_key)
		
		if 'Custody' in self.signatures and not self.signatures['Custody']:
			# The Custody-Signature field must be populated if it exists
			rv.set_error(NotCompliant)
			rv['field'] = 'Custody-Signature'
			return rv
		
		if sigtype == 'Organization':
			if 'User' not in self.signatures or not self.signatures['User']:
				rv.set_error(NotCompliant)
				rv['field'] = 'User-Signature'
				return rv
		
		if sigtype == 'Entry':
			if 'User' not in self.signatures or not self.signatures['User']:
				rv.set_error(NotCompliant)
				rv['field'] = 'User-Signature'
				return rv
			
			if 'Organization' not in self.signatures or not self.signatures['Organization']:
				rv.set_error(NotCompliant)
				rv['field'] = 'Organization-Signature'
				return rv
		
		sig_map = {
			'Custody' : 0,
			'User' : 1,
			'Organization' : 2,
			'Entry' : 3
		}
		try:
			data = self.make_bytestring(sig_map[sigtype])
			vkey.verify(data, Base85Encoder.decode(self.signatures[sigtype]))
		except nacl.exceptions.BadSignatureError:
			rv.set_error(InvalidKeycard)
		
		return rv
		

class Keycard:
	'''This class contains and manages a chain of keycard entries'''
	def __init__(self):
		self.entries = list()
		self.type = ''

	def load(self, path: str) -> RetVal:
		'''Loads an entire keycard from disk'''
		# TODO: Implement
		return RetVal(Unimplemented)
	
	def save(self, path: str) -> RetVal:
		'''Saves an entire keycard to disk'''
		# TODO: Implement
		return RetVal(Unimplemented)
	
	def append(self, entry: __EntryBase) -> RetVal:
		'''Adds a new entry to the chain'''
		
		if self.type and self.type != entry.type:
			return RetVal(BadParameterType)
		
		if not entry.is_compliant():
			return RetVal(NotCompliant)		

		# TODO: Finish implementation

		return RetVal(Unimplemented)

	def verify(self) -> RetVal:
		'''Verifies the entire chain of entries'''
		# TODO: Implement
		return RetVal(Unimplemented)


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
