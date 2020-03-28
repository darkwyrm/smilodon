from storage import ClientStorage

# The role of this class is to provide an interface to the client as a whole,
# not just the storage aspects. It does duplicate the ClientStorage interface,
# but it also handles network interaction where needed. In short, the user's
# commands map pretty much one-to-one to this class.
class AnselusClient:
	'''This class provides the interface to the Anselus protocol for the app'''
	def __init__(self):
		self.fs = ClientStorage()
		self.active_profile = ''
		self.socket = None

	def activate_profile(self, name):
		'''Activates the specified profile'''

		status = self.fs.activate_profile(name)
		# TODO: add server connect/disconnect here
		return status

	def activate_default_profile(self):
		'''
		Activates the default profile. If no profile exists, one is created.

		Returns:
		"error" : string
		"name" : name of the profile loaded
		'''

		# Confirm that we really don't have any profiles created on disk.
		if len(self.fs.get_profiles()) == 0:
			status = self.fs.load_profiles()
			if status['error']:
				return { 'error' : status['error'], 'name' : '' }

		if len(self.fs.get_profiles()) == 0:
			status = self.fs.create_profile('primary')
			if status['error']:
				return { 'error' : status['error'], 'name' : '' }
			self.fs.set_default_profile('primary')
		
		status = self.activate_profile('default')
		if status['error']:
			return { 'error' : status['error'], 'name' : '' }
		
		return { 'error' : '', 'name' : self.active_profile }
	
	def get_active_profile(self):
		'''Returns the name of the active profile'''
		return self.active_profile

	def get_profiles(self):
		'''Gets the list of available profiles'''
		return self.fs.get_profiles()

	def create_profile(self, name):
		'''Creates a new profile'''
		return self.fs.create_profile(name)

	def delete_profile(self, name):
		'''Deletes the specified profile'''
		return self.fs.delete_profile(name)
	
	def rename_profile(self, oldname, newname):
		'''Renames the specified profile'''
		status = self.fs.rename_profile(oldname, newname)
		if status['error'] != '':
			return status
		
		if self.active_profile == oldname:
			self.active_profile = newname
		return { 'error' : '' }
	
	def get_default_profile(self):
		'''Gets the default profile'''
		return self.fs.get_default_profile()
		
	def set_default_profile(self, name):
		'''Sets the profile loaded on startup'''
		return self.fs.set_default_profile(name)

	def register_account(self, server, password):
		'''Create a new account on the specified server.'''
		
		# Process for registration of a new account:
		# 
		# Connect to requested server
		# Send registration request to server, which requires a hash of the user's supplied
		#	password
		# Close the connection to the server
		# If the server returns an error, such as 304 REGISTRATION CLOSED, then return an error.
		# If the server has returned anything else, including a 101 PENDING, begin the 
		#	client-side workspace information to generate.
		# Call storage.generate_profile()
		# Add the device ID and session string to the profile
		# Create the necessary client-side folders
		# Generate the folder mappings

		# If the server returned 201 REGISTERED, we can proceed with the server-side setup
		#
		# Create the server-side folders based on the mappings on the client side
		# Save all encryption keys into an encrypted 7-zip archive which uses the hash of the 
		# user's password has the archive encryption password and upload the archive to the server.
		
		return { 'error':'Unimplemented' }
	
	def unregister_account(self, server):
		'''Remove account from server. This does not delete any local files'''
		return { 'error':'Unimplemented' }
		