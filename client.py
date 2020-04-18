'''This module provides a simple interface to the handling storage and networking needs for an 
Anselus client'''
import clientlib
from encryption import Password
from storage import ClientStorage

class AnselusClient:
	'''
	The role of this class is to provide an interface to the client as a whole, not just the 
	storage aspects. It does duplicate the ClientStorage interface,	but it also handles network 
	interaction where needed. In short, the user's commands map pretty much one-to-one to this class.
	'''
	def __init__(self):
		self.fs = ClientStorage()
		self.active_profile = ''
		self.socket = None

	def activate_profile(self, name):
		'''Activates the specified profile'''

		status = self.fs.activate_profile(name)
		if status['error']:
			return status
		
		if self.socket:
			clientlib.disconnect(self.socket)
		self.socket = None
		
		status = clientlib.connect(status['host'],status['port'])
		return status

	def activate_default_profile(self):
		'''
		Activates the default profile. If no profile exists, one is created.

		Returns:
		"error" : string
		"name" : name of the profile loaded
		'''

		# Confirm that we really don't have any profiles created on disk.
		if not self.fs.get_profiles():
			status = self.fs.load_profiles()
			if status['error']:
				return { 'error' : status['error'], 'name' : '' }

		if not self.fs.get_profiles():
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

	def register_account(self, server, userpass):
		'''Create a new account on the specified server.'''
		
		# Process for registration of a new account:
		# 
		# Check to see if we already have a workspace allocated on this profile. Because we don't
		# 	yet support shared workspaces, it means that there are only individual ones. Each 
		#	profile can have only one individual workspace.
		#
		# Connect to requested server
		# Send registration request to server, which requires a hash of the user's supplied
		#	password
		# Close the connection to the server
		# If the server returns an error, such as 304 REGISTRATION CLOSED, then return an error.
		# If the server has returned anything else, including a 101 PENDING, begin the 
		#	client-side workspace information to generate.
		# Call storage.generate_profile_data()
		# Add the device ID and session string to the profile
		# Create the necessary client-side folders
		# Generate the folder mappings

		# If the server returned 201 REGISTERED, we can proceed with the server-side setup
		#
		# Create the server-side folders based on the mappings on the client side
		# Save all encryption keys into an encrypted 7-zip archive which uses the hash of the 
		# user's password has the archive encryption password and upload the archive to the server.
		
		if self.fs.get_profiles():
			return { 'error' : 'an individual workspace already exists' }

		# Parse server string. Should be in the form of (ip/domain):portnum
		if ':' in server:
			addressparts = server.split(':')
			host = addressparts[0]
			try:
				port = int(addressparts[1])
			except ValueError:
				return { 'error' : 'bad server string'}
			serverstring = server
		else:
			host = server
			port = 2001
			serverstring = host + ':2001'
		
		# Password requirements aren't really set here, but we do have to draw the 
		# line *somewhere*.
		pw = Password()
		status = pw.Set(userpass)
		if status['error']:
			return status
		
		conndata = clientlib.connect(host, port)
		if conndata['error']:
			return conndata
		
		regdata = clientlib.register(conndata['socket'], pw.hashstring)
		if regdata['error']:
			return regdata
		
		clientlib.disconnect(conndata['socket'])

		# Possible errorcodes from register()
		# 304 - Registration closed
		# 406 - Payment required
		# 101 - Pending
		# 201 - Registered
		# 300 - Internal server error
		# 408 - Resource exists
		if regdata['errorcode'] in [304, 406, 300, 408]:
			return regdata
		
		# Just a basic sanity check
		if 'wid' not in regdata:
			return { 'error' : 'BUG: bad data from clientlib.register()' }

		status = self.fs.generate_profile_data(self.fs.get_active_profile(), server, 
			regdata['wid'], pw)
		if status['error']:
			return status
		
		address = '/'.join([regdata['wid'], serverstring])
		status = self.fs.add_session(address, regdata['devid'], regdata['session'])
		return status
	
	def unregister_account(self):
		'''Remove account from server. This does not delete any local files'''
		status = self.fs.get_credentials()
		if status['error']:
			return status
		
		status = clientlib.unregister(self.socket, status['password'])
		return status
		