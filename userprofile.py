'''The userprofile module handles user profile management'''
import json
import os
import uuid

import utils

class Profile:
	'''Encapsulates data for user profiles'''
	def __init__(self):
		self.name = ''
		self.isdefault = False
		self.id = ''
		self.wid = ''
		self.domain = ''
		self.port = 2001
	
	def make_id(self):
		'''Generates a new profile ID for the object'''
		self.id = str(uuid.uuid4())

	def address(self):
		'''Returns the identity workspace address for the profile'''
		return '/'.join([self.wid, self.domain])
	
	def serverstring(self):
		'''Returns the identity workspace address for the profile including port'''
		return ':'.join([self.address(),self.port])
	
	def as_dict(self):
		'''Returns the state of the profile as JSON'''
		return {
			'name' : self.name,
			'isdefault' : self.isdefault,
			'id' : self.id,
			'wid' : self.wid,
			'domain' : self.domain,
			'port' : self.port
		}
	
	def set_from_dict(self, data):
		'''Assigns profile data from a JSON string'''
		
		for k,v in data.items():
			if k in [ 'name', 'isdefault', 'id', 'wid', 'domain', 'port' ]:
				setattr(self, k, v)
	
	def is_valid(self):
		'''Returns true if data stored in the profile object is valid'''
		if self.name and utils.validate_uuid(self.id):
			return True
		
		return False


def load_profiles(list_path):
	'''
	Loads profile information from the specified JSON file stored in the top level of the 
	profile folder.

	Returns:
	"error" : string
	"profiles" : list
	'''
	if not os.path.exists(list_path):
		return { 'error' : 'file not found' }
	
	try:
		with open(list_path, 'r') as fhandle:
			profile_data = json.load(fhandle)
		
	except Exception as e:
		return { "error" : e.__str__() }

	profiles = list()
	for item in profile_data:
		profile = Profile()
		profile.set_from_dict(item)
		profiles.append(profile)

	return { "error" : '', 'profiles' : profiles }


def save_profiles(profile_path, profiles):
	'''
	Saves the current list of profiles to the profile list file.

	Returns:
	"error" : error state - string
	'''
	profile_list_path = os.path.join(profile_path, 'profiles.json')
	
	if not os.path.exists(profile_path):
		os.mkdir(profile_path)

	try:
		with open(profile_list_path, 'w') as fhandle:
			profile_data = list()
			for profile in profiles:

				if not profile.is_valid():
					raise ValueError
				
				profile_data.append(profile.as_dict())

				item_folder = os.path.join(profile_path, profile.name)
				if not os.path.exists(item_folder):
					os.mkdir(item_folder)

			json.dump(profile_data, fhandle)
		
	except Exception as e:
		return { "error" : e.__str__() }

	return { "error" : '' }
