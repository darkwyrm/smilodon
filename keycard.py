'''This module is responsible for Anselus keycard definition and resolution'''

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
		'''Checks the fields to ensure that it meets spec requirements'''

		# Check for existence of required fields
		for field in self.required_fields:
			if field not in self.fields or not self.fields[field]:
				return False
		
		return True


class OrgCard(__CardBase):
	'''Represents an organizational keycard'''
	def __init__(self):
		super().__init__()
		self.type = 'Organization'
		self.field_names = [
			'Type',
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
			'Type',
			'Name',
			'Contact-Admin',
			'Primary-Signing-Key',
			'Encryption-Key',
			'Time-To-Live',
			'Expires'
		]
	


class UserCard(__CardBase):
	'''Represents a user keycard'''
	def __init__(self):
		super().__init__()
		self.type = 'User'
		self.field_names = [
			'Type',
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
			'Type',
			'Workspace-ID',
			'Domain',
			'Contact-Request-Key',
			'Public-Encryption-Key',
			'Time-To-Live',
			'Expires'
		]


if __name__ == '__main__':
	card = OrgCard()
	card.fields = {
		'Name':'Example, Inc.',
		'Street':'1443 Dogwood Lane',
		'City':'Nogales',
		'Province':'AZ',
		'Postal-Code':'85621',
		'Country':'United States',
		'Contact-Admin':'admin/example.com',
		'Language':'English',
		'Website':'https://www.example.com',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Secondary-Signing-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt',
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB'
	}
	print(card)
