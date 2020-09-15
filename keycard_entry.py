'''This module is part of the successor to the original keycard module. It contains the classes 
representing the entry blocks which are chained together in a keycard.'''

import base64
import datetime
import os

import nacl.public
import nacl.signing

from retval import RetVal, BadData, BadParameterValue, ExceptionThrown, ResourceExists, \
		ResourceNotFound, Unimplemented

FeatureNotAvailable = 'FeatureNotAvailable'
UnsupportedKeycardType = 'UnsupportedKeycardType'
UnsupportedEncryptionType = 'UnsupportedEncryptionType'
InvalidKeycard = 'InvalidKeycard'
InvalidEntry = 'InvalidEntry'

# These three return codes are associated with a second field, 'field', which indicates which
# signature field is related to the error
NotCompliant = 'NotCompliant'
RequiredFieldMissing = 'RequiredFieldMissing'
SignatureMissing = 'SignatureMissing'

class ComplianceException(Exception):
	'''Custom exception for spec compliance failures'''

class AlgoString:
	'''This class encapsulates code for working with strings associated with an algorithm. This 
	includes hashes and encryption keys.'''
	def __init__(self, data=''):
		if data:
			self.set(data)
		else:
			self.prefix = ''
			self.data = ''
	
	def set(self, data: str) -> RetVal:
		'''Initializes the instance from data passed to it. The string is expected to follow the 
		format ALGORITHM:DATA, where DATA is assumed to be base85-encoded raw byte data'''
		
		parts = data.split(':', 1)
		if len(parts) == 1:
			return RetVal(BadParameterValue, 'data is not colon-separated')
		
		self.prefix = parts[0]
		self.data = parts[1]
		return RetVal()

	def set_bytes(self, data: bytes) -> RetVal:
		'''Initializesthe instance from a byte string'''
		try:
			return self.set(data.decode())
		except Exception as e:
			return RetVal(BadData, e)
	
	def __str__(self):
		return '%s:%s' % (self.prefix, self.data)
	
	def as_bytes(self) -> bytes:
		'''Returns the instance information as a byte string'''
		return b'%s:%s' % (self.prefix, self.data)
	
	def raw_data(self) -> bytes:
		'''Decodes the internal data and returns it as a byte string.'''
		return base64.b85decode(self.data)
	
	def is_valid(self) -> bool:
		'''Returns false if the prefix and/or the data is missing'''
		return self.prefix and self.data
	
	def make_empty(self):
		'''Makes the entry empty'''
		self.prefix = ''
		self.data = ''


