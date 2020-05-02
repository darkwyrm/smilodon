'''This module is responsible for Anselus keycard definition and resolution'''

import datetime


class __CardBase:
	'''Represents an organizational keycard'''
	def __init__(self):
		self.fields = dict()
		self.field_names = list()
		self.required_fields = list()
		self.type = ''

	def __str__(self):
		lines = list()
		if self.type:
			lines.append("Type:" + self.type)
		
		for field in self.field_names:
			# Although fields aren't technically required to be in a certain order, keycards are 
			# meant to be human-readable, so order matters in that sense.
			if field in self.fields and self.fields[field]:
				lines.append("%s:%s" % (field, self.fields[field]))
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
	
	def set_fields(self, fields):
		'''Takes a dictionary of fields to be assigned to the object. Any field which is not part 
		of the official spec is assigned but otherwise ignored.'''
		for field in fields:
			self.fields[field] = fields[field]

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
