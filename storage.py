import platform

class ClientStorage:
	'''
	This class provides a storage API for the rest of the client.
	'''
	def __init__(self):
		osname = platform.system().casefold()
		if osname == 'windows':
			self.dbfolder = os.path.join(os.getenv('LOCALAPPDATA'), 'anselus')
		else:
			self.dbfolder = os.path.join(os.getenv('HOME'), '.config','anselus')
		
		if not os.path.exists(self.dbfolder):
			os.mkdir(self.dbfolder)

	# Creates a profile with the specified name.
	# Returns: [dict] "id" : uuid as string, "error" : string
	def create_profile(self, name):
		return { 'error' : 'Unimplemented' }
	
	# Deletes the specified profile.
	# Returns: [dict] "error" : string
	def delete_profile(self, name):
		return { 'error' : 'Unimplemented' }

	# Renames the specified profile. The UUID of the storage folder remains unchanged.
	# Returns: [dict] "error" : string
	def rename_profile(self, oldname, newname):
		return { 'error' : 'Unimplemented' }
	
	# Returns a list of the available profiles and the default profile, if one has been set.
	# Returns: [dict] "profiles" : dictionary mapping profile names to UUIDs, "error" : string,
	#			"default" : string (possibly empty)
	def get_profiles(self):
		return { 'error' : 'Unimplemented' }
	
	# Loads a profile as the active one
	# Returns: [dict] "error" : string
	def set_profile(self, name):
		return { 'error' : 'Unimplemented' }
