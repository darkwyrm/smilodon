'''This module is part of the successor to the original keycard module. It contains the classes 
representing the entry blocks which are chained together in a keycard.'''

import base64
import datetime
import os

import nacl.public
import nacl.signing

from retval import RetVal, Unimplemented

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

	def make_bytestring(self, include_signatures : bool) -> bytes:	# pylint: disable=unused-argument,no-self-use
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
