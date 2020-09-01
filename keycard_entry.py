'''This module is part of the successor to the original keycard module. It contains the classes 
representing the entry blocks which are chained together in a keycard.'''

import base64
import datetime
import os

import nacl.public
import nacl.signing

from retval import RetVal, BadData, ExceptionThrown, Unimplemented

UnsupportedKeycardType = 'UnsupportedKeycardType'
InvalidKeycard = 'InvalidKeycard'
InvalidEntry = 'InvalidEntry'

# These three return codes are associated with a second field, 'field', which indicates which
# signature field is related to the error
NotCompliant = 'NotCompliant'
RequiredFieldMissing = 'RequiredFieldMissing'
SignatureMissing = 'SignatureMissing'

class ComplianceException(Exception):
	'''Custom exception for spec compliance failures'''

class EntryBase:
	'''Base class for all code common to org and user cards'''
	def __init__(self):
		self.fields = dict()
		self.field_names = list()
		self.required_fields = list()
		self.type = ''
		self.signatures = dict()

	def is_compliant(self) -> RetVal:
		'''Checks the fields to ensure that it meets spec requirements. If a field causes it 
		to be noncompliant, the noncompliant field is also returned'''

		if self.type != 'User' and self.type != 'Organization':
			return RetVal(UnsupportedKeycardType, 'unsupported card type %s' % self.type)
		
		# Check for existence of required fields
		for field in self.required_fields:
			if field not in self.fields or not self.fields[field]:
				return RetVal(RequiredFieldMissing, 'missing field %s' % field)
		
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