class EntryBase:
	'''Base class for all code common to org and user cards'''
	def __init__(self):
		self.fields = dict()
		self.field_names = list()
		self.required_fields = list()
		self.type = ''
		self.signatures = dict()
		self.signature_info = list()
	
	def __str__(self):
		return self.make_bytestring(-1).decode()
	
	def is_compliant(self) -> RetVal:
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''

		if self.type not in [ 'User', 'Organization']:
			return RetVal(UnsupportedKeycardType, 'unsupported card type %s' % self.type)
		
		# Check for existence of required fields
		for field in self.required_fields:
			if field not in self.fields or not self.fields[field]:
				return RetVal(RequiredFieldMissing, 'missing field %s' % field)
		
		# Ensure signature compliance
		for info in self.signature_info:
			if info['optional']:
				# Optional signatures, if present, may not be empty
				if info['name'] in self.signatures and not self.signatures[info['name']]:
					return RetVal(SignatureMissing, '%s-Signature' % info['name'])
			else:
				if info['name'] not in self.signatures or not self.signatures[info['name']]:
					return RetVal(SignatureMissing, '%s-Signature' % info['name'])

		return RetVal()
	
	def get_signature(self, sigtype: str) -> RetVal:
		'''Retrieves the requested signature and type'''
		if sigtype not in self.signatures:
			return RetVal(ResourceNotFound, sigtype)
		
		if len(self.signatures[sigtype]) < 1:
			return RetVal(SignatureMissing, sigtype)

		parts = self.signatures[sigtype].split(':')
		if len(parts) == 1:
			return RetVal().set_value('signature', parts[0])
		
		if len(parts) == 2:
			return RetVal().set_values({
				'algorithm' : parts[0],
				'signature' : parts[1]
			})
		
		return RetVal(BadData, self.signatures[sigtype])
	
	def make_bytestring(self, include_signatures : int) -> bytes:
		'''Creates a byte string from the fields in the keycard. Because this doesn't use join(), 
		it is not affected by Python's line ending handling, which is critical in ensuring that 
		signatures are not invalidated. The second parameterm, include_signatures, specifies 
		how many signatures to include. Passing a negative number specifies all signatures.'''
		lines = list()
		if self.type:
			lines.append(b':'.join([b'Type', self.type.encode()]))

		for field in self.field_names:
			if field in self.fields and self.fields[field]:
				lines.append(b':'.join([field.encode(), self.fields[field].encode()]))
		
		if include_signatures > len(self.signature_info) or include_signatures < 0:
			include_signatures = len(self.signature_info)
		
		sig_names = [x['name'] for x in self.signature_info]
		for i in range(include_signatures):
			name = sig_names[i]
			if name in self.signatures and self.signatures[name]:
				lines.append(b''.join([name.encode() + b'-Signature:',
								self.signatures[name].encode()]))

		lines.append(b'')
		return b'\r\n'.join(lines)
	
	def save(self, path : str, clobber = False) -> RetVal:
		'''Saves to the specified path, forcing CRLF line endings to prevent any weird behavior 
		caused by line endings invalidating signatures.'''

		if not path:
			return RetVal(BadParameterValue, 'path may not be empty')
		
		if os.path.exists(path) and not clobber:
			return RetVal(ResourceExists)
		
		try:
			with open(path, 'wb') as f:
				f.write(self.make_bytestring(-1))
		
		except Exception as e:
			return RetVal(ExceptionThrown, str(e))

		return RetVal()
	
	def set_field(self, field_name: str, field_value: str):
		'''Takes a dictionary of fields to be assigned to the object. Any field which is not part 
		of the official spec is assigned but otherwise ignored.'''
		self.fields[field_name] = field_value
		
		# Any kind of editing invalidates the signatures
		self.signatures = dict()

	def set_fields(self, fields: dict) -> RetVal:
		'''Takes a dictionary of fields to be assigned to the object. Any field which is not part 
		of the official spec is assigned but otherwise ignored.'''
		for k,v in fields.items():
			if k.endswith('Signature'):
				sigparts = k.split('-', 1)
				if sigparts[0] not in [ 'Custody', 'User', 'Organization', 'Entry' ]:
					return RetVal(BadData, 'bad signature line %s' % sigparts[0])
				self.signatures[sigparts[0]] = v
			else:
				self.fields[k] = v
		
		return RetVal()
	
	def set(self, data: bytes) -> RetVal:
		'''Sets the object's information from a bytestring'''

		try:
			rawstring = data.decode()
		except Exception as e:
			return RetVal(ExceptionThrown, e)
		
		lines = rawstring.split('\r\n')
		for line in lines:
			if not line:
				continue

			parts = line.strip().split(':', 1)
			if len(parts) != 2:
				return RetVal(BadData, line)
			
			if parts[0] == 'Type':
				if parts[0] != self.type:
					return RetVal(BadData, "can't use %s data on a %s entry" % (parts[0], self.type))
			
			elif parts[0].endswith('Signature'):
				sigparts = parts[0].split('-', 1)
				if sigparts[0] not in [ 'Custody', 'User', 'Organization', 'Entry' ]:
					return RetVal(BadData, 'bad signature line %s' % sigparts[0])
				self.signatures[sigparts[0]] = parts[1]
			
			else:
				self.fields[parts[0]] = parts[1]
			
		return RetVal()

	def set_expiration(self, numdays=-1) -> RetVal:
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

	def sign(self, signing_key: AlgoString, sigtype: str) -> RetVal:
		'''Adds a signature to the  Note that for any change in the keycard fields, this 
		call must be made afterward. Note that successive signatures are deleted, such that 
		updating a User signature will delete the Organization signature which depends on it. The 
		sigtype must be Custody, User, or Organization, and the type is case-sensitive.'''
		if not signing_key.is_valid():
			return RetVal(BadParameterValue, 'signing key')
		
		if signing_key.prefix != 'ED25519':
			return RetVal(UnsupportedEncryptionType, signing_key.prefix)
		
		sig_names = [x['name'] for x in self.signature_info]
		if sigtype not in sig_names:
			return RetVal(BadParameterValue, 'sigtype')
		
		key = nacl.signing.SigningKey(signing_key.raw_data())

		# Clear all signatures which follow the current one. This expects that the signature_info
		# field lists the signatures in the order that they are required to appear.		
		clear_sig = False
		sigtype_index = 0

		# We really do need to use an index here instead of just an iterator. Sheesh.
		for i in range(len(sig_names)): # pylint: disable=consider-using-enumerate
			name = sig_names[i]
			if name == sigtype:
				clear_sig = True
				sigtype_index = i

			if clear_sig:
				self.signatures[name] = ''

		signed = key.sign(self.make_bytestring(sigtype_index + 1), Base85Encoder)
		self.signatures[sigtype] = 'ED25519:' + signed.signature.decode()
		return RetVal()

	def verify_signature(self, verify_key: AlgoString, sigtype: str) -> RetVal:
		'''Verifies a signature, given a verification key'''
	
		if not verify_key:
			return RetVal(BadParameterValue, 'missing verify key')
		
		sig_names = [x['name'] for x in self.signature_info]
		if sigtype not in sig_names:
			return RetVal(BadParameterValue, 'bad signature type')
		
		if verify_key.prefix != 'ED25519':
			return RetVal(UnsupportedEncryptionType, verify_key.prefix)

		if sigtype in self.signatures and not self.signatures[sigtype]:
			return RetVal(NotCompliant, 'empty signature ' + sigtype)
		
		sig = AlgoString()
		status = sig.set(self.signatures[sigtype])
		if status.error():
			return status

		try:
			vkey = nacl.signing.VerifyKey(verify_key.raw_data())
		except Exception as e:
			return RetVal(ExceptionThrown, e)

		try:
			data = self.make_bytestring(sig_names.index(sigtype))
			vkey.verify(data, sig.raw_data())
		except nacl.exceptions.BadSignatureError:
			return RetVal(InvalidKeycard)
		
		return RetVal()


