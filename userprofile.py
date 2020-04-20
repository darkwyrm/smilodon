'''The userprofile module handles user profile management'''
import json

import utils

class Profile:
	'''Encapsulates data for user profiles'''
	def __init__(self):
		self.name = ''
		self.isdefault = False
		self.id = ''
		self.wid = ''
		self.domain = ''
	
	def address(self):
		'''Returns the identity workspace address for the profile'''
		return '/'.join([self.wid, self.domain])
	
	def as_json(self):
		'''Returns the state of the profile as JSON'''
		return json.dumps({
			'name' : self.name,
			'isdefault' : self.isdefault,
			'id' : self.id,
			'wid' : self.wid,
			'domain' : self.domain
		})
	
	def set_from_json(self, jsonstr):
		'''Assigns profile data from a JSON string'''
		
		# If parsing doesn't go well, this will raise a JSONDecodeError. We purposely don't 
		# handle it here -- handling JSON errors is the caller's responsibility.
		parts = json.loads(jsonstr)

		for k,v in parts.items():
			if k in [ 'name', 'isdefault', 'id', 'wid', 'domain' ]:
				setattr(self, k, v)
	
	def isvalid(self):
		'''Returns true if data stored in the profile object is valid'''
		if self.name and utils.validate_uuid(self.id):
			return True
		
		return False


