import os
import platform
import shutil
import uuid

import dbhandler
import utils

class ClientStorage:
	'''Provides a storage API for the rest of the client.'''

	def __init__(self):
		osname = platform.system().casefold()
		if osname == 'windows':
			self.profile_folder = os.path.join(os.getenv('LOCALAPPDATA'), 'anselus')
		else:
			self.profile_folder = os.path.join(os.getenv('HOME'), '.config','anselus')
		
		if not os.path.exists(self.profile_folder):
			os.mkdir(self.profile_folder)
		
		self.profiles = dict()
		self.default_profile = ''
		self.active_profile = ''
		self.db = dbhandler.sqlite()
	
	def _save_profiles(self):
		'''
		Exports the current list of profiles to the profile list file.

		Returns:
		"error" : error state - string
		'''
		profile_list_path = os.path.join(self.profile_folder, 'profiles.txt')
		
		if not os.path.exists(self.profile_folder):
			os.mkdir(self.profile_folder)

		try:
			with open(profile_list_path, 'w') as fhandle:
				for k,v in self.profiles.items():
					fhandle.write("%s=%s%s" % (k,v,os.linesep))

					item_folder = os.path.join(self.profile_folder,k)
					if not os.path.exists(item_folder):
						os.mkdir(item_folder)

				fhandle.write("default=%s%s" % (self.default_profile,os.linesep))
		except Exception as e:
			return { "error" : e.__str__() }

		return { "error" : '' }

	def load_profiles(self):
		'''
		Loads the list of profiles from disk, which is stored in AppData/Local/anselus/profiles.txt 
		on Windows and ~/.config/anselus/profiles.txt on POSIX platforms.

		Returns:
		"error" : error state - string
		"count" : number of profiles loaded - int
		'''
		self.profiles = dict()
		profile_list_path = os.path.join(self.profile_folder, 'profiles.txt')
		if not os.path.exists(profile_list_path):
			return { "error" : '', 'count' : 0 }
		
		errormsg = ''
		with open(profile_list_path, 'r') as fhandle:
			lines = fhandle.readlines()
			line_index = 1
			for line in lines:
				tokens = '='.split(line)
				if len(tokens) != 2:
					if len(errormsg) > 0:
						errormsg = errormsg + ', bad line %d' % line_index
					else:
						errormsg = 'bad line %d' % line_index
					line_index = line_index + 1
					continue
				
				if not utils.validate_uuid(tokens[1]):
					if len(errormsg) > 0:
						errormsg = errormsg + ', bad folder id in line %d' % line_index
					else:
						errormsg = 'bad folder id in line %d' % line_index
					line_index = line_index + 1
					continue
				
				if tokens[0] == 'default':
					self.default_profile = tokens[1]
				else:
					self.profiles[tokens[0]] = tokens[1]
			
			if self.default_profile not in self.profiles.keys():
				if len(self.profiles) == 1:
					for k in self.profiles.keys():
						self.profiles['default'] = k
				else:
					self.default_profile = ''
				
		return { "error" : errormsg, 'count' : len(self.profiles) }
				
	def create_profile(self, name):
		'''
		Creates a profile with the specified name.

		Returns:
		"error" : string
		"id" : uuid of folder for new profile
		'''
		if name == 'default':
			return { 'error' : "Name 'default' is reserved", 'id' : '' }
		
		if not name:
			return { 'error' : "Name parameter may not be empty" }
		
		if name in self.profiles.keys():
			return { 'error' : 'Name exists' }

		item_id = ''
		while len(item_id) < 1 and item_id in self.profiles.values():
			item_id = uuid.uuid4().__str__()
		
		status = self._save_profiles()
		if status['error']:
			return status
		
		self.profiles[name] = item_id
		if len(self.profiles) == 1:
			for k in self.profiles.keys():
				self.profiles['default'] = k
		return status
	
	def delete_profile(self, name):
		'''
		Deletes the named profile and all files on disk contained in it.

		Returns:
		"error" : string
		'''
		if name == 'default':
			return { 'error' : "Name 'default' is reserved" }
		
		if not name:
			return { 'error' : "Name parameter may not be empty" }
		
		if name not in self.profiles.keys():
			return { 'error' : 'Name not found' }

		item_id = self.profiles[name]
		profile_path = os.path.join(self.profile_folder, item_id)
		if os.path.exists(profile_path):
			try:
				shutil.rmtree(profile_path)
			except Exception as e:
				return { 'error' : e.__str__() }
		
		del self.profiles[name]
		if self.profiles['default'] == name:
			if len(self.profiles) == 1:
				for k in self.profiles.keys():
					self.profiles['default'] = k
			else:
				self.profiles['default'] = ''
		
		return self._save_profiles()

	# Renames the specified profile. The UUID of the storage folder remains unchanged.
	# Returns: [dict] "error" : string
	def rename_profile(self, oldname, newname):
		'''
		Renames a profile, leaving the profile ID unchanged.

		Returns:
		"error" : string
		'''
		
		if oldname == 'default' or newname == 'default':
			return { 'error' : "Name 'default' is reserved" }
		
		if not oldname or not newname:
			return { 'error' : "Name parameters may not be empty" }
		
		if oldname not in self.profiles.keys():
			return { 'error' : 'Old name not found' }

		if newname in self.profiles.keys():
			return { 'error' : 'New name already exists' }

		self.profiles[newname] = self.profiles[oldname]
		del self.profiles[oldname]

		return self._save_profiles()
	
	def get_profiles(self):
		'''
		Returns the list of loaded profile names and the default one, if one has been set.

		Returns:
		"default" : name of the default profile - string
		"profiles" : profile names mapped to folder ID names - dict
		'''
		return { 'default' : self.default_profile, 'profiles' : self.profiles }
	
	def get_default_profile(self):
		'''
		Returns the name of the default profile. If one has not been set, it returns an empty string.
		'''
		return { 'default' : self.default_profile }

	def set_default_profile(self, name):
		'''
		Sets the default profile. If there is only one profile -- or none at all -- this call has 
		no effect.
		'''
		if name == 'default':
			return { 'error' : "Name 'default' is reserved" }
		
		if not name:
			return { 'error' : "Name parameter may not be empty" }
		
		if len(self.profiles) == 1:
			for k in self.profiles.keys():
				self.profiles['default'] = k
			return { 'error' : '' }
		
		if name:
			if name in self.profiles.keys():
				self.default_profile = name
			else:
				return { 'error' : 'Name not found' }
		else:
			self.default_profile = ''
			
		return { 'error' : '' }

	def set_profile(self, name):
		'''
		Activates the specified profile.

		Returns:
		"error" : string
		'''
		if self.active_profile:
			self.db.disconnect()
		
		if not name:
			return { 'error' : "Name parameter may not be empty" }
		
		if name == 'default':
			return { 'error' : "Name 'default' is reserved" }
		
		if name not in self.profiles:
			return { 'error' : 'Name not found' }
		
		self.db.connect()
		self.active_profile = name
		return { 'error' : '' }
