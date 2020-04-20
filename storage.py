'''This module provides an API to interact with the filesystem'''
import os
import platform
import shutil

import dbhandler
import encryption
import userprofile
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
		
		self.profiles = list()
		self.default_profile = ''
		self.active_index = -1
		self.db = dbhandler.Sqlite()		
	
	def __index_for_profile(self, name):
		'''Returns the numeric index of the named profile. Returns -1 on error'''
		if not name:
			return -1
		
		name_squashed = name.casefold()
		for i in range(0, len(self.profiles)):
			if name_squashed == self.profiles[i].name:
				return i
		return -1

	def create_profile(self, name):
		'''
		Creates a profile with the specified name. Profile names are not case-sensitive.

		Returns:
		"error" : string
		"id" : uuid of folder for new profile
		'''
		if not name:
			return { 'error' : "BUG: name may not be empty" }
		
		name_squashed = name.casefold()
		if self.__index_for_profile(name_squashed):
			return { 'error' : "%s already exists" % name }

		profile = userprofile.Profile()
		profile.make_id()

		if len(self.profiles) == 1:
			profile.isdefault = True
		
		self.profiles.append(profile)
		return userprofile.save_profiles(os.path.join(self.profile_folder,'profiles.json'),
				self.profiles)
	
	def delete_profile(self, name):
		'''
		Deletes the named profile and all files on disk contained in it.

		Returns:
		"error" : string
		'''
		if name == 'default':
			return { 'error' : "'default' is reserved" }
		
		if not name:
			return { 'error' : "BUG: name may not be empty" }
		
		name_squashed = name.casefold()
		itemindex = self.__index_for_profile(name_squashed)
		if itemindex < 0:
			return { 'error' : "%s doesn't exist" }

		profile = self.profiles.pop(itemindex)
		profile_path = os.path.join(self.profile_folder, profile.id)
		if os.path.exists(profile_path):
			try:
				shutil.rmtree(profile_path)
			except Exception as e:
				return { 'error' : e.__str__() }
		
		if profile.isdefault:
			if self.profiles:
				self.profiles[0].isdefault = True
		
		return userprofile.save_profiles(os.path.join(self.profile_folder,'profiles.json'),
				self.profiles)

	def rename_profile(self, oldname, newname):
		'''
		Renames a profile, leaving the profile ID unchanged.

		Returns:
		"error" : string
		'''
		
		if not oldname or not newname:
			return { 'error' : "BUG: name may not be empty" }
		
		old_squashed = oldname.casefold()
		new_squashed = newname.casefold()

		if old_squashed == new_squashed:
			return { 'error' : '' }
		
		index = self.__index_for_profile(old_squashed)
		if index < 0:
			return { 'error' : "'%s' doesn't exist" % oldname }

		if self.__index_for_profile(new_squashed):
			return { 'error' : "'%s' already exists" % newname }

		self.profiles[index].name = new_squashed
		return userprofile.save_profiles(os.path.join(self.profile_folder,'profiles.json'),
				self.profiles)
	
	def get_profiles(self):
		'''Returns a list of loaded profiles'''
		return self.profiles
	
	def get_default_profile(self):
		'''
		Returns the name of the default profile. If one has not been set, it returns an empty string.
		'''
		for item in self.profiles:
			if item.isdefault:
				return item.name
		return ''

	def set_default_profile(self, name):
		'''
		Sets the default profile. If there is only one profile -- or none at all -- this call has 
		no effect.
		'''
		if not name:
			return { 'error' : "Name parameter may not be empty" }
		
		if len(self.profiles) == 1:
			if self.profiles[0].isdefault:
				return { 'error' : '' }
			self.profiles[0].isdefault = True
			return userprofile.save_profiles(os.path.join(self.profile_folder,'profiles.json'),
					self.profiles)
		
		oldindex = -1
		for i in range(0, len(self.profiles)):
			if self.profiles[i].isdefault:
				oldindex = i
		
		name_squashed = name.casefold()
		newindex = self.__index_for_profile(name_squashed)
		
		if newindex < 0:
			return { 'error' : "New profile %s not found" % name_squashed }
		
		if oldindex >= 0:
			if name_squashed == self.profiles[i].name:
				return { 'error' : '' }
			self.profiles[i].isdefault = False

		self.profiles[newindex].isdefault = True		
		
		return userprofile.save_profiles(os.path.join(self.profile_folder,'profiles.json'),
				self.profiles)

	def activate_profile(self, name):
		'''
		Activates the specified profile.

		Returns:
		"error" : string
		"wid" : string
		"host" : string
		"port" : integer
		'''
		if self.active_index >= 0:
			self.db.disconnect()
			self.active_index = -1
		
		if not name:
			return { 'error' : "BUG: name may not be empty" }
		
		name_squashed = name.casefold()
		active_index = self.__index_for_profile(name_squashed)
		if active_index < 0:
			return { 'error' : "%s doesn't exist" % name_squashed }
		
		self.db.connect(name_squashed)
		self.active_index = active_index
		
		return {
			'error' : '', 
			'wid' : self.profiles[active_index].wid,
			'host' : self.profiles[active_index].domain,
			'port' : self.profiles[active_index].port 
		}

	def get_active_profile(self):
		'''Returns the active profile name'''
		if self.active_index >= 0:
			return self.profiles[self.active_index]
		return ''

	def set_credentials(self, address, pw):
		'''
		Sets the login credentials for the user's workspace in the active profile. 
		'''
		
		parts = utils.split_address(address)
		if parts['error']:
			return parts
		
		if not pw.hash:
			return { 'error' : 'empty password given'}
		
		if not self.db.set_credentials(parts[0], parts[1], pw):
			return { 'error' : 'database error' }
		
		return { 'error':'' }

	def get_credentials(self):
		'''
		Get the login credentials for the user's workspace in the active profile.

		Returns:
		"error" : string
		"wid" : string
		"password" : string -- empty if password-saving is disabled
		'''
		creds = self.db.get_credentials(self.profiles[self.active_index].wid,
				self.profiles[self.active_index].domain)
		if 'password' not in creds:
			return { 'error' : 'database error' }
		
		creds['wid'] = self.profiles[self.active_index].wid
		return creds

	def generate_profile_data(self, name, server, wid, pw):
		'''Creates full all the data needed for an individual workspace account'''
		
		# Add workspace
		if not self.db.add_workspace(wid, server, pw):
			return { 'error' : 'database error' }
		
		address = '/'.join([wid,server])

		# Generate user's encryption keys
		keys = {
			'identity' : encryption.KeyPair('identity'),
			'conrequest' : encryption.KeyPair('conrequest'),
			'broadcast' : encryption.SecretKey('broadcast'),
			'folder' : encryption.SecretKey('folder')
		}
		
		# Add encryption keys
		for key in keys.items():
			out = self.db.add_key(key, address)
			if out['error']:
				self.db.remove_workspace_entry(wid, server)
				return { 'error' : 'database error' }
		
		# Add folder mappings
		foldermap = encryption.FolderMapping()

		folderlist = [
			'messages',
			'contacts',
			'events',
			'tasks',
			'notes'
			'files',
			'files attachments'
		]

		for folder in folderlist:
			foldermap.MakeID()
			foldermap.Set(address, keys['folder'].get_id(), folder, 'root')
			self.db.add_folder(foldermap)

		# Create the folders themselves
		new_profile_folder = os.path.join(self.profile_folder, name)
		try:
			os.mkdir(new_profile_folder)
		except:
			self.db.remove_workspace(wid, server)
			return { 'error' : 'filesystem rejected new profile path'}
		
		os.mkdir(os.path.join(new_profile_folder, 'messages'))
		os.mkdir(os.path.join(new_profile_folder, 'contacts'))
		os.mkdir(os.path.join(new_profile_folder, 'events'))
		os.mkdir(os.path.join(new_profile_folder, 'tasks'))
		os.mkdir(os.path.join(new_profile_folder, 'notes'))
		os.mkdir(os.path.join(new_profile_folder, 'files'))
		os.mkdir(os.path.join(new_profile_folder, 'files', 'attachments'))

		return { 'error' : ''}
	
	def add_session(self, address, devid, session_str, devname=None):
		'''
		Adds a device session to a workspace
		
		Returns: [dict]
		error : string
		'''
		if self.db.add_device_session(address, devid, session_str, devname):
			return { 'error' : '' }
		return { 'error' : 'Failure to add device session' }

	def update_device_session(self, devid, session_str):
		'''
		Updates the session string for a device
		
		Returns: [dict]
		error : string
		'''
		if self.db.update_device_session(devid, session_str):
			return { 'error' : '' }
		return { 'error' : 'Failure to update device session' }

	def remove_device_session(self, devid):
		'''
		Removes an authorized device from the workspace.
		
		Returns: [dict]
		error : string
		'''
		if self.db.remove_device_session(devid):
			return { 'error' : '' }
		return { 'error' : 'Failure to remove device session' }

	def get_session_string(self, address):
		'''
		The device can have sessions on multiple servers, but it can only have one on each server.
		
		Returns: [dict]
		error : string
		session : string
		'''
		
		session = self.db.get_session_string(address)
		if session:
			return { 'error' : '', 'session' : session }
		return { 'error' : 'Failure to obtain device session' }