class OrgEntry(EntryBase):
	'''Class for managing organization keycard entries'''
	
	def __init__(self):
		super().__init__()
		self.type = 'Organization'
		self.field_names = [
			'Name',
			'Contact-Admin',
			'Contact-Abuse',
			'Contact-Support',
			'Language',
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
		self.signature_info = [ 
			{ 'name' : 'Custody', 'optional' : True },
			{ 'name' : 'Organization', 'optional' : False }
		]
		
		self.fields['Time-To-Live'] = '30'
		self.set_expiration()

	def chain(self, rotate_optional: bool) -> RetVal:
		'''Creates a new OrgEntry object with new keys and a custody signature. The keys are 
		returned in AlgoString format using the following fields:
		entry
		sign.public / sign.private -- primary signing keypair
		altsign.public / crsign.private -- contact request signing keypair
		encrypt.public / encrypt.private -- general-purpose public encryption keypair

		For organization entries, rotating optional keys works a little differently: the primary 
		signing key becomes the secondary signing key in the new entry. When rotation is False, 
		which is recommended only in instances of revocation, the secondary key is removed. Only 
		when rotate_optional is True is the field altsign.private returned.
		'''
		status = self.is_compliant()
		if status.error():
			return status
		
		new_entry = OrgEntry()
		new_entry.fields = self.fields

		out = RetVal()

		skey = nacl.signing.SigningKey.generate()
		crskey = nacl.signing.SigningKey.generate()
		crekey = nacl.public.PrivateKey.generate()

		out['sign.public'] = 'ED25519:' + skey.verify_key.encode(Base85Encoder).decode()
		out['sign.private'] = 'ED25519:' + skey.encode(Base85Encoder).decode()
		out['encrypt.public'] = 'CURVE25519:' + crekey.public_key.encode(Base85Encoder).decode()
		out['encrypt.private'] = 'CURVE25519:' + crekey.encode(Base85Encoder).decode()
		
		if rotate_optional:
			out['altsign.public'] = 'ED25519:' + crskey.verify_key.encode(Base85Encoder).decode()
			out['altsign.private'] = 'ED25519:' + crskey.encode(Base85Encoder).decode()
		else:
			out['altsign.public'] = self.fields['Primary-Signing-Key']
			out['altsign.private'] = ''

		status = new_entry.sign(AlgoString(self.fields['Contact-Request-Signing-Key']), 'Custody')
		if status.error():
			return status

		out['entry'] = new_entry
		return out
	
	def verify_chain(self, previous: EntryBase) -> RetVal:
		'''Verifies the chain of custody between the provided previous entry and the current one.'''
		# TODO: Implement OrgEntry.verify_chain()
		return RetVal(Unimplemented)


class UserEntry(EntryBase):
	'''Represents a user keycard entry'''
	def __init__(self):
		super().__init__()
		self.type = 'User'
		self.field_names = [
			'Name',
			'Workspace-ID',
			'User-ID',
			'Domain',
			'Contact-Request-Signing-Key',
			'Contact-Request-Encryption-Key',
			'Public-Encryption-Key',
			'Alternate-Encryption-Key',
			'Time-To-Live',
			'Expires'
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
		self.signature_info = [ 
			{ 'name' : 'Custody', 'optional' : True },
			{ 'name' : 'User', 'optional' : False },
			{ 'name' : 'Organization', 'optional' : False },
			{ 'name' : 'Entry', 'optional' : False }
		]
		
		self.fields['Time-To-Live'] = '7'
		self.set_expiration()
	
	def chain(self, key: AlgoString, rotate_optional: bool) -> RetVal:
		'''Creates a new UserEntry object with new keys and a custody signature. It requires the 
		previous contact request signing key passed as an AlgoString. The new keys are returned in 
		AlgoString format using the following fields:
		entry
		sign.public / sign.private -- primary signing keypair
		crsign.public / crsign.private -- contact request signing keypair
		crencrypt.public / crencrypt.private -- contact request encryption keypair
		encrypt.public / encrypt.private -- general-purpose public encryption keypair
		altencrypt.public / altencrypt.private -- alternate public encryption keypair

		Note that the last two keys are not required to be updated during entry rotation so that 
		they can be rotated on a different schedule from the other keys. These fields are only 
		returned if there are no errors.
		'''
		if key.prefix != 'ED25519':
			return RetVal(BadParameterValue, f'wrong key type {key.prefix}')
		
		status = self.is_compliant()
		if status.error():
			return status
		
		new_entry = UserEntry()
		new_entry.fields = self.fields

		out = RetVal()

		skey = nacl.signing.SigningKey.generate()
		crskey = nacl.signing.SigningKey.generate()
		crekey = nacl.public.PrivateKey.generate()

		out['sign.public'] = 'ED25519:' + skey.verify_key.encode(Base85Encoder).decode()
		out['sign.private'] = 'ED25519:' + skey.encode(Base85Encoder).decode()
		out['crsign.public'] = 'ED25519:' + crskey.verify_key.encode(Base85Encoder).decode()
		out['crsign.private'] = 'ED25519:' + crskey.encode(Base85Encoder).decode()
		out['crencrypt.public'] = 'CURVE25519:' + crekey.public_key.encode(Base85Encoder).decode()
		out['crencrypt.private'] = 'CURVE25519:' + crekey.encode(Base85Encoder).decode()
		
		new_entry.fields['Contact-Request-Signing-Key'] = out['crsign.public']
		new_entry.fields['Contact-Request-Encryption-Key'] = out['crencrypt.public']

		if rotate_optional:
			ekey = nacl.public.PrivateKey.generate()
			out['encrypt.public'] ='CURVE25519:' +  ekey.public_key.encode(Base85Encoder).decode()
			out['encrypt.private'] = 'CURVE25519:' + ekey.encode(Base85Encoder).decode()

			aekey = nacl.public.PrivateKey.generate()
			out['altencrypt.public'] = 'CURVE25519:' + aekey.public_key.encode(Base85Encoder).decode()
			out['altencrypt.private'] = 'CURVE25519:' + aekey.encode(Base85Encoder).decode()
			
			new_entry.fields['Public-Encryption-Key'] = out['encrypt.public']
			new_entry.fields['Alternate-Encryption-Key'] = out['altencrypt.public']
		else:
			out['encrypt.public'] = ''
			out['encrypt.private'] = ''
			out['altencrypt.public'] = ''
			out['altencrypt.private'] = ''

		status = new_entry.sign(key, 'Custody')
		if status.error():
			return status

		out['entry'] = new_entry
		return out
		
	def verify_chain(self, previous: EntryBase) -> RetVal:
		'''Verifies the chain of custody between the provided previous entry and the current one.'''

		if previous.type != 'User':
			return RetVal(BadParameterValue, 'entry type mismatch')
		
		if 'Custody' not in self.signatures or not self.signatures['Custody']:
			return RetVal(ResourceNotFound, 'custody signature missing')
		
		if 'Contact-Request-Signing-Key' not in previous.fields or \
				not previous.fields['Contact-Request-Signing-Key']:
			return RetVal(ResourceNotFound, 'signing key missing')
		
		status = self.verify_signature(AlgoString(previous.fields['Contact-Request-Signing-Key']),
				'Custody')
		return status


class Keycard:
	'''Encapsulates a chain of keycard entries and higher-level management methods'''
	def __init__(self, cardtype = ''):
		self.type = cardtype
		self.entries = list()
	
	def chain(self, rotate_optional = True) -> RetVal:
		'''Appends a new entry to the chain, optionally rotating keys which aren't required to be 
		changed. This method requires that the root entry already exist. Note that user cards will 
		not have all the required signatures when the call returns'''
		if len(self.entries) < 1:
			return RetVal(ResourceNotFound, 'missing root entry')

		# Just in case we get some squirrelly non-Org, non-User card type
		chain_method = getattr(self.entries[-1], "chain", None)
		if not chain_method or not callable(chain_method):
			return RetVal(FeatureNotAvailable, "entry doesn't support chaining")
		
		chaindata = self.entries[-1].chain(rotate_optional)
		if chaindata.error():
			return chaindata
		
		new_entry = chaindata['entry']

		skeystring = AlgoString()
		status = skeystring.set(chaindata['sign.private'])
		if status.error():
			return status
		
		status = new_entry.sign(skeystring, 'User')
		if status.error():
			return status
		
		chaindata['entry'] = new_entry
		self.entries.append(new_entry)
		return chaindata
	
	def load(self, path: str) -> RetVal:
		'''Loads a keycard from a file'''
		# TODO: Implement load()
		return RetVal(Unimplemented)

	def save(self, path: str, clobber: bool) -> RetVal:
		'''Saves a keycard to a file'''
		if not path:
			return RetVal(BadParameterValue, 'path may not be empty')
		
		if os.path.exists(path) and not clobber:
			return RetVal(ResourceExists)
			
		try:
			with open(path, 'wb') as f:
				for entry in self.entries:
					f.write(b'----- BEGIN ENTRY -----\r\n')
					f.write(entry.make_bytestring(-1))
					f.write(b'----- END ENTRY -----\r\n')
			
		except Exception as e:
			return RetVal(ExceptionThrown, str(e))

		return RetVal()
	
	def verify(self) -> RetVal:
		'''Verifies the card's entire chain of entries'''
		# TODO: Implement verify()
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
